from typing import Dict
from typing import cast
import pywikibot
import pywikibot.login
from pywikibot.site import APISite

from util.config import GetCredentials
from util.logger import get_logger

DESYNCED_WIKI_URL = "https://wiki.desyncedgame.com/api.php"

logger = get_logger()


class DesyncedWiki:
    """pywikibot wrapper, handles auth and configuration

    Usage:
        wiki = DesyncedWiki()
        page: Page = wiki.page(title)
        if page.text = ...
    """

    CONFIG_SECTION_NAME = "wiki"

    _site: APISite

    def __init__(
        self,
    ):
        username, password = GetCredentials(self.CONFIG_SECTION_NAME)

        self._site = cast(APISite, pywikibot.Site(url=DESYNCED_WIKI_URL, user=username))
        login_manager = pywikibot.login.ClientLoginManager(
            site=self._site, user=username, password=password
        )
        login_manager.login_to_site()
        self._site.login(user=username)
        # throttle: Throttle = Throttle(site=self._site)
        # self._site.throttle = throttle

        logged_user = self._site.user()
        if not logged_user:
            raise ValueError("Failed to login, logic error?")

        logger.info(f"Logged in to wiki as user {logged_user}")

    def recreate_cargo_table(self, template_name: str) -> bool:
        # https://all.docs.genesys.com/api.php?action=help&modules=cargorecreatetables
        form: Dict = {
            "template": template_name,
            "createReplacement": "true",
        }

        try:
            result = self._site.post(action="cargorecreatetables", **form)
            print("Cargo table recreation triggered:", result)
            return True
        except pywikibot.exceptions.APIError as e:
            print("API error:", e)
            logger.error(f"recreate_cargo_table failed with: {e.info}")

        return False

    def recreate_cargo_data(self, template_name: str, table_name: str) -> bool:
        form: Dict = {"template": template_name, "table": table_name}

        try:
            result = self._site.post(action="cargorecreatedata", **form)
            print("Cargo table data recreation triggered:", result)
            return True
        except pywikibot.exceptions.APIError as e:
            print("API error:", e)
            logger.error(f"recreate_cargo_data failed with: {e.info}")

        return False

    def page(self, title):
        return pywikibot.Page(self._site, title)

    def filepage(self, title):
        return pywikibot.FilePage(self._site, title)
