from cli_tools.cli_common import CliTools
from wiki.data_categories import DataCategory
from wiki.page_template import get_category_template
from wiki.ratelimiter import limiter
from util.logger import get_logger


logger = get_logger()


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
