import argparse
import logging
import os
import sys

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
    for root, _, files in os.walk(input_dir):
        subcategory = os.path.basename(root)
        for file in files:
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                if subcategory == "Template":
                    title = f"Template:Data{file[0].upper() + file[1:]}"
                else:
                    title = f"Data:{subcategory}:{file}"

                content: str = f.read()

                # Bail if it's a dry run.
                if dry_run:
                    logger.info("Not uploading %s to %s due to --dry-run.", file, title)
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
