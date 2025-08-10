from typing import override
from cli_tools.common import CliTools
from wiki.data_categories import DataCategory
from wiki.page_template import get_category_template
from util.ratelimiter import limiter
from util.logger import get_logger


logger = get_logger()


class CreateMissingPages(CliTools):
    missing_pages = []

    @override
    async def process_page(
        self,
        category: DataCategory,
        wiki_page_path: str,
        wiki_content: str | None,
        file_content: str | None,
    ) -> bool:
        if (
            not wiki_content
        ):  # seems an empty page returns empty string, rather than None as documented
            logger.info(f"Missing page: {wiki_page_path}")
            self.missing_pages.append((wiki_page_path))

            if self.args.apply:
                logger.info(f"Creating page {wiki_page_path}")
                await limiter(self.wiki.edit)(
                    title=wiki_page_path,
                    text=get_category_template(DataCategory(category)),
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
    cli = CreateMissingPages(
        description="For all previously generated cargo data pages, find if their the non-data counterpart exists."
    )
    cli.run()
