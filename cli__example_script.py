# pylint: disable=unused-argument
# pylint: disable=unused-import
# (remove those when implementing)

import argparse
from typing import override
from cli_tools.common import CliTools, CliToolsOptions, PageMode
from wiki.data_categories import DataCategory
from util.ratelimiter import limiter
from util.logger import get_logger

logger = get_logger()


class ExampleScript(CliTools):
    # match_pattern: str

    @override
    def should_process_page(
        self,
        category: DataCategory,
        subpagename: str,
    ) -> bool:
        return True

    @override
    def add_args(self, parser: argparse.ArgumentParser):
        # parser.add_argument(
        #     "match_pattern",
        #     type=str,
        #     help="Regex match of files to remove",
        # )
        pass

    @override
    def process_args(self, args: argparse.Namespace):
        # self.match_pattern = args.match_pattern
        pass

    @override
    async def process_page(
        self,
        _: DataCategory,
        title: str,
        wiki_content: str | None,
        file_content: str | None,
    ) -> bool:
        if wiki_content:
            logger.info(f"with content: {wiki_content}")
            if self.args.apply:
                logger.info("Doing the thing")
                # await limiter(self.wiki.edit)(
                #     title=pagename,
                #     text="Batch delete from script",
                # )

        return False

    async def main(self):
        # Do whatever first

        # The optional main thing:
        # Calling process_all_pages will trigger process_page for each page found in the wiki output dir
        # Override should_process_page to control wheter a page needs to be processed

        await self.process_all_pages()

        # Do whatever after
        logger.info("I did all the things.")


if __name__ == "__main__":
    cli = ExampleScript(
        description="For all previously generated cargo data pages, remove the one regex-matching given param.",
        options=CliToolsOptions(page_mode=PageMode.DATA),
    )
    cli.run()
