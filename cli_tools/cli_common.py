import argparse
import asyncio
from asyncio.log import logger
from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import final
from abc import ABC, abstractmethod

from cli_tools.resume import Resumable, ResumeHelper
from util.constants import DEFAULT_WIKI_OUTPUT_DIR
from util.logger import get_logger
from wiki.data_categories import category_has_page, DataCategory, get_page_prefix
from wiki.ratelimiter import limiter
from wiki.wiki_override import DesyncedWiki

logger = get_logger()


@dataclass
class CliCommonArgs:
    """The shared arguments that will be passed to the specific cli tool implementation"""

    output_directory: Path
    resume_file: Path
    resume: bool
    apply: bool
    only_one_change: bool
    only_categories: list[DataCategory]
    debug: bool


class CliToolsArgs:
    """All the stuff about the input args"""

    @staticmethod
    def add_common_args(parser: argparse.ArgumentParser):
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
            "--resume",
            action="store_true",
            help="If true, will try to resume progress",
            default=False,
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually do the changes",
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

    @staticmethod
    def process_common_args(args) -> CliCommonArgs:
        """Transform parsed args in"""
        # howto? logger = get_logger(logging.DEBUG if parsed_args.debug else logging.INFO)
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

        return CliCommonArgs(
            Path(args.wiki_output_directory),
            Path(args.resume_file),
            resume=args.resume,
            apply=args.apply,
            only_one_change=args.one,
            only_categories=only_categories,
            debug=args.debug,
        )


class CliTools(ABC):
    """Common asbtract class for cli tools to inherit from"""

    parser: argparse.ArgumentParser
    args: CliCommonArgs
    resume: ResumeHelper
    wiki: DesyncedWiki

    def __init__(self, description: str):
        self.parser = argparse.ArgumentParser(
            description=description,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        CliToolsArgs.add_common_args(self.parser)
        self.add_args(self.parser)

        self.args = CliToolsArgs.process_common_args(self.parser.parse_args())
        self.resume = ResumeHelper(self.args.resume_file, self.args.resume)
        self.wiki = DesyncedWiki()

    def add_args(
        self, parser: argparse.ArgumentParser  # pylint: disable=unused-argument
    ):
        """(To override) Add command-specific command-line arguments to the parser."""
        logger.debug("Command did not add any specific args")

    def process_args(
        self, parser: argparse.ArgumentParser  # pylint: disable=unused-argument
    ):
        """(To override) Process command-specific command-line arguments to the parser."""

    @abstractmethod
    async def process_page(
        self,
        category: DataCategory,
        full_title: str,
        existing_content: str | None,
    ) -> bool:
        """(To override) Defines how to process one page. Must returns true if a change was made."""
        return False

    @abstractmethod
    async def main(self):
        """Your main method, to implement"""

    @final
    def run(self):
        logger.setLevel(logging.DEBUG if self.args.debug else logging.INFO)
        asyncio.run(self.main())

    @final
    async def process_all_pages(self):
        """Helper to iterate on every non-data wiki page related to our data and apply given function"""

        data_root_dir: Path = self.args.output_directory / "Data"
        if not os.path.isdir(data_root_dir):
            logger.error(f"Data directory not found: {data_root_dir}")
            return

        @dataclass
        class ToProcess:
            category: DataCategory
            page: str

        to_process: list[Resumable] = []

        for category_dir in data_root_dir.iterdir():
            if not category_dir.is_dir():
                continue
            try:
                category = DataCategory(category_dir.name)
            except ValueError as e:
                logger.error(
                    f"Unknown category directory: {category_dir.name}, skipping."
                )
                raise e

            if self.args.only_categories and category not in self.args.only_categories:
                continue

            if not category_has_page(category):
                continue

            for file_path in category_dir.iterdir():
                if not file_path.is_file():
                    continue
                title = file_path.stem
                to_process.append(Resumable(title, ToProcess(category, title)))

        current_index = self.resume.init_resume_index(to_process)

        for idx in range(current_index, len(to_process)):
            obj: ToProcess = to_process[idx].obj
            category = obj.category
            title = obj.page
            logger.debug(f"Processing page {title} ({category})")

            full_title = get_page_prefix(category) + title
            existing_content = await limiter(self.wiki.page_text)(full_title)
            made_change = await self.process_page(
                category, full_title, existing_content
            )

            self.resume.update_progress(title)

            if made_change and self.args.only_one_change:
                break
