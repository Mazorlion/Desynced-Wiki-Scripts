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
    hasPage: bool  # object in this category should have their own page
    subPageOf: str | None = None


DATA_CATEGORY_INFO: dict[DataCategory, DataCategoryInfo] = {
    DataCategory.entity: DataCategoryInfo(hasPage=True),
    DataCategory.component: DataCategoryInfo(hasPage=True),
    DataCategory.item: DataCategoryInfo(hasPage=True),
    DataCategory.instruction: DataCategoryInfo(hasPage=True, subPageOf="Instructions"),
    DataCategory.tech: DataCategoryInfo(hasPage=True, subPageOf="Technology"),
    DataCategory.techUnlock: DataCategoryInfo(hasPage=False),
    DataCategory.techCategory: DataCategoryInfo(hasPage=False),
}


def CategoryHasPage(cat: DataCategory) -> bool:
    info = DATA_CATEGORY_INFO.get(cat)
    return info.hasPage if info is not None else False


def GetPagePrefix(cat: DataCategory) -> str:
    info = DATA_CATEGORY_INFO.get(cat)
    if info and info.subPageOf:
        return f"{info.subPageOf}/"

    return ""
