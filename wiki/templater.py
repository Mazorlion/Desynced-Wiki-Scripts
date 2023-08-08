import logging
from pprint import pformat
from typing import Optional
from jinja2 import Environment, FileSystemLoader, Template
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
        recipe_production_template.blocks["category"](
            recipe_production_template.new_context({})
        )
    ).strip()


# Set up the environment and file loader
env = Environment(loader=FileSystemLoader("wiki/templates"))
recipe_production_template: Template = env.get_template(
    "recipe_production.jinja"
)
_recipe_production_cat = get_category(recipe_production_template)


def recipe_production_category() -> str:
    return _recipe_production_cat


def render_recipe_production(recipe: Recipe) -> str:
    return recipe_production_template.render(recipe=recipe)
