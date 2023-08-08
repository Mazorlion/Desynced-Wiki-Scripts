import ast
from dataclasses import dataclass
from enum import Enum
import logging
from typing import Optional
from jinja2 import Environment, FileSystemLoader, Template, meta

logger = logging.getLogger("templater.py")


def _parse_category(template: Template) -> Optional[str]:
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


class WikiTemplate(Enum):
    RECIPE_PRODUCTION = "recipe_production.jinja"
    ENTITY_STATS = "entity_stats.jinja"


@dataclass
class CachedTemplate:
    template: Template
    category: str
    var_name: str


cached_templates: dict[WikiTemplate, CachedTemplate] = {}


def get_var_name(ast: ast) -> str:
    return meta.find_undeclared_variables(ast).pop()


for type in WikiTemplate:
    template = env.get_template(type.value)
    category = _parse_category(template)
    var_name = get_var_name(env.parse(env.loader.get_source(env, type.value)))
    cached_templates[type] = CachedTemplate(template, category, var_name)


# Actual Public Interface
# TODO(maz): Hide the above stuff better
def render_template(type: WikiTemplate, object):
    template: Template = cached_templates[type].template
    var_name = cached_templates[type].var_name
    return template.render({var_name: object})


def get_category(type: WikiTemplate) -> str:
    return cached_templates[type].category
