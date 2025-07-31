import argparse
import os
import sys

from cli_tools.cli_common import CliTools
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

from util.logger import get_logger
from wiki.ratelimiter import limiter


class CreateMissingPages(CliTools):
    missing_pages = []

    async def process_page(
        self,
        category: DataCategory,
        full_title: str,
        existing_content: str | None,
    ) -> bool:
        if (
            not existing_content
        ):  # seems an empty page returns empty string, rather than None as documented
            logger.info(f"Missing page: {full_title}")
            self.missing_pages.append((full_title))

            if self.args.apply:
                logger.info(f"Creating page {full_title}")
                await limiter(self.wiki.edit)(
                    title=full_title,
                    text=GetCategoryTemplate(DataCategory(category)),
                )
                return True

        return False

    async def main(self):
        await self.process_all_pages()

        if self.missing_pages:
            logger.info("Found missing pages:")
            for full_title in self.missing_pages:
                print(f"- {full_title}")

            print(
                f"Condensed list:\n {','.join(full_title for full_title in self.missing_pages)}"
            )
        else:
            logger.info("No missing pages found.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="For all previously generated cargo data pages, find if their the non-data counterpart exists.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    cli = CreateMissingPages("Create Missing Pages", parser)
    cli.run()


logger = get_logger()
