from collections import defaultdict
from dataclasses import dataclass
import os
from pathlib import Path
from typing import override
from cli_tools.common import CliTools, CliToolsOptions, PageMode
from util.ratelimiter import limiter
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
    def should_process_page(self, _: DataCategory, title: str) -> bool:
        return True

    @override
    async def process_page(
        self,
        category: DataCategory,
        wiki_page_path: str,
        wiki_content: str | None,
        file_content: str | None,
    ) -> bool:
        if not wiki_content or wiki_content != file_content:
            logger.info(f"Updating page {wiki_page_path}")
            self._updated_category_data.add(category)

            if self.args.apply:
                # Upload the file.
                await limiter(self.wiki.edit)(
                    title=wiki_page_path,
                    text=file_content,
                )
                return True

        return False

    async def update_templates(self):
        templates_root_dir: Path = self.args.output_directory / "Template"
        for root, _, files in os.walk(templates_root_dir):
            for file in files:
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    template_title = get_template_title(file)
                    page_title = get_template_page(template_title)
                    content: str = f.read()

                    # Upload the file.
                    wiki_content = await limiter(self.wiki.page_text)(page_title)

                    # Bail if there's no change.
                    if content == wiki_content:
                        continue

                    self._updated_category_templates.add(DataCategory(file))
                    logger.info(f"Updating {page_title} because content changed")
                    if not self.args.apply:
                        continue

                    await limiter(self.wiki.edit)(
                        title=page_title,
                        text=content,
                    )

    async def main(self):
        await self.update_templates()
        await self.process_all_pages()

        # Recreate cargo tables here.
        for category in self._updated_category_templates:
            table = category
            logger.info(f"Triggering recreating cargo TABLE for {table}")
            if not self.args.apply:
                continue

            assert await limiter(self.wiki.recreate_cargo_table)(
                table
            ), f"Failed to recreate table for {table}"

        # Recreate cargo data here.
        for category in self._updated_category_data:
            table = category
            template_title = get_template_title(category)
            logger.info(
                f"Triggering recreating cargo DATA for table {table} template {template_title}"
            )
            if not self.args.apply:
                continue

            assert await limiter(self.wiki.recreate_cargo_data)(
                template_title, table
            ), f"Failed to recreate data for {table}"

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


if __name__ == "__main__":
    cli = UploadWiki(
        description="For all previously generated cargo data pages, remove the one regex-matching given param.",
        options=CliToolsOptions(page_mode=PageMode.DATA),
    )
    cli.run()
