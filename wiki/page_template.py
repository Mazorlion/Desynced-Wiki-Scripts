from dataclasses import dataclass
from typing import TypeAlias

from pywikibot import Page
from util.logger import get_logger
from wiki.data_categories import DataCategory

logger = get_logger()

# MediaWiki templates
DEFAULT = """\
{{Infobox}}

__NOEDITSECTION__
{{Recipe cargo|{{PAGENAME}}}}"""

INSTRUCTION = """\
{{Instruction_Top}}
    
__NOEDITSECTION__
{{Instruction_Bottom}}
"""
TECH = """\
{{Infobox}}

__NOEDITSECTION__
{{TechTemplates|{{SUBPAGENAME}}}}

{{TechnologyNav}}

[[Category:Tech]]
"""

CATEGORY_PAGE_BLUEPRINT: dict[DataCategory, str] = {
    DataCategory.entity: DEFAULT,
    DataCategory.component: DEFAULT,
    DataCategory.item: DEFAULT,
    DataCategory.instruction: INSTRUCTION,
    DataCategory.tech: TECH,
}


def get_category_page_blueprint(category: DataCategory) -> str | None:
    """Return the template string for the given data category."""
    return CATEGORY_PAGE_BLUEPRINT.get(category)


TemplateName: TypeAlias = str


@dataclass
class TemplateInfo:
    """Metadata about templates used in MediaWiki pages"""

    arg_count: int
    max_arg_count: int

    def validate(self, other: "TemplateInfo"):
        return (
            other.arg_count >= self.arg_count and other.arg_count <= self.max_arg_count
        )


# Hardcoded info about what the arguments expect... might get out of date pretty quick
TEMPLATES_INFO: dict[TemplateName, TemplateInfo] = {
    "Infobox": TemplateInfo(0, 0),
    "Recipe cargo": TemplateInfo(1, 1),
    "Instruction_Top": TemplateInfo(0, 0),
    "Instruction_Bottom": TemplateInfo(0, 0),
    "TechTemplates": TemplateInfo(1, 1),
    "TechnologyNav": TemplateInfo(0, 0),
}


def get_template_info(template_name) -> TemplateInfo | None:
    return TEMPLATES_INFO.get(template_name)


def extract_template_info(template_content) -> tuple[TemplateName, TemplateInfo] | None:
    template_name = template_content.split("|")[0].split("#")[0].strip()
    arg_count = template_content.count("|")
    if not template_name:
        logger.warning(
            f"Unexpected empty template, logic error or bad page data? template was: '{template_content}'"
        )
        return None

    return template_name, TemplateInfo(arg_count, arg_count)


def extract_templates_info_from_page(
    content: str,
) -> list[tuple[TemplateName, TemplateInfo]]:
    """Extract all template names & info from the given page content.

    Uses a read pointer approach to handle multi-line templates and nested templates.
    The template name is all text before the first | (if any, else it's all text).
    """
    templates_in_content = []
    read_pointer = 0
    content_length = len(content)

    while read_pointer < content_length:
        # Find the next template start
        start_pos = content.find("{{", read_pointer)
        if start_pos == -1:
            break

        # Find the corresponding template end
        end_pos = content.find("}}", start_pos)
        if end_pos == -1:
            break

        # Extract the template content
        template_content = content[start_pos + 2 : end_pos].strip()

        # Process nested templates recursively
        nested_templates = extract_templates_info_from_page(template_content)
        templates_in_content.extend(nested_templates)

        # Extract the main template name
        templates_in_content.append(extract_template_info(template_content))

        # Move the read pointer past this template
        read_pointer = end_pos + len("}}")

    return templates_in_content


def extract_templates_from_page(content: str) -> list[TemplateName]:
    """Extract all template names from the given page content.

    Uses a read pointer approach to handle multi-line templates and nested templates.
    The template name is all text before the first | (if any, else it's all text).
    """
    templates_in_content = extract_templates_info_from_page(content)
    return [name for name, _ in templates_in_content]


def page_has_template(content: str, template: str) -> bool:
    templates = extract_templates_from_page(content)
    return template in templates


# Testing, using Page instead. Could be great to use Page everywhere here but that's some rework.
def page_has_template_title(page: Page, template_title: str) -> bool:
    return any(t.title == template_title for t in page.templates())


def __compute_mandatory_templates() -> dict[DataCategory, list[TemplateName]]:
    """Go through all CATEGORY_TEMPLATE categories. For each of those, we get the template (get_category_template),
    then parse the text to find all listed (mediawiki) templates. We make a list of them, then validate if we have info for all of
    them in TEMPLATES_INFO. Error then raise if we don't."""
    mandatory_templates = {}

    for category, template_text in CATEGORY_PAGE_BLUEPRINT.items():
        mandatory_templates[category] = extract_templates_from_page(template_text)

    return mandatory_templates


MANDATORY_TEMPLATES = __compute_mandatory_templates()


def get_mandatory_templates(query_category: DataCategory) -> list[TemplateName]:
    for category, templates in MANDATORY_TEMPLATES.items():
        if category == query_category:
            return [name for name in templates]

    return []


# We could further
