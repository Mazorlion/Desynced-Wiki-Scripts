from dataclasses import dataclass
from enum import Enum
from models.entity import Entity, EntityType
from models.item import Item

from models.types import Race
from wiki.templates.data_models.unit_type import UnitType, derive_unit_type


@dataclass
class Category:
    class EntityType(Enum):
        UNIT = "Unit"
        BUILDING = "Building"

    class MaterialType(Enum):
        SIMPLE = "Simple"
        ADVANCED = "Advanced"
        HITECH = "High-tech"

    class ItemType(Enum):
        COMPONENT = "Component"
        RESOURCE = "Resource"
        MATERIAL = "Material"
        RESEARCH = "Research"
        PACKAGE = "Package"

    race: Race = None
    item_type: ItemType = None
    material_type: MaterialType = None
    entity_type: EntityType = None
    unit_type: UnitType = None


def category_from_entity(entity: Entity) -> Category:
    return Category(
        race=entity.race,
        entity_type=Category.EntityType.BUILDING
        if EntityType.BUILDING in entity.types
        else Category.EntityType.UNIT,
        unit_type=derive_unit_type(entity),
    )


def category_from_item(item: Item) -> Category:
    material_type = None
    item_type = None

    if item.type.is_material():
        item_type = Category.ItemType.MATERIAL
        material_type = Category.MaterialType[item.type.name.split("_")[0]]

    return Category(item_type=item_type, material_type=material_type)
