import logging
from pprint import pformat
from typing import Optional
from jinja2 import Environment, FileSystemLoader, Template
from models.entity import Entity
from models.recipe import Recipe

logger = logging.getLogger("templater.py")


def get_category(template: Template) -> Optional[str]:
    """Read the content of the `category` block in `template`.

    You'd be better off pretending this function doesn't exist.
    This function exists so that each template can declare its own category.

    Args:
        template (Template): Template to render the block from.

    Returns:
        Optional[str]: Content of the `category` block or None.
    """
    if not template.blocks["category"]:
        logger.error("Invalid template: " + str(template))
        return None
    return "".join(
        template.blocks["category"](template.new_context({}))
    ).strip()


def remove_none(element):
    return element if element else ""


# Set up the environment and file loader
env = Environment(
    loader=FileSystemLoader("wiki/templates"), finalize=remove_none
)
_recipe_production_template: Template = env.get_template(
    "recipe_production.jinja"
)
_recipe_production_cat = get_category(_recipe_production_template)


def recipe_production_category() -> str:
    return _recipe_production_cat


def render_recipe_production(recipe: Recipe) -> str:
    return _recipe_production_template.render(recipe=recipe)


_entity_stats_template: Template = env.get_template("entity_stats.jinja")
_entity_stats_cat = get_category(_entity_stats_template)


def entity_stats_category() -> str:
    return _entity_stats_cat


def render_entity_stats(entity: Entity) -> str:
    return _entity_stats_template.render(entity=entity)
