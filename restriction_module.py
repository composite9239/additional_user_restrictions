from typing import Any, Dict

from synapse.events import EventBase
from synapse.module_api import ModuleApi, NOT_SPAM
from synapse.module_api.errors import ConfigError

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

        leave_error_message = config.get("leave_error_message", "You are not allowed to leave this room.")
        if not isinstance(leave_error_message, str):
            raise ConfigError("leave_error_message must be a string")

        return {
            "restricted_rooms": set(restricted_rooms),  # Use a set for O(1) lookups
            "leave_error_message": leave_error_message,
        }

    def __init__(self, config: Dict[str, Any], api: ModuleApi):
        self._api = api
        self._restricted_rooms = config["restricted_rooms"]
        self._leave_error_message = config["leave_error_message"]

        # Register the relevant callbacks
        self._api.register_spam_checker_callbacks(
            check_event_for_spam=self.check_event_for_spam,
        )
        self._api.register_third_party_rules_callbacks(
            check_can_deactivate_user=self.check_can_deactivate_user,
        )

    async def check_event_for_spam(self, event: EventBase) -> Any:
        """
        Check if the event is a user attempting to leave a restricted room.
        """
        if event.type != "m.room.member":
            return NOT_SPAM

        membership = event.content.get("membership")
        if membership != "leave":
            return NOT_SPAM

        if event.room_id not in self._restricted_rooms:
            return NOT_SPAM

        # If the sender is the same as the state_key, it's a self-leave attempt
        if event.sender == event.state_key:
            # Reject with custom error message (using string return for custom msg, as per docs)
            return self._leave_error_message

        # Allow other actions (e.g., admin kicks)
        return NOT_SPAM

    async def check_can_deactivate_user(self, user_id: str, by_admin: bool) -> bool:
        """
        Prevent users from deactivating their own accounts, but allow admins to do so.
        """
        return by_admin
