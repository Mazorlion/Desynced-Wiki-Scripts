from typing import override
from cli_tools.common import CliTools, Page
from wiki.data_categories import DataCategory
from wiki.page_template import get_category_page_blueprint
from util.logger import get_logger


logger = get_logger()


class CreateMissingPages(CliTools):
    missing_pages = []

    @override
    def process_page(
        self,
        category: DataCategory,
        page: Page,
        _file_content: str,
    ) -> bool:
        if not page.exists():
            logger.info(f"Creating page: {page.title()}")
            self.missing_pages.append(page.title())

            if self.args.apply:
                page.text = get_category_page_blueprint(DataCategory(category))
                page.save()
                return True

        return False

    def main(self):
        self.process_all_pages()

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
