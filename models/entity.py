from dataclasses import dataclass
from models.sockets import Sockets


@dataclass
class Entity:
    name: str
    health: int
    power_usage_per_second: int
    movement_speed: float
    visibility: float
    storage: int
    size: str
    race: str
    types: list[str]
    sockets: Sockets
