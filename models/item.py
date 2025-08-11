from enum import Enum
from typing import List

from models.decorators import desynced_object, length_check
from models.decorators_options import ListFieldOptions, annotate
from models.recipe import Recipe


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


class ItemSlotType(Enum):
    STORAGE = "Storage"
    ALIEN_STORAGE = "Alien Storage"
    GAS = "Gas"
    ANOMALY = "Anomaly"
    VIRUS = "Virus"
    ALIEN = "Alien"


@desynced_object
class MiningRecipe:
    # Name of mining component.
    miner_component: str
    # Number of seconds to mine the item.
    mining_seconds: float


@desynced_object
@length_check
class Item:
    name: str
    lua_id: str
    description: str
    # Item Category.
    type: ItemType
    # Some items are stored in a special storage (such as gas).
    slot_type: ItemSlotType
    # Recipe to produce this item.
    production_recipe: Recipe
    # Tag for category matching
    tag: str
    # If this `Item` is mineable, this is a list of components that can mine it.
    mining_recipes: List[MiningRecipe] = annotate(ListFieldOptions(max_length=4))
    # How many of this item stack in a single slot.
    stack_size: int = 1


# data.items.sampleitem = {
# 	name = "<NAME>",
# 	texture = "<PATH/TO/IMAGE.png>",
# 	slot_type = "storage|intel|liquid|radioactive|...",
# 	-- Optional
# 	stack_size = <COUNT>, --default: 1
# 	visual = "<VISUAL>", -- visual to use when visible in world
# 	-- Recipe of produced item
# 	production_recipe = CreateProductionRecipe(
# 		{ <INGREDIENT_ITEM_ID> = <INGREDIENT_NUM>, ... },
# 		{ <PRODUCTION_COMPONENT_ID> = <PRODUCTION_TICKS>, }
# 		-- Optional
# 		<AMOUNT_NUM>, --default: 1
# 	),
# 	-- Recipe of resources harvested from the world
# 	mining_recipe = CreateMiningRecipe({ <MINER_COMPONENT_ID = <MINING_TICKS>, ... }),
# }
# -- when renaming an id
# data.update_mapping.simulation_data = "datacube_matrix"
