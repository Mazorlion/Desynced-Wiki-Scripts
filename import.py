import logging
import sys
import os
import argparse
from wiki.wiki_override import DesyncedWiki

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("import.py")


def run(recipe_dir: str, dry_run: bool):
    # Logs in and initializes wiki connection.
    wiki = DesyncedWiki()
    # Walk the recipes directory and upload each file there.
    for root, dirs, files in os.walk(recipe_dir):
        for file in files:
            with open(os.path.join(root, file), "r") as f:
                if dry_run:
                    logger.info(f"Not uploading {file} due to --dry_run.")
                else:
                    logger.info(f"Uploading {file}")
                    wiki.edit(title=f"GameData:Recipe:{file}", text=f.read())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--recipe_directory",
        type=str,
        help="Path to the directory containing wiki files for gamedata recipes.",
        default="wiki/GameData/Recipe",
    )
    parser.add_argument(
        "--dry_run",
        type=bool,
        help="If True, prevents any changes to the wiki. Default: True.",
        default="True",
    )

    args = parser.parse_args()
    run(args.recipe_directory, args.dry_run)
