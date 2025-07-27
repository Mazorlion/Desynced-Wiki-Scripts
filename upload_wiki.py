import argparse
from dataclasses import dataclass
import logging
import os
from typing import List
from collections import defaultdict

import asyncio
from util.constants import DEFAULT_OUTPUT_DIR
from util.logging_util import PrefixAdapter

from wiki.ratelimiter import limiter
from wiki.wiki_override import DesyncedWiki

current_file = os.path.basename(__file__)


async def run(input_dir: str, dry_run: bool, debug: bool):
    logger = logging.getLogger(current_file)
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )

    logger.info("Starting upload of wiki files from %s", input_dir)

    # really yucky but whatever I'm lazy
    # TODO(maz): Make this into a class.
    if dry_run:
        logger = PrefixAdapter(logger, {"prefix": "DRY_RUN"})

    # Logs in and initializes wiki connection.
    wiki = DesyncedWiki()

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
                existing_content = await limiter(wiki.page_text)(title)

                # Bail if there's no change.
                if content == existing_content:
                    continue

                updated_tables.append(
                    CargoTable(template_title=template_title, table=file)
                )
                logger.debug("Updating %s because content changed", title)
                if dry_run:
                    continue

                await limiter(wiki.edit)(
                    title=title,
                    text=content,
                )

    # Recreate cargo tables here.
    for changed_table in updated_tables:
        logger.debug("Recreating cargo table for %s", changed_table.template_title)
        if dry_run:
            continue

        assert await limiter(wiki.recreate_cargo_table)(
            changed_table.template_title
        ), f"Failed to recreate table for {changed_table.template_title}"

    # Update data files.
    updated_files = defaultdict(list)  # key: category, value: list of titles
    for root, _, files in os.walk(input_dir):
        subcategory = os.path.basename(root)
        if subcategory == "Template":
            continue
        for file in files:
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                title = f"Data:{subcategory}:{file}"
                content: str = f.read()

                # existing_content = await limiter(wiki.page_text)(title)

                # # Bail if there's no change. (long!)
                # if content == existing_content:
                #     continue

                logger.debug("Updating page %s", title)
                updated_files[subcategory].append(title)
                if dry_run:
                    continue

                # Upload the file.
                await limiter(wiki.edit)(
                    title=title,
                    text=content,
                )

    # Recreate cargo data here.
    for changed_table in updated_tables:
        logger.debug("Recreating cargo data for %s", changed_table.template_title)
        if dry_run:
            continue
        assert await limiter(wiki.recreate_cargo_data)(
            changed_table.template_title, changed_table.table
        ), f"Failed to recreate data for {changed_table.template_title}"

    logger.info(
        "Updated tables: %s", ", ".join(t.template_title for t in updated_tables)
    )
    logger.info(f"Updated {len(updated_files)} files:")

    logger.info(f"{'Category':<20} | {'Updated Files':>13}")
    logger.info("-" * 36)
    for category in sorted(updated_files):
        count = len(updated_files[category])
        logger.info(f"{category:<20} | {count:>13}")

    if dry_run:
        logger.info("To commit those changes, run with --no-dry-run")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload previously generated wiki files to Desynced Wiki",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-directory",
        type=str,
        help="Path to the directory containing wiki files for gamedata recipes",
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="If True, prevents any changes to the wiki",
        default="True",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output (sets logging level to DEBUG)",
        default=False,
    )
    args = parser.parse_args()
    asyncio.run(run(args.input_directory, args.dry_run, args.debug))
