import argparse
from typing import override
from cli_tools.common import CliTools, PageMode
from wiki.data_categories import DataCategory
from wiki.ratelimiter import limiter  # pylint: disable=unused-import
from util.logger import get_logger

logger = get_logger()


class ExampleScript(CliTools):
    # match_pattern: str

    @override
    def should_process_page(self, _: DataCategory, title: str) -> bool:
        return True

    @override
    def add_args(
        self, parser: argparse.ArgumentParser  # pylint: disable=unused-argument
    ):
        # parser.add_argument(
        #     "match_pattern",
        #     type=str,
        #     help="Regex match of files to remove",
        # )
        pass

    @override
    def process_args(self, args: argparse.Namespace):  # pylint: disable=unused-argument
        # self.match_pattern = args.match_pattern
        pass

    @override
    async def process_page(
        self,
        _: DataCategory,
        full_title: str,
        existing_content: str | None,
    ) -> bool:
        logger.info(f"Processing page: {full_title}")
        if existing_content:
            logger.info(f"with content: {existing_content}")
            if self.args.apply:
                logger.info("Doing the thing")
                # await limiter(self.wiki.edit)(
                #     title=full_title,
                #     text="Batch delete from script",
                # )

        return False

    async def main(self):
        # Do whatever

        await self.process_all_pages()

        logger.info("I did all the things.")


if __name__ == "__main__":
    cli = ExampleScript(
        description="For all previously generated cargo data pages, remove the one regex-matching given param.",
        page_mode=PageMode.DATA,
    )
    cli.run()
