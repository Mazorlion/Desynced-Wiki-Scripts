# See https://www.mediawiki.org/wiki/Transclusion#Partial_transclusion_markup for the following functions.
def only_include(source: str) -> str:
    """Wraps `source` in `<onlyinclude>` tags."""
    return f"<onlyinclude>{source}</onlyinclude>"


def no_wiki(source: str) -> str:
    """Wraps `source` in `<nowiki>` tags."""
    return f"<nowiki>{source}</nowiki>"


def no_include(source: str) -> str:
    """Wraps `source` in `<noinclude>` tags."""
    return f"<noinclude>{source}</noinclude>"
