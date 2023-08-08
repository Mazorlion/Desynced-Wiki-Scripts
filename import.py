import logging
import sys
import os
import argparse
from ratelimiter import RateLimiter
from wiki.wiki_override import DesyncedWiki

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("import.py")


def run(input_dir: str, dry_run: bool):
    # TODO(maz): Compare content to existing page to avoid unecessary edits

    # 90 calls per minute.
    rate_limiter = RateLimiter(max_calls=3, period=2)
    # Logs in and initializes wiki connection.
    wiki = DesyncedWiki()
    # Walk the recipes directory and upload each file there.
    for root, dirs, files in os.walk(input_dir):
        subcategory = os.path.basename(root)
        for file in files:
            with open(os.path.join(root, file), "r") as f:
                title: str = f"GameData:{subcategory}:{file}"
                content: str = f.read()

                # Bail if it's a dry run.
                if dry_run:
                    logger.info(
                        f"Not uploading {file} to {title} due to --dry-run."
                    )
                    continue

                # Upload the file.
                with rate_limiter:
                    wiki.edit(
                        title=title,
                        text=content,
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
