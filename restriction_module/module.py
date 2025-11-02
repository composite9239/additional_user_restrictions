from typing import Any, Dict, Optional, Tuple
import logging

from synapse.events import EventBase
from synapse.module_api import ModuleApi
from synapse.module_api.errors import ConfigError
from synapse.types import StateMap

from .config import RestrictionModuleConfig

class RestrictionModule:
    @staticmethod
    def parse_config(config: Dict[str, Any]) -> RestrictionModuleConfig:
        logger = logging.getLogger(__name__)
        logger.warning("Parsing config for RestrictionModule")
        try:
            return RestrictionModuleConfig.from_config(config)
        except (TypeError, ValueError) as e:
            raise ConfigError(f"Failed to parse restriction module config: {e}")

    def __init__(self, config: RestrictionModuleConfig, api: ModuleApi):
        self._api = api
        self._restricted_rooms = config.restricted_rooms
        self._local_domain = config.local_domain
        self._leave_error_message = config.leave_error_message

        self.logger = logging.getLogger(__name__)
        self.logger.warning(
            "RestrictionModule initialized. Restricted rooms: %s, local_domain: %s",
            list(self._restricted_rooms),
            self._local_domain
        )

        # Register the third-party rules callbacks
        self._api.register_third_party_rules_callbacks(
            check_event_allowed=self.check_event_allowed,
            check_can_deactivate_user=self.check_can_deactivate_user,
        )
        self.logger.warning("Third-party rules callbacks registered.")

    def _is_local_user(self, user_id: str) -> bool:
        """Check if the user_id belongs to this homeserver's domain."""
        return user_id.endswith(f":{self._local_domain}")

    async def check_event_allowed(
        self, event: EventBase, state_events: StateMap
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Hard-block local users from leaving restricted rooms.
        Returns (False, error_dict) to reject the event with a custom message.
        """
        membership = event.content.get("membership")
        self.logger.warning(
            "check_event_allowed called: type=%s, room_id=%s, sender=%s, state_key=%s, membership=%s",
            event.type, event.room_id, event.sender, event.state_key, membership
        )

        if event.type != "m.room.member":
            self.logger.warning("Allowed: Not a membership event.")
            return True, None

        if membership != "leave":
            self.logger.warning("Allowed: Membership not 'leave'.")
            return True, None

        if event.room_id not in self._restricted_rooms:
            self.logger.warning("Allowed: Room not restricted.")
            return True, None

        if event.sender != event.state_key:
            self.logger.warning("Allowed: Not a self-leave (e.g., kick).")
            return True, None

        if not self._is_local_user(event.sender):
            self.logger.warning("Allowed: Not a local user.")
            return True, None

        self.logger.warning("Blocking leave attempt in restricted room %s by %s", event.room_id, event.sender)

        # Hard reject with custom error message
        return False, {
            "errcode": "M_FORBIDDEN",
            "error": self._leave_error_message,
        }

    async def check_can_deactivate_user(self, user_id: str, by_admin: bool) -> bool:
        """
        Prevent users from deactivating their own accounts, but allow admins to do so.
        """
        return by_admin
