from typing import Any, Dict, Set
from synapse.module_api.errors import ConfigError

@attr.s(auto_attribs=True, frozen=True)
class RestrictionModuleConfig:
    restricted_rooms: Set[str]
    local_domain: str
    leave_error_message: str

    @staticmethod
    def from_config(config: Dict[str, Any]) -> "RestrictionModuleConfig":
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
            restricted_rooms=set(restricted_rooms),
            local_domain=local_domain,
            leave_error_message=leave_error_message,
        )
