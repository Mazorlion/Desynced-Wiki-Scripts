from enum import Enum
from pprint import pprint

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
        self.race: str = race
        self.name: str = name
        self.items: list[RecipeItem] = items
        self.producers: list[RecipeProducer] = producers or []
        self.template_str: str = self.to_template()
        self.is_derived: bool = is_derived

    # Template: {{Recipe|Name|Item1|Amount1|Item2|Amount2|Item3|Amount3|Item4|Amount4|ProducedBy1|Time1|ProducedBy2|Time2}}
    # See: https://wiki.desyncedgame.com/Template:Recipe
    def to_template(self) -> str:
        return (
            "{{Recipe|"
            + f"{self.name}{self._items_to_template()}{self._producers_to_template()}"
            + "}}"
        )

    def _items_to_template(self) -> str:
        ret = ""
        for item in self.items:
            ret += str(item)
        padding: int = TEMPLATE_NUM_ITEMS - len(self.items)
        for i in range(padding):
            ret += "||"
        return ret

    def _producers_to_template(self) -> str:
        ret = ""
        for producer in self.producers:
            ret += f"|{producer.name}|{str(producer.time)}"
        padding: int = TEMPLATE_NUM_PRODUCERS - len(self.producers)
        for i in range(padding):
            ret += "||"
        return ret

    def __repr__(self) -> str:
        return pprint(vars(self)) or ""


# TODO(maz): Mining recipe? Maybe separate class.
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
