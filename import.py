import argparse
from dataclasses import dataclass
import logging
import os
from re import template
import sys
from typing import List

from ratelimiter import RateLimiter
from util.logging_util import PrefixAdapter

from wiki.wiki_override import DesyncedWiki

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)
logger = logging.getLogger("import.py")


def run(input_dir: str, dry_run: bool):
    # TODO(maz): Compare content to existing page to avoid unecessary edits

    # 90 calls per minute.
    rate_limiter = RateLimiter(max_calls=3, period=2)
    # Logs in and initializes wiki connection.
    wiki = DesyncedWiki()

    # really yucky but whatever I'm lazy
    # TODO(maz): Make this into a class.
    global logger
    if dry_run:
        logger = PrefixAdapter(logger, {"prefix": "DRY_RUN"})

    @dataclass
    class CargoTable:
        template_title: str
        table: str

    updated_tables: List[CargoTable] = []
    # Walk the recipes directory and upload each file there.
    for root, _, files in os.walk(input_dir):
        subcategory = os.path.basename(root)
        if subcategory != "Template":
            continue
        for file in files:
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                template_title = f"Data{file[0].upper() + file[1:]}"
                title = f"Template:{template_title}"
                content: str = f.read()

                # Upload the file.
                existing_content = None
                with rate_limiter:
                    existing_content = wiki.page_text(title)

                # Bail if there's no change.
                if content == existing_content:
                    continue

                updated_tables.append(
                    CargoTable(template_title=template_title, table=file)
                )
                logger.info("Updating %s because content changed", title)
                if dry_run:
                    continue

                with rate_limiter:
                    wiki.edit(
                        title=title,
                        text=content,
                    )

    # Recreate cargo tables here.
    for changed_table in updated_tables:
        logger.info("Recreating cargo table for %s", changed_table.template_title)
        if dry_run:
            continue
        with rate_limiter:
            assert wiki.recreate_cargo_table(
                changed_table.template_title
            ), f"Failed to recreate table for {changed_table.template_title}"

    # Update data files.
    for root, _, files in os.walk(input_dir):
        subcategory = os.path.basename(root)
        if subcategory == "Template":
            continue
        for file in files:
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                title = f"Data:{subcategory}:{file}"
                content: str = f.read()
                logger.info("Updating page %s", title)
                if dry_run:
                    continue

                # Upload the file.
                with rate_limiter:
                    wiki.edit(
                        title=title,
                        text=content,
                    )

    # Recreate cargo data here.
    for changed_table in updated_tables:
        logger.info("Recreating cargo data for %s", changed_table.template_title)
        if dry_run:
            continue
        with rate_limiter:
            assert wiki.recreate_cargo_data(
                changed_table.template_title, changed_table.table
            ), f"Failed to recreate data for {changed_table.template_title}"


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
