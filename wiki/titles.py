from wiki.data_categories import DATA_CATEGORY_INFO, DataCategory


def get_human_page_title(cat: DataCategory, subpagename: str) -> str:
    info = DATA_CATEGORY_INFO.get(cat)
    if info and info.subpage_of:
        return f"{info.subpage_of}/{subpagename}"
    else:
        return subpagename


def get_data_page_title(category: DataCategory, human_title: str) -> str:
    return f"Data:{category}:{human_title}"


def get_template_title(category: str):
    """Not the same as the page name"""
    return f"Data{category[0].upper() + category[1:]}"  # "component" -> "DataComponent"


def get_template_page(template_title: str):
    return f"Template:{template_title}"


def get_sub_pagename(title: str) -> str:
    return title.split("/")[-1]


def get_base_pagename(title: str) -> str:
    return title.split("/")[0]
