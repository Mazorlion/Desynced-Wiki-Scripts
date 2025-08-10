import argparse
import re
from typing import override
from cli_tools.common import CliTools, CliToolsOptions, PageMode, Page
from wiki.data_categories import DataCategory
from util.logger import get_logger


logger = get_logger()


class RemoveDataPages(CliTools):
    _match_pattern: str

    _to_remove: list[Page] = []

    @override
    def should_process_page(self, _category: DataCategory, page: Page) -> bool:
        title = page.title()
        matched = bool(re.search(self._match_pattern, title))
        if matched:
            logger.debug(f"Page {title} did match filter")
        else:
            logger.debug(f"Page {title} did not match filter")

        return matched

    @override
    def add_args(
        self, parser: argparse.ArgumentParser  # pylint: disable=unused-argument
    ):
        parser.add_argument(
            "match_pattern",
            type=str,
            help="Regex match of files to remove",
        )

    @override
    def process_args(self, args: argparse.Namespace):
        self._match_pattern = args.match_pattern

    @override
    def process_page(
        self,
        _category: DataCategory,
        page: Page,
        _file_content: str,
    ) -> bool:
        # seems an empty page returns empty string, rather than None as documented
        if page.exists():
            logger.info(f"Add page to remove: {page.title()}")
            self._to_remove.append(page)

        return False

    def main(self):
        self.process_all_pages()

        if self._to_remove:
            logger.info("Pages to remove:")
            for page in self._to_remove:
                print(f"- {page.title}")
        else:
            logger.info("No pages removed.")

        if self.args.apply:
            for page in self._to_remove:
                logger.info(f"Removing page {page.title}")
                page.delete(f"Scripted batch remove from {__class__}")


if __name__ == "__main__":
    cli = RemoveDataPages(
        description="For all currently existing generated cargo data pages, remove the ones with wiki title regex-matching given param.",
        options=CliToolsOptions(page_mode=PageMode.DATA),
    )
    cli.run()
