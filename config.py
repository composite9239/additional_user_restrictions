from typing import Any, Dict
from synapse.module_api.errors import ConfigError

class RestrictionModuleConfig:
    """
    Parsed and validated module configuration.
    """
    def __init__(
        self,
        restricted_rooms: set[str],
        local_domain: str,
        leave_error_message: str,
    ):
        self.restricted_rooms = restricted_rooms
        self.local_domain = local_domain
        self.leave_error_message = leave_error_message

    @staticmethod
    def parse_config(config: Dict[str, Any]) -> "RestrictionModuleConfig":
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

        return RestrictionModuleConfig(
            restricted_rooms=set(restricted_rooms),  # Use a set for O(1) lookups
            local_domain=local_domain,
            leave_error_message=leave_error_message,
        )
