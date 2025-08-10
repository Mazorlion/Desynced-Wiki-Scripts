from collections import defaultdict
from dataclasses import dataclass
import os
from pathlib import Path
from typing import override

from cli_tools.common import CliTools, CliToolsOptions, PageMode, Page
from util.logger import get_logger
from wiki.data_categories import DataCategory
from wiki.titles import get_template_page, get_template_title

logger = get_logger()


@dataclass(frozen=True)
class CargoTable:
    template_title: str
    table: str


class UploadWiki(CliTools):
    _updated_category_templates: set[DataCategory] = set()
    _updated_category_data: set[DataCategory] = set()
    _updated_data_files: dict[DataCategory, list] = defaultdict(list)

    @override
    def process_page(
        self,
        category: DataCategory,
        title: str,
        page: Page,
        file_content: str,
    ) -> bool:
        if not page.text or page.text != file_content:
            logger.info(f"Updating page {title}")
            self._updated_category_data.add(category)

            if self.args.apply:
                page.text = file_content
                page.save()
                return True

        return False

    def update_templates(self):
        templates_root_dir: Path = self.args.output_directory / "Template"
        for root, _, files in os.walk(templates_root_dir):
            for file in files:
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    template_title = get_template_title(file)
                    page_title = get_template_page(template_title)
                    content: str = f.read()

                    # Upload the file.
                    page = self.wiki.page(page_title)

                    # Bail if there's no change.
                    if content == page.text:
                        continue

                    self._updated_category_templates.add(DataCategory(file))
                    logger.info(f"Updating {page_title} because content changed")
                    if not self.args.apply:
                        continue

                    page.text = content
                    page.save()

    def main(self):
        self.update_templates()
        self.process_all_pages()

        # Recreate cargo tables here.
        for category in self._updated_category_templates:
            table = category
            logger.info(f"Triggering recreating cargo TABLE for {table}")
            if not self.args.apply:
                continue

            assert self.wiki.recreate_cargo_table(
                table
            ), f"Failed to recreate table for {table}"

        # Should not be needed! Updating a page should automatically update the cargo table data related to it
        # # Recreate cargo data here.
        # for category in self._updated_category_data:
        #     table = category
        #     template_title = get_template_title(category)
        #     logger.info(
        #         f"Triggering recreating cargo DATA for table {table} template {template_title}"
        #     )
        #     if not self.args.apply:
        #         continue

        #     assert self.wiki.recreate_cargo_data(
        #         template_title, table
        #     ), f"Failed to recreate data for {table}"

        logger.info(f"Recreated tables: {self._updated_category_templates}")
        logger.info(f"Regenerated data for tables: {self._updated_category_data}")

        logger.info(f"Updated {len(self._updated_data_files)} data files:")

        logger.info(f"{'Category':<20} | {'Updated Files':>13}")
        logger.info("-" * 36)
        for category in sorted(self._updated_data_files):
            count = len(self._updated_data_files[category])
            logger.info(f"{category:<20} | {count:>13}")

        if not self.args.apply:
            logger.info("(Not applied, this is a dry run)")

        logger.info(
            "New tables/data might need to be swapped in at https://wiki.desyncedgame.com/Special:CargoTables manually.\n"
            "If it didn't work, delete the temporary table and try again."
        )


if __name__ == "__main__":
    cli = UploadWiki(
        description="For all previously generated cargo data pages, remove the one regex-matching given param.",
        options=CliToolsOptions(page_mode=PageMode.DATA),
    )
    cli.run()
