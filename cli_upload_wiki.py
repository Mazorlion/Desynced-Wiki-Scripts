import argparse
from dataclasses import dataclass
import logging
import os
from collections import defaultdict

import asyncio
from util.constants import DEFAULT_WIKI_OUTPUT_DIR
from util.logger import PrefixAdapter, get_logger

from util.ratelimiter import limiter
from wiki.titles import get_data_page_title, get_template_title
from wiki.wiki_override import DesyncedWiki


async def run(input_dir: str, dry_run: bool):
    logger.info(f"Starting upload of wiki files from {input_dir}")

    # Logs in and initializes wiki connection.
    wiki = DesyncedWiki()

    @dataclass(frozen=True)
    class CargoTable:
        template_title: str
        table: str

    updated_tables: set[CargoTable] = set()
    # Walk the template directory and upload each file there.
    for root, _, files in os.walk(input_dir):
        subcategory = os.path.basename(root)
        if subcategory != "Template":
            continue

        # Update templates
        for file in files:
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                template_title = get_template_title(file)
                title = f"Template:{template_title}"
                content: str = f.read()

                # Upload the file.
                wiki_content = await limiter(wiki.page_text)(title)

                # Bail if there's no change.
                if content == wiki_content:
                    continue

                updated_tables.add(
                    CargoTable(template_title=template_title, table=file)
                )
                logger.info(f"Updating {title} because content changed")
                if dry_run:
                    continue

                await limiter(wiki.edit)(
                    title=title,
                    text=content,
                )

    # Recreate cargo tables here.
    for changed_table in updated_tables:
        logger.info(
            f"Triggering recreating cargo TABLE for {changed_table.template_title}"
        )
        if dry_run:
            continue

        assert await limiter(wiki.recreate_cargo_table)(
            changed_table.template_title
        ), f"Failed to recreate table for {changed_table.template_title}"

    # Update data files.
    updated_files = defaultdict(list)  # key: category, value: list of titles
    for root, _, files in os.walk(input_dir):
        table = os.path.basename(root)
        if table == "Template":
            continue
        template_title = get_template_title(table)
        for file in files:
            with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                title = get_data_page_title(table, file)
                content: str = f.read()

                wiki_content = await limiter(wiki.page_text)(title)

                # Bail if there's no change. (long!)
                if content == wiki_content:
                    continue

                logger.debug(f"Updating page {title}")
                updated_files[table].append(title)

                updated_tables.add(
                    CargoTable(template_title=template_title, table=table)
                )

                if dry_run:
                    continue

                # Upload the file.
                await limiter(wiki.edit)(
                    title=title,
                    text=content,
                )

    # Recreate cargo data here.
    for changed_table in updated_tables:
        logger.info(
            f"Triggering recreating cargo DATA for table {changed_table.table} template {changed_table.template_title}"
        )
        if dry_run:
            continue

        assert await limiter(wiki.recreate_cargo_data)(
            changed_table.template_title, changed_table.table
        ), f"Failed to recreate data for {changed_table.template_title}"

    updated_table_list = ", ".join(t.template_title for t in updated_tables)
    logger.info(f"Updated tables: {updated_table_list}")
    logger.info(f"Updated {len(updated_files)} files:")

    logger.info(f"{'Category':<20} | {'Updated Files':>13}")
    logger.info("-" * 36)
    for category in sorted(updated_files):
        count = len(updated_files[category])
        logger.info(f"{category:<20} | {count:>13}")

    if dry_run:
        logger.info("To commit those changes, run with --no-dry-run")


logger = get_logger()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload previously generated wiki files to Desynced Wiki",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-directory",
        type=str,
        help="Path to the directory containing wiki files for gamedata recipes",
        default=DEFAULT_WIKI_OUTPUT_DIR,
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

    logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
    # really yucky but whatever I'm lazy
    # TODO(maz): Make this into a class.
    if args.dry_run:
        logger = PrefixAdapter(logger, {"prefix": "DRY_RUN"})

    asyncio.run(run(args.input_directory, args.dry_run))
