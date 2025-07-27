import argparse
import asyncio

from wiki.ratelimiter import limiter
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


async def run(dry_run: bool):
    # Logs in and initializes wiki connection.
    wiki = DesyncedWiki()

    for cat in wiki.category_members("Category:Data:Storage"):
        for page in wiki.category_members(cat):
            if should_prune(page):
                print(f"Deleting {page}")
                if dry_run:
                    continue

                await limiter(wiki.edit)(page, "Pruned hidden game data.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="If True, prevents any changes to the wiki",
        default="True",
    )

    args = parser.parse_args()
    asyncio.run(run(args.dry_run))
