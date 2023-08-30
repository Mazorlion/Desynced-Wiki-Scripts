import argparse
from ratelimiter import RateLimiter

from wiki.wiki_override import DesyncedWiki


def should_prune(page: str) -> bool:
    lower_name = page.lower()

    if lower_name in ["simulator"] or any(
        exclusion in lower_name
        for exclusion in [
            "artificial",
            "alien",
            "human",
            "curious",
            "attack",
            "c_",
            "spawner",
            "hive",
            "mothika",
            "gigakaiju",
            "ravager",
            "scale worm",
            "trilobyte",
            "malika",
        ]
    ):
        return True

    return False


def run(dry_run: bool):
    # 90 calls per minute.
    rate_limiter = RateLimiter(max_calls=3, period=2)
    # Logs in and initializes wiki connection.
    wiki = DesyncedWiki()

    # 90 calls per minute.
    rate_limiter = RateLimiter(max_calls=3, period=2)

    for cat in wiki.category_members("Category:Data:Storage"):
        for page in wiki.category_members(cat):
            if should_prune(page):
                print(f"Deleting {page}")
                with rate_limiter:
                    wiki.edit(page, "Pruned hidden game data.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="If True, prevents any changes to the wiki. Default: True.",
        default="True",
    )

    args = parser.parse_args()
    run(args.dry_run)
