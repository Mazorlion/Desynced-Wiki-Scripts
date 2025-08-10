from typing import override
from cli_tools.common import CliTools, Page
from wiki.data_categories import DataCategory
from wiki.page_template import (
    CATEGORY_PAGE_BLUEPRINT,
    TemplateName,
    extract_template_info,
    extract_templates_from_page,
    get_mandatory_templates,
    get_template_info,
)
from wiki.page_url import WikiUrl
from util.logger import get_logger


logger = get_logger()


def cut_template_to_arg_count(content: str, desired_count: int):
    read_pointer = 0
    content_length = len(content)
    current_arg_count = 0
    while read_pointer < content_length:
        arg_pos = content.find("|", read_pointer)
        if arg_pos == -1:
            break

        current_arg_count += 1
        if current_arg_count > desired_count:
            return content[0:arg_pos].strip()

        read_pointer += arg_pos

    return content


TEMPLATE_START = "{{"
TEMPLATE_END = "}}"


def replace_at_index(content: str, start_pos: int, old_content: str, new_content: str):
    return content[:start_pos] + content[start_pos:].replace(old_content, new_content)


def find_closing(content: str, start_pos: int) -> int:
    opened_count = 1
    read_pointer = start_pos
    next_close: None | int = None
    while opened_count > 0:
        next_open = content.find(TEMPLATE_START, read_pointer)
        next_close = content.find(TEMPLATE_END, read_pointer)
        if next_close == -1:
            raise ValueError(f"Wrong content? '{content}'")

        if next_open != -1 and next_open < next_close:
            read_pointer = next_open + len(TEMPLATE_START)
            opened_count += 1
        else:
            read_pointer = next_close + len(TEMPLATE_END)
            opened_count -= 1

    assert next_close is not None
    return next_close


def cleanup_extra_arguments(content: str, title: str) -> str:
    """Try to remove extra arguments from template when there are too many
    Mostly using logic from extract_templates_info_from_page"""

    read_pointer = 0

    while read_pointer < len(content):
        # Find the next template start
        start_pos = content.find(TEMPLATE_START, read_pointer)
        if start_pos == -1:
            break

        start_pos += len(TEMPLATE_START)

        # Find the corresponding template end
        end_pos = find_closing(content, start_pos)
        if end_pos == -1:
            break

        # Extract the template content
        template_content = content[start_pos:end_pos]

        # Process nested templates recursively
        cleaned_content = cleanup_extra_arguments(template_content, title)
        if cleaned_content != template_content:
            content = replace_at_index(
                content, start_pos, template_content, cleaned_content
            )
            # we replaced some content, start again without advancing reading pointer
            continue

        # Extract the main template name
        used_template = extract_template_info(template_content)
        if used_template:
            used_name = used_template[0]
            used_info = used_template[1]
            if expected_info := get_template_info(used_name):
                if used_info.arg_count < expected_info.arg_count:
                    logger.error(
                        f"Page {title} has template {used_name} with fewer args can expected, this needs manual fixing"
                    )
                elif used_info.arg_count > expected_info.max_arg_count:
                    # Then we have too many args and we can try to remove some
                    cleaned_template = cut_template_to_arg_count(
                        template_content, expected_info.max_arg_count
                    )
                    content = replace_at_index(
                        content, start_pos, template_content, cleaned_template
                    )
                    continue

        # Move the read pointer past this template
        read_pointer = end_pos + len(TEMPLATE_END)

    return content


SWAP_TEMPLATES: dict[DataCategory, dict[TemplateName, TemplateName]] = {
    DataCategory.instruction: {"Infobox": "Instruction_Top"}
}


def swap_templates(category, content, title) -> str:
    """Batch replace old template names with new ones"""
    if swaps := SWAP_TEMPLATES.get(category):
        for old, new in swaps.items():
            if content.find(old):
                content = content.replace(old, new)
                logger.info(
                    f"Page '{title}' has old template '{old}', replacing with '{new}' -> {WikiUrl.get_page_history(title)}"
                )

    return content


def find_missing_templates(category, content) -> list[TemplateName]:
    """List here all mandatory templates for category that are not used in content"""

    if mandatory := get_mandatory_templates(category):
        used = extract_templates_from_page(content)
        missing = [name for name in mandatory if name not in used]

        return missing

    return []


def test_category_templates_consistency():
    for cat, content in CATEGORY_PAGE_BLUEPRINT.items():
        if missing := find_missing_templates(cat, content):
            raise ValueError(
                f"Category {cat} default template does not fit rules from find_missing_templates, missing: {missing}"
            )


class CleanupPageTemplates(CliTools):
    _update_pages = []

    @override
    def process_page(
        self,
        category: DataCategory,
        title: str,
        page: Page,
        file_content: str,
    ) -> bool:
        if not page.text:
            logger.error(f"Page '{title}' did not exists -> {WikiUrl.get_page(title)}")
            return False

        updated_content = swap_templates(category, page.text, title)
        updated_content = cleanup_extra_arguments(updated_content, title)
        # -> Extra cleanup checks go here <-

        missing_templates = find_missing_templates(category, updated_content)
        if missing_templates:
            missing_str = ",".join(title for title in missing_templates)
            logger.warning(
                f"Page '{title}' is missing some templates: '{missing_str}' -> {WikiUrl.get_page(title)}"
            )

        if updated_content != page.text:
            logger.info(
                f"Updating content for page: '{title}' -> {WikiUrl.get_page_history(title)}"
            )
            self._update_pages.append((title))

            if self.args.apply:
                page.text = updated_content
                page.save()
                return True

        return False

    def main(self):
        test_category_templates_consistency()
        self.process_all_pages()

        if self._update_pages:
            logger.info("Updated pages:")
            for title in self._update_pages:
                print(f"- {title} -> {WikiUrl.get_page_history(title)}")
        else:
            logger.info("No pages were updated.")


if __name__ == "__main__":
    cli = CleanupPageTemplates(
        description="Cleanup page templates, checking for missing templates for given category or wrong arg count."
    )
    cli.run()
