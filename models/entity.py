from dataclasses import dataclass
from enum import Enum
from models.sockets import Sockets
from models.types import Race


class SlotType(Enum):
    NONE = "None"
    FLYER = "Flyer"
    DRONE = "Drone"
    SATELLITE = "Satellite"
    GARAGE = "Garage"
    BUGHOLE = "Bughole"


class EntityType(Enum):
    BUG = "Bug"
    BOT = "Bot"
    BUILDING = "Building"


@dataclass
class Entity:
    name: str
    health: int
    power_usage_per_second: int
    movement_speed: float
    visibility: float
    storage: int
    size: str
    race: Race
    types: list[EntityType]
    sockets: Sockets
    slot_type: SlotType
