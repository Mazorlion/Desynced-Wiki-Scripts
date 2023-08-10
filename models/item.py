from dataclasses import dataclass
from enum import Enum


class ItemType(Enum):
    PACKAGE = "Package"
    RESEARCH = "Research"
    RESOURCE = "Resource"
    SIMPLE_MATERIAL = "Simple"
    ADVANCED_MATERIAL = "Advanced"
    HITECH_MATERIAL = "Hi-Tech"

    def is_material(self) -> bool:
        return self in [
            ItemType.SIMPLE_MATERIAL,
            ItemType.ADVANCED_MATERIAL,
            ItemType.HITECH_MATERIAL,
        ]


@dataclass
class Item:
    name: str
    description: str
    stack_size: int
    type: ItemType
