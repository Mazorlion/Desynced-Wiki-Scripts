from dataclasses import dataclass


@dataclass
class Sockets:
    large_sockets: int = 0
    medium_sockets: int = 0
    small_sockets: int = 0
    internal_sockets: int = 0

    def increment_socket(self, socket_type) -> None:
        socket_type = socket_type.lower()
        # Construct the field name
        field_name = f"{socket_type}_sockets"

        # Increment the field value
        current_value = getattr(self, field_name)
        setattr(self, field_name, current_value + 1)
