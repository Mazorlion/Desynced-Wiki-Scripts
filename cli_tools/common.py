import argparse
import asyncio
from asyncio.log import logger
from dataclasses import dataclass, field
from enum import Flag, auto
import logging
import os
from pathlib import Path
from typing import final
from abc import ABC, abstractmethod

from cli_tools.resume import Resumable, ResumeHelper
from util.constants import DEFAULT_WIKI_OUTPUT_DIR
from util.logger import get_logger
from util.ratelimiter import limiter
from wiki.data_categories import (
    category_has_human_pages,
    DataCategory,
)
from wiki.titles import get_data_page_title, get_human_page_title
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
            default=".resume",
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


class PageMode(Flag):
    HUMAN = auto()
    DATA = auto()


@dataclass
class CliToolsOptions:
    page_mode: PageMode = PageMode.HUMAN


@dataclass
class CliTools(ABC):
    """Common asbtract class for cli tools to inherit from

    This class mainly provides:
    - Common cli arguments
    - A standard way to process each file found in the wiki output directory

    See cli__example_script.py for an example usage.
    """

    description: str
    options: CliToolsOptions = field(default_factory=CliToolsOptions)

    parser: argparse.ArgumentParser = field(init=False)  # excluded from __init__
    args: CliCommonArgs = field(init=False)  # excluded from __init__
    resume: ResumeHelper = field(init=False)  # excluded from __init__
    wiki: DesyncedWiki = field(init=False)  # excluded from __init__

    def __post_init__(self):
        self.parser = argparse.ArgumentParser(
            description=self.description,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

        CliToolsArgs.add_common_args(self.parser)
        self.add_args(self.parser)

        parsed_args = self.parser.parse_args()
        self.args = CliToolsArgs.process_common_args(parsed_args)
        logger.setLevel(logging.DEBUG if self.args.debug else logging.INFO)
        self.process_args(parsed_args)
        self.resume = ResumeHelper(self.args.resume_file, self.args.resume)
        self.wiki = DesyncedWiki()

    def add_args(
        self, parser: argparse.ArgumentParser  # pylint: disable=unused-argument
    ):
        """(To override) Add tool-specific command-line arguments to the parser."""
        logger.debug("Command did not add any specific args")

    def process_args(self, args: argparse.Namespace):  # pylint: disable=unused-argument
        """(To override) Process tool-specific command-line arguments to the parser."""

    def should_process_page(
        self,
        category: DataCategory,  # pylint: disable=unused-argument
        subpagename: str,  # pylint: disable=unused-argument
    ) -> bool:
        """Should given page be processed by process_all_pages?"""
        return True

    @abstractmethod
    async def process_page(
        self,
        category: DataCategory,
        title: str,
        wiki_content: str | None,
        file_content: str | None,
    ) -> bool:
        """(To override) Defines how to process one page. Must returns true if a change was made."""
        return False

    @abstractmethod
    async def main(self):
        """Your main method, to implement"""

    @final
    def run(self):
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
            title: str
            path: Path

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

            for file_path in category_dir.iterdir():
                if not file_path.is_file():
                    continue

                subpagename = file_path.stem
                if not self.should_process_page(category, subpagename):
                    continue

                if (
                    category_has_human_pages(category)
                    and self.options.page_mode & PageMode.HUMAN
                ):
                    title = get_human_page_title(category, subpagename)
                    to_process.append(
                        Resumable(title, ToProcess(category, title, file_path))
                    )

                if self.options.page_mode & PageMode.DATA:
                    data_title = get_data_page_title(category, subpagename)
                    to_process.append(
                        Resumable(
                            data_title, ToProcess(category, data_title, file_path)
                        )
                    )

        current_index = (
            self.resume.init_resume_index(to_process) if self.args.resume else 0
        )

        for idx in range(current_index, len(to_process)):
            obj: ToProcess = to_process[idx].obj

            logger.debug(f"Processing page {obj.title} ({obj.category})")

            wiki_content = await limiter(self.wiki.page_text)(obj.title)
            made_change = await self.process_page(
                category, obj.title, wiki_content, obj.path.read_text()
            )

            self.resume.update_progress(subpagename)

            if made_change and self.args.only_one_change:
                break
