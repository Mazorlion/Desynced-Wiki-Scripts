from util.constants import WIKI_BASE_URL


class WikiUrl:
    @staticmethod
    def cleanup_title(pagename: str) -> str:
        return pagename.replace(" ", "_")

    @staticmethod
    def get_page(pagename: str) -> str:
        return f"{WIKI_BASE_URL}/{WikiUrl.cleanup_title(pagename)}"

    @staticmethod
    def get_page_history(pagename: str) -> str:
        return f"{WIKI_BASE_URL}/index.php?title={WikiUrl.cleanup_title(pagename)}&action=history'"
