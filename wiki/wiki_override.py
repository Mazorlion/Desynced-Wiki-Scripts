from pwiki.wiki import Wiki
from wiki_credentials import username, password

DESYNCED_WIKI_URL = "wiki.desyncedgame.com"


class DesyncedWiki(Wiki):
    """Overrides the regular `pwiki.Wiki` to intercept the endpoint.

    By default the underlying `Wiki` class forced the endpoint to be `/w/api.php`.
    However the actual endpoint for the desynced wiki is `api.php`.

    Usage:
        wiki = DesyncedWiki()
        wiki.edit(...)
    """

    def __init__(
        self,
    ):
        self.endpoint = f"https://{DESYNCED_WIKI_URL}/api.php"
        super().__init__(
            DESYNCED_WIKI_URL,
            username,
            password,
        )
        # Override bot status even without the "bot" permission.
        self.is_bot = True

    def __setattr__(self, name, value):
        # Block the super constructor from setting the endpoint to something bad
        if name == "endpoint" and hasattr(self, "endpoint"):
            return
        else:
            super().__setattr__(name, value)
