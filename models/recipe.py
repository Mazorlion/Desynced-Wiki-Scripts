from enum import StrEnum
from typing import List

from models.decorators import desynced_object
from models.decorators_options import ListFieldOptions, annotate


class RecipeTypeGame(StrEnum):
    """Value matches the field names used in game."""

    CONSTRUCTION = "construction_recipe"
    PRODUCTION = "production_recipe"
    UPLINK = "uplink_recipe"
    ITEMS = "items"
    PRODUCERS = "producers"
    CONSTRUCTION_TICKS = "ticks"


class RecipeType(StrEnum):
    Construction = "Construction"
    Production = "Production"
    Uplink = "Uplink"


@desynced_object
class RecipeItem:
    # Item name.
    ingredient: str
    # Numer of the required item.
    amount: int


@desynced_object
class RecipeProducer:
    # Name of producing component.
    producer: str
    # Time in seconds to produce.
    time: float


@desynced_object
class Recipe:
    items: List[RecipeItem] = annotate(ListFieldOptions(max_length=4))
    producers: List[RecipeProducer] = annotate(ListFieldOptions(max_length=4))
    recipe_type: RecipeType
    # For production recipes, the type produced may be greater than one.
    num_produced: int

    def __post_init__(self):
        """Sort the internal lists so that they always get exported in a consistent order."""
        self.items: list[RecipeItem] = sorted(self.items, key=lambda x: x.ingredient)
        self.producers = sorted(self.producers, key=lambda x: x.producer)
