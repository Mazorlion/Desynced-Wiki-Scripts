from typing import List

from models.decorators import desynced_object
from models.decorators_options import FieldOptions, ListFieldOptions, annotate
from models.recipe import Recipe


@desynced_object
class Technology:
    name: str
    lua_id: str
    description: str
    category: str
    texture: str
    # Number of times recipe must be completed.
    progress_count: int
    recipe: Recipe | None
    # List of required techs by name.
    required_tech: List[str] = annotate(ListFieldOptions(max_length=3))


@desynced_object
class TechnologyUnlock:
    tech_name: str
    unlocks: str
    name: str = annotate(FieldOptions(skip_field=True))


@desynced_object
class TechnologyCategory:
    name: str
    discovery_tech: str
    initial_tech: str
    texture: str
    sub_categories: List[str] = annotate(ListFieldOptions(max_length=3))
