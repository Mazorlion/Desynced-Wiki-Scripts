import argparse
import asyncio
from asyncio.log import logger
from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Awaitable, Callable, final
from abc import ABC, abstractmethod

from cli_tools.resume import Resumable, ResumeHelper
from util.constants import DEFAULT_WIKI_OUTPUT_DIR
from util.logger import get_logger
from wiki.data_categories import CategoryHasPage, DataCategory, GetPagePrefix
from wiki.ratelimiter import limiter
from wiki.wiki_override import DesyncedWiki

logger = get_logger()

# Function applied to each page.
# Should take (wiki, category, full_title: str, current_content: str) and return True if changes were made.
apply_func_type = Callable[[DesyncedWiki, str, str, str], Awaitable[bool]]


@dataclass
class CliCommonArgs:
    """The shared arguments that will be passed to the specific cli tool implementation"""

    output_directory: Path
    resume_file: Path
    restart: bool
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
            "--restart",
            action="store_true",
            help="Force starting again, ignoring saved progress from resume file",
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
            restart=args.restart,
            apply=args.apply,
            only_one_change=args.one,
            only_categories=only_categories,
            debug=args.debug,
        )


class CliTools(ABC):
    """Common asbtract class for cli tools to inherit from"""

    cli_name: str
    args: CliCommonArgs
    resume: ResumeHelper
    wiki: DesyncedWiki

    def __init__(self, name: str, parser: argparse.ArgumentParser):
        self.cli_name = name
        CliToolsArgs.add_common_args(parser)
        self.add_args(parser)

        self.args = CliToolsArgs.process_common_args(parser.parse_args())
        self.resume = ResumeHelper(self.args.resume_file, self.args.restart)
        self.wiki = DesyncedWiki()

    def add_args(self, parser: argparse.ArgumentParser):  # type: ignore
        """(To override) Add command-specific command-line arguments to the parser."""
        logger.debug("Command did not add any specific args")

    def process_args(self, parser: argparse.ArgumentParser):  # type: ignore
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
        pass

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

            if not CategoryHasPage(category):
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
            logger.debug(f"Checking page {title} ({category})")

            full_title = GetPagePrefix(category) + title
            existing_content = await limiter(self.wiki.page_text)(full_title)
            made_change = await self.process_page(
                category, full_title, existing_content
            )

            self.resume.update_progress(title)

            if made_change and self.args.only_one_change:
                break
