def get_data_page_title(table: str, human_title: str) -> str:
    return f"Data:{table}:{human_title}"


def get_template_title(category: str):
    """Not the same as the page name"""
    return f"Data{category[0].upper() + category[1:]}"  # "component" -> "DataComponent"


def get_template_page(template_title: str):
    return f"Template:{template_title}"
