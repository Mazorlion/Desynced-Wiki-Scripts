from util.constants import WIKI_BASE_URL


class WikiUrl:
    @staticmethod
    def cleanup_title(title: str) -> str:
        # could use Page functions here instead
        return title.replace(" ", "_")

    @staticmethod
    def get_page(title: str) -> str:
        return f"{WIKI_BASE_URL}/{WikiUrl.cleanup_title(title)}"

    @staticmethod
    def get_page_history(title: str) -> str:
        return f"{WIKI_BASE_URL}/index.php?title={WikiUrl.cleanup_title(title)}&action=history'"
