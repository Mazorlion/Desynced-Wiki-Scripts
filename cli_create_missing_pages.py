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
        title: str,
        wiki_content: str | None,
        file_content: str | None,
    ) -> bool:
        if (
            not wiki_content
        ):  # seems an empty page returns empty string, rather than None as documented
            logger.info(f"Missing page: {title}")
            self.missing_pages.append((title))

            if self.args.apply:
                logger.info(f"Creating page {title}")
                await limiter(self.wiki.edit)(
                    title=title,
                    text=get_category_template(DataCategory(category)),
                )
                return True

        return False

    async def main(self):
        await self.process_all_pages()

        if self.missing_pages:
            logger.info("Found missing pages:")
            for title in self.missing_pages:
                print(f"- {title}")

            print(
                f"Condensed list:\n {','.join(title for title in self.missing_pages)}"
            )
        else:
            logger.info("No missing pages found.")


if __name__ == "__main__":
    cli = CreateMissingPages(
        description="For all previously generated cargo data pages, find if their the non-data counterpart exists."
    )
    cli.run()
