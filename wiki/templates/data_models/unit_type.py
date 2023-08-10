from enum import Enum
from typing import Optional
from unittest import case

from models.entity import Entity, EntityType, SlotType
from models.types import Race


class UnitType(Enum):
    BOT = "Bot"
    DRONE = "Drone"
    ALIEN = "Alien"
    BUG = "Bug"
    HUMAN = "Human"
    SPACE = "Space"


def derive_unit_type(entity: Entity) -> Optional[UnitType]:
    if entity.race == Race.ALIEN:
        return UnitType.ALIEN

    if entity.race == Race.BUG or EntityType.BUG in entity.types:
        return UnitType.BUG

    if entity.race == Race.HUMAN:
        return UnitType.HUMAN

    if entity.slot_type == SlotType.DRONE:
        return UnitType.DRONE

    if entity.slot_type == SlotType.SATELLITE:
        return UnitType.SPACE

    if EntityType.BOT in entity.types:
        return UnitType.BOT

    return None
