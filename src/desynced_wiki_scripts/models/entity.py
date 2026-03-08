from dataclasses import field
from enum import Enum

from .decorators import desynced_object, length_check
from .decorators_options import ListFieldOptions, annotate
from .wiki_metadata import WikiMetadata
from .recipe import Recipe
from .sockets import Sockets
from .types import Race


class SlotType(Enum):
    NONE = "None"
    FLYER = "Flyer"
    DRONE = "Drone"
    SATELLITE = "Satellite"
    # Most bots are garage.
    GARAGE = "Garage"
    BUGHOLE = "Bughole"
    ALIEN = "Alien"


class EntityType(Enum):
    BUG = "Bug"
    BOT = "Bot"
    BUILDING = "Building"


@desynced_object
@length_check
class Entity:
    name: str
    description: str
    lua_id: str
    health: int
    power_usage_per_second: int
    movement_speed: float
    flying: bool
    visibility: float
    storage: int
    size: str
    race: Race
    sockets: Sockets
    # Special kind of storage to house this entity.
    slot_type: SlotType
    recipe: Recipe
    types: list[EntityType] = annotate(ListFieldOptions(max_length=2, skip_suffix=False))
    # Shared attributes for wiki metadata
    metadata: WikiMetadata = field(  # pylint: disable=invalid-field-call # type: ignore[misc]
        default_factory=WikiMetadata  # type: ignore[misc]
    )
