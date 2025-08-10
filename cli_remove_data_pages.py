import argparse
import re
from typing import override
from cli_tools.common import CliTools, CliToolsOptions, PageMode
from wiki.data_categories import DataCategory
from util.ratelimiter import limiter
from util.logger import get_logger


logger = get_logger()


class RemoveDataPages(CliTools):
    _match_pattern: str

    _to_remove = []

    @override
    def should_process_page(self, _: DataCategory, title: str) -> bool:
        matched = bool(re.search(self._match_pattern, title))
        if matched:
            logger.debug(f"Page {title} did match filter")
        else:
            logger.debug(f"Page {title} did not match filter")

        return bool(re.search(self._match_pattern, title))

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
    async def process_page(
        self,
        _: DataCategory,
        wiki_page_path: str,
        wiki_content: str | None,
        file_content: str | None,
    ) -> bool:
        # seems an empty page returns empty string, rather than None as documented
        if wiki_content:
            logger.info(f"Add page to remove: {wiki_page_path}")
            self._to_remove.append((wiki_page_path))

        return False

    async def main(self):
        await self.process_all_pages()

        if self._to_remove:
            logger.info("Pages to remove:")
            for full_title in self._to_remove:
                print(f"- {full_title}")
        else:
            logger.info("No pages removed.")

        if self.args.apply:
            for to_remove in self._to_remove:
                logger.info(f"Removing page {to_remove}")
                await limiter(self.wiki.delete)(
                    title=to_remove,
                    text="Batch delete from script",
                )


if __name__ == "__main__":
    cli = RemoveDataPages(
        description="For all previously generated cargo data pages, remove the one regex-matching given param.",
        options=CliToolsOptions(page_mode=PageMode.DATA),
    )
    cli.run()
