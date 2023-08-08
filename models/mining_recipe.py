from pprint import pformat
from models.recipe import RecipeProducer

TEMPLATE_NUM_PRODUCERS = 4


class MiningRecipe:
    def __init__(self, name: str, producers: list[RecipeProducer]):
        self.name: str = name
        self.producers: list[RecipeProducer] = sorted(
            producers, key=lambda x: x.name
        )
        self.template_str = self.to_template()

    def to_template(self) -> str:
        return (
            "{{MiningRecipe|"
            + f"{self.name}{self._producers_to_template()}"
            + "}}"
        )

    def _producers_to_template(self) -> str:
        ret = ""
        for producer in self.producers:
            ret += f"|{producer.name}|{str(producer.time)}"
        padding: int = TEMPLATE_NUM_PRODUCERS - len(self.producers)
        for i in range(padding):
            ret += "||"
        return ret

    def __repr__(self) -> str:
        return pformat(vars(self)) or ""
