import logging
import sys
import os
import argparse
from wiki.wiki_override import DesyncedWiki

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("import.py")


def run(input_dir: str, dry_run: bool):
    # TODO(maz): Compare content to existing page to avoid unecessary edits

    # Logs in and initializes wiki connection.
    wiki = DesyncedWiki()
    # Walk the recipes directory and upload each file there.
    for root, dirs, files in os.walk(input_dir):
        subcategory = os.path.basename(root)
        for file in files:
            with open(os.path.join(root, file), "r") as f:
                if dry_run:
                    logger.info(
                        f"Not uploading {file} to GameData:{subcategory}:{file} due to --dry-run."
                    )
                else:
                    logger.info(
                        f"Uploading {file}  to GameData:{subcategory}:{file}"
                    )
                    wiki.edit(
                        title=f"GameData:{subcategory}:{file}", text=f.read()
                    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-directory",
        type=str,
        help="Path to the directory containing wiki files for gamedata recipes.",
        default="Output",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="If True, prevents any changes to the wiki. Default: True.",
        default="True",
    )

    args = parser.parse_args()
    run(args.input_directory, args.dry_run)
