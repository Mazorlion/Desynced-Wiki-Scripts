from enum import Enum
from pprint import pformat

from models.types import Race

# Number of expected items/producers in the template.
# See: https://wiki.desyncedgame.com/Template:Recipe
TEMPLATE_NUM_ITEMS = 4
TEMPLATE_NUM_PRODUCERS = 2


class Recipe:
    """Class representing a recipe for some item/building/unit."""

    def __init__(
        self, recipe_type, race, name, items, producers, is_derived
    ) -> None:
        self.type: RecipeType = recipe_type
        self.race: Race = race
        self.name: str = name
        self.items: list[RecipeItem] = sorted(items, key=lambda x: x.name)
        self.producers: list[RecipeProducer] = producers or []
        self.producers = sorted(self.producers, key=lambda x: x.name)
        self.is_derived: bool = is_derived

    def __repr__(self) -> str:
        return pformat(vars(self)) or ""


class RecipeType(Enum):
    Construction = 1
    Production = 2


class RecipeItem:
    """Item in a recipe"""

    def __init__(self, readable_name, amount) -> None:
        self.name: str = readable_name
        self.amount: int = amount

    def __repr__(self) -> str:
        return f"|{self.name}|{str(self.amount)}"


class RecipeProducer:
    """Producer of a recipe."""

    def __init__(self, readable_name: str, time_seconds: int) -> None:
        """
        Args:
            name (str): Name of the producer (NOT ID)
            time (int): Time in SECONDS to produce
        """
        self.name: str = readable_name
        self.time: int = time_seconds

    def __repr__(self) -> str:
        return f"|{self.name}|{str(self.time)}"
