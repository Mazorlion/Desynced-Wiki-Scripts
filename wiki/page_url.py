from util.constants import WIKI_BASE_URL


class WikiUrl:
    @staticmethod
    def cleanup_title(full_title: str) -> str:
        return full_title.replace(" ", "_")

    @staticmethod
    def get_page(full_title: str) -> str:
        return f"{WIKI_BASE_URL}/{WikiUrl.cleanup_title(full_title)}"

    @staticmethod
    def get_page_history(full_title: str) -> str:
        return f"{WIKI_BASE_URL}/index.php?title={WikiUrl.cleanup_title(full_title)}&action=history'"
