from enum import Enum

from models.decorators import desynced_object


class SocketSize(Enum):
    HIDDEN = "Hidden"
    INTERNAL = "Internal"
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"


@desynced_object
class Sockets:
    large_sockets: int = 0
    medium_sockets: int = 0
    small_sockets: int = 0
    internal_sockets: int = 0

    def increment_socket(self, socket_type: str) -> None:
        """Takes a prefix of one of the fields in this class and adds one to it.
        Useful for quickly adding based on the string table in the lua.

        Args:
            socket_type (str): type of socket to add.
            Must be one of the prefixes for a field in this class.
        """
        socket_type = socket_type.lower()
        # Construct the field name
        field_name = f"{socket_type}_sockets"

        # Increment the field value
        current_value = getattr(self, field_name)
        setattr(self, field_name, current_value + 1)
