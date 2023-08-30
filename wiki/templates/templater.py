import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict

from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger("templater.py")


class WikiTemplate(Enum):
    CARGO_DECLARE = "cargo_declaration.jinja"
    CARGO_STORE = "cargo_storage.jinja"


def remove_none(element):
    return element if element else ""


# Set up the environment and file loader
env = Environment(
    loader=FileSystemLoader("wiki/templates"),
    finalize=remove_none,
    trim_blocks=True,
    lstrip_blocks=True,
)


@dataclass
class CachedTemplate:
    template: Template


cached_templates: dict[WikiTemplate, CachedTemplate] = {}

for template_type in WikiTemplate:
    template = env.get_template(template_type.value)
    cached_templates[template_type] = CachedTemplate(template)


# Actual Public Interface
def render_template(t_type: WikiTemplate, template_args: Dict):
    tmp: Template = cached_templates[t_type].template
    return tmp.render(template_args)
