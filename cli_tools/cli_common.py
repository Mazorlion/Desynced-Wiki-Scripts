from asyncio.log import logger
from dataclasses import dataclass
import logging
import os
from pathlib import Path
from typing import Awaitable, Callable

from cli_tools.resume import Resumable, ResumeHelper
from wiki.data_categories import CategoryHasPage, DataCategory, GetPagePrefix
from wiki.ratelimiter import limiter
from wiki.wiki_override import DesyncedWiki

logger = logging.getLogger()

# Function applied to each page.
# Should take (wiki, category, full_title: str, current_content: str) and return True if changes were made.
ApplyFuncType = Callable[[DesyncedWiki, str, str, str], Awaitable[bool]]


async def process_all_pages(
    wiki_output_path: Path,
    only_one_change: bool,
    resume_helper: ResumeHelper,
    applyFunc: ApplyFuncType,
):
    """Iterate on every non-data wiki page related to our data and apply given function"""

    wiki = DesyncedWiki()
    data_root_dir = Path(wiki_output_path / "Data")
    if not os.path.isdir(data_root_dir):
        logger.error(f"Data directory not found: {data_root_dir}")
        return

    @dataclass
    class ToProcess:
        category: DataCategory
        page: str

    to_process: list[Resumable] = []

    for category_dir in data_root_dir.iterdir():
        if not category_dir.is_dir():
            continue
        try:
            category = DataCategory(category_dir.name)
        except ValueError:
            logger.error(f"Unknown category directory: {category_dir.name}, skipping.")
            continue

        if not CategoryHasPage(category):
            continue

        for file_path in category_dir.iterdir():
            if not file_path.is_file():
                continue
            title = file_path.stem
            to_process.append(Resumable(title, ToProcess(category, title)))

    current_index = resume_helper.init_resume_index(to_process)

    for idx in range(current_index, len(to_process)):
        obj: ToProcess = to_process[idx].obj
        category = obj.category
        title = obj.page
        logger.debug(f"Checking page {title} ({category})")

        full_title = GetPagePrefix(category) + title
        existing_content = await limiter(wiki.page_text)(full_title)
        made_change = await applyFunc(wiki, category, full_title, existing_content)

        resume_helper.update_progress(title)

        if made_change and only_one_change:
            break
