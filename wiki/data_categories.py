from dataclasses import dataclass
from enum import StrEnum, auto


class DataCategory(StrEnum):
    entity = auto()
    component = auto()
    item = auto()
    instruction = auto()
    tech = auto()
    techUnlock = auto()
    techCategory = auto()


@dataclass
class DataCategoryInfo:
    has_page: bool  # object in this category should have their own page
    subpage_of: str | None = None


DATA_CATEGORY_INFO: dict[DataCategory, DataCategoryInfo] = {
    DataCategory.entity: DataCategoryInfo(has_page=True),
    DataCategory.component: DataCategoryInfo(has_page=True),
    DataCategory.item: DataCategoryInfo(has_page=True),
    DataCategory.instruction: DataCategoryInfo(
        has_page=True, subpage_of="Instructions"
    ),
    DataCategory.tech: DataCategoryInfo(has_page=True, subpage_of="Technology"),
    DataCategory.techUnlock: DataCategoryInfo(has_page=False),
    DataCategory.techCategory: DataCategoryInfo(has_page=False),
}


def CategoryHasPage(cat: DataCategory) -> bool:
    info = DATA_CATEGORY_INFO.get(cat)
    return info.has_page if info is not None else False


def GetPagePrefix(cat: DataCategory) -> str:
    info = DATA_CATEGORY_INFO.get(cat)
    if info and info.subpage_of:
        return f"{info.subpage_of}/"

    return ""
