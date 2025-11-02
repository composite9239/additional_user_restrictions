from typing import Any, Dict, Optional, Tuple
from synapse.events import EventBase
from synapse.module_api import ModuleApi
from synapse.module_api.errors import ConfigError
from synapse.types import StateMap

class RestrictionModule:
    @staticmethod
    def parse_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate the module configuration.
        """
        restricted_rooms = config.get("restricted_rooms", [])
        if not isinstance(restricted_rooms, list):
            raise ConfigError("restricted_rooms must be a list of strings")
        for room in restricted_rooms:
            if not isinstance(room, str) or not room.startswith("!"):
                raise ConfigError("Each entry in restricted_rooms must be a valid room ID starting with '!'")

        local_domain = config.get("local_domain")
        if not isinstance(local_domain, str) or not local_domain:
            raise ConfigError("local_domain must be a non-empty string (e.g., 'example.com')")

        leave_error_message = config.get("leave_error_message", "You are not allowed to leave this room.")
        if not isinstance(leave_error_message, str):
            raise ConfigError("leave_error_message must be a string")

        return {
            "restricted_rooms": set(restricted_rooms),  # Use a set for O(1) lookups
            "local_domain": local_domain,
            "leave_error_message": leave_error_message,
        }

    def __init__(self, config: Dict[str, Any], api: ModuleApi):
        self._api = api
        self._restricted_rooms = config["restricted_rooms"]
        self._local_domain = config["local_domain"]
        self._leave_error_message = config["leave_error_message"]  # Unused for now (see class docstring)

        # Register the third-party rules callback for hard-blocking room leaves
        self._api.register_third_party_rules_callbacks(
            check_event_allowed=self.check_event_allowed,
        )
        # Register for account deactivation prevention (unchanged)
        self._api.register_third_party_rules_callbacks(
            check_can_deactivate_user=self.check_can_deactivate_user,
        )

    def _is_local_user(self, user_id: str) -> bool:
        """Check if the user_id belongs to this homeserver's domain."""
        return user_id.endswith(f":{self._local_domain}")

    async def check_event_allowed(
        self, event: EventBase, state_events: StateMap
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Hard-block local users from leaving restricted rooms.
        Returns (False, None) to reject the event with a generic "Forbidden" error.
        """
        if event.type != "m.room.member":
            return True, None

        membership = event.content.get("membership")
        if membership != "leave":
            return True, None

        if event.room_id not in self._restricted_rooms:
            return True, None

        # Only block self-leaves (sender == state_key)
        if event.sender != event.state_key:
            return True, None

        # Only block local users
        if not self._is_local_user(event.sender):
            return True, None

        # Hard reject the leave attempt
        return False, None

    async def check_can_deactivate_user(self, user_id: str, by_admin: bool) -> bool:
        """
        Prevent users from deactivating their own accounts, but allow admins to do so.
        """
        return by_admin
