from wiki.data_categories import DataCategory

default = """\
{{Infobox}}

{{Recipe cargo|{{PAGENAME}}}}"""

instruction = """\
{{Infobox}}
    
__NOEDITSECTION__
{{Instruction_Bottom}}
"""
tech = """\
{{Infobox}}

__NOEDITSECTION__
{{TechTemplates|{{SUBPAGENAME}}}}

{{TechnologyNav}}

[[Category:Tech]]
"""

CATEGORY_TEMPLATE: dict[DataCategory, str] = {
    DataCategory.entity: default,
    DataCategory.component: default,
    DataCategory.item: default,
    DataCategory.instruction: instruction,
    DataCategory.tech: tech,
}


def GetCategoryTemplate(category: DataCategory) -> str | None:
    """Return the template string for the given data category."""
    return CATEGORY_TEMPLATE.get(category)
