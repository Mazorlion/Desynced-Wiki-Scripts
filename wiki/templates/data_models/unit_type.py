from enum import Enum
from unittest import case

from models.entity import Entity, SlotType
from models.types import Race


class UnitType(Enum):
    BOT = "Bot"
    DRONE = "Drone"
    ALIEN = "Alien"
    BUG = "Bug"
    HUMAN = "Human"
    SPACE = "Space"


def derive_unit_type(entity: Entity) -> UnitType:
    if entity.race == Race.ALIEN:
        return UnitType.ALIEN

    if entity.race == Race.BUG:
        return UnitType.BUG

    if entity.race == Race.HUMAN:
        return UnitType.HUMAN

    entity.type

    slot_unit_mapping = {
        SlotType.SATELLITE: UnitType.SPACE,
        SlotType.GARAGE: UnitType.BOT,
        SlotType.DRONE: UnitType.DRONE,
    }

    if entity.slot_type == SlotType.SATELLITE:
        return UnitType.SPACE
