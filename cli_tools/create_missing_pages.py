import argparse
import asyncio
from dataclasses import dataclass
import logging
import os
import pprint
import sys

from cli_tools.cli_common import process_all_pages
from cli_tools.resume import Resumable, ResumeHelper
from wiki.data_categories import CategoryHasPage, DataCategory, GetPagePrefix
from wiki.page_template import GetCategoryTemplate

if __package__ is None or __package__ == "":
    current_file = os.path.basename(__file__)
    print(
        f"WARNING: This script is intended to be run as a module:\n"
        f"    python -m cli_tools.{current_file}\n"
        f"Running directly may cause import errors.",
        file=sys.stderr,
    )

from util.constants import DEFAULT_WIKI_OUTPUT_DIR
from util.logger import initLogger
from wiki.ratelimiter import limiter
from wiki.wiki_override import DesyncedWiki
from pathlib import Path


async def find_missing_pages(
    wiki_output_path: Path,
    create: bool,
    only_one_create: bool,
    resume_helper: ResumeHelper,
):
    """Loop through pages found from the output dir and print a list of the missing ones from the wiki."""

    missing_pages = []

    async def find_and_create_missing(
        wiki, category, full_title, existing_content
    ) -> bool:
        if (
            not existing_content
        ):  # seems an empty page returns empty string, rather than None as documented
            logger.info(f"Missing page: {full_title}")
            missing_pages.append((full_title))

            if create:
                logger.info(f"Creating page {full_title}")
                await limiter(wiki.edit)(
                    title=full_title,
                    text=GetCategoryTemplate(DataCategory(category)),
                )
                return True

        return False

    await process_all_pages(
        wiki_output_path, only_one_create, resume_helper, find_and_create_missing
    )

    if missing_pages:
        logger.info("Found missing pages:")
        for full_title in missing_pages:
            print(f"- {full_title}")

        print(
            f"Condensed list:\n {','.join(full_title for full_title in missing_pages)}"
        )

    else:
        logger.info("No missing pages found.")


if __name__ == "__main__":

    print(__package__)

    parser = argparse.ArgumentParser(
        description="For all previously generated cargo data pages, find if their the non-data counterpart exists.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--wiki-output-directory",
        type=str,
        help="Path to the directory containing the output wiki files for gamedata",
        default=DEFAULT_WIKI_OUTPUT_DIR,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output (sets logging level to DEBUG)",
        default=False,
    )
    parser.add_argument(
        "--resume-file",
        type=str,
        help="A temp file to store our progress and continue later",
        default=".missing_page_resume",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Force starting again, ignoring saved progress from resume file",
        default=False,
    )
    parser.add_argument(
        "--create",
        action="store_true",
        help="Enable creation of missing pages",
        default=False,
    )
    parser.add_argument(
        "--one",
        action="store_true",
        help="Stop after one create",
        default=False,
    )

    args = parser.parse_args()

    logger = initLogger(logging.DEBUG if args.debug else logging.INFO)
    logger.info(f"Running with args:\n{pprint.pformat(vars(args))}")

    wiki_output_path = Path(args.wiki_output_directory)
    resume_helper = ResumeHelper(Path(args.resume_file), args.restart)

    asyncio.run(
        find_missing_pages(wiki_output_path, args.create, args.one, resume_helper)
    )
