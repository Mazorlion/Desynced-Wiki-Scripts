from dataclasses import dataclass
from enum import StrEnum, auto


class DataCategory(StrEnum):
    categoryFilter = auto()  # pylint: disable=invalid-name
    component = auto()  # pylint: disable=invalid-name
    entity = auto()  # pylint: disable=invalid-name
    item = auto()  # pylint: disable=invalid-name
    instruction = auto()  # pylint: disable=invalid-name
    tech = auto()  # pylint: disable=invalid-name
    techCategory = auto()  # pylint: disable=invalid-name
    techUnlock = auto()  # pylint: disable=invalid-name


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
    DataCategory.categoryFilter: DataCategoryInfo(has_page=False),
}


def category_has_human_pages(cat: DataCategory) -> bool:
    info = DATA_CATEGORY_INFO.get(cat)
    return info.has_page if info is not None else False
