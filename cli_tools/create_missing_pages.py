import argparse
import asyncio
import logging
import os
import pprint
import sys

from cli_tools.cli_common import CliTools
from cli_tools.resume import ResumeHelper
from wiki.data_categories import DataCategory
from wiki.page_template import GetCategoryTemplate

if __name__ != "__main__":
    raise RuntimeError(
        "This script is intended to be executed as a module, not imported."
    )

if __package__ is None or __package__ == "":
    current_file = os.path.basename(__file__)
    print(
        f"WARNING: This script is intended to be run as a module:\n"
        f"    python -m cli_tools.{current_file}\n"
        f"Running directly may cause import errors.",
        file=sys.stderr,
    )

from util.constants import DEFAULT_WIKI_OUTPUT_DIR
from util.logger import get_logger
from wiki.ratelimiter import limiter
from pathlib import Path


async def find_missing_pages(
    wiki_output_path: Path,
    create: bool,
    only_one_create: bool,
    only_categories: list[DataCategory],
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

    await CliTools().process_all_pages(
        wiki_output_path,
        only_one_create,
        resume_helper,
        only_categories,
        find_and_create_missing,
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


def main(args):
    logger.info(f"Running with args:\n{pprint.pformat(vars(args))}")

    wiki_output_path = Path(args.wiki_output_directory)
    resume_helper = ResumeHelper(Path(args.resume_file), args.restart)

    try:
        only_categories = [
            DataCategory[name.strip()]
            for name in (
                args.only_categories.split(",") if args.only_categories else []
            )
        ]
    except KeyError as e:
        logger.error(f"Invalid category name in {args.only_categories}")
        raise e

    asyncio.run(
        find_missing_pages(
            wiki_output_path, args.create, args.one, only_categories, resume_helper
        )
    )


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
    data_categories = {e.value for e in DataCategory}
    parser.add_argument(
        "--only-categories",
        type=str,
        help=f"If set, only produces data for categories specified. Comma separated list. Possible values: {data_categories}",
    )

    args = parser.parse_args()
    logger = get_logger(logging.DEBUG if args.debug else logging.INFO)
    main(args)
else:
    logger = get_logger()
