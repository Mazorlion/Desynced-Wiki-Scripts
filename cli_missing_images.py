import argparse
from pathlib import Path
import re
from typing import override
from pywikibot import FilePage
from pywikibot.exceptions import APIError
from cli_tools.common import CliTools, CliToolsOptions, PageMode, Page
from lua import lua_util
from lua.game_data import GameData
from util.logger import get_logger
from util.constants import FETCHED_GAME_DATA_DIR
from wiki.data_categories import DataCategory
from wiki.page_template import page_has_template
from wiki.titles import get_sub_pagename

logger = get_logger()


class MissingImages(CliTools):
    _game_data_directory: Path

    @override
    def should_process_page(
        self,
        category: DataCategory,
        _page: Page,
    ) -> bool:
        return category in [
            DataCategory.entity,
            DataCategory.item,
            DataCategory.component,
            DataCategory.tech,  # removed for now: those have some texture field extracted in the model, it might need different handling
        ]

    @override
    def process_page(
        self,
        category: DataCategory,
        page: Page,
        file_content: str,
    ) -> bool:
        # We process only pages having an infobox as a shortcut to whatever has missing images. Infobox has a fixed image format.
        if page.exists() and page_has_template(page.text, "Infobox"):

            image_page = self.wiki.filepage(
                f"File:{get_sub_pagename(page.title())}.png"
            )
            logger.debug(f"Checking image: {image_page.title()}")

            # this does not actually check if there is an image on the file page
            if not image_page.exists():
                logger.info(f"Image: {image_page.title()} is missing.")
                return self.handle_missing_image(
                    category, page, file_content, image_page
                )

        return False

    @staticmethod
    def get_lua_id(page_title: str, file_content: str) -> str:
        # Search for the luaId parameter within the params block
        luaid_match = re.search(r"\|\s*luaId\s*=\s*([^\|\n\r]+)", file_content)
        if luaid_match:
            return luaid_match.group(1).strip()

        raise ValueError(
            f"Could not find lua ID (from locally extracted files) for object {page_title}"
        )

    def get_texture_file_path(self, category: DataCategory, lua_id: str) -> str | None:
        data = self.game_data.lua.globals().data  # type: ignore

        if category == DataCategory.component:
            search_table = data.components
        elif category == DataCategory.item:
            search_table = data["items"]
        elif category == DataCategory.entity:
            search_table = data.frames
        elif category == DataCategory.tech:
            search_table = data.techs
        else:
            raise ValueError(f"Invalid category {category}")

        for obj_id, obj in search_table.items():
            if obj_id == lua_id:
                return obj.texture

        return None

    def get_valid_image_path(self, game_texture_path: str) -> None | Path:
        """
        Returns actual existing file path on disk

        Parameters
        ----------
        arg1 : texture_path
            As declared in the game object, like "Main/textures/tech/alien_tech.png"
        """
        prefix = "Main/"
        if game_texture_path.startswith(prefix):
            cleaned_texture_path = game_texture_path[len(prefix) :]
        else:
            logger.error(
                f'Texture path {game_texture_path} does not start with "{prefix}"'
            )
            return None

        file_path = Path(self._game_data_directory) / cleaned_texture_path
        if not file_path.exists() or file_path.is_dir():
            logger.error("Image file {file_path} does not exists")
            return None

        return file_path

    def extract_redirect_target(self, error_msg: str) -> str | None:
        match = re.search(r"\['([^']+)'.*\]", error_msg)
        return match.group(1) if match else None

    def handle_missing_image(
        self,
        category: DataCategory,
        page: Page,
        file_content: str,
        image_page: FilePage,
    ) -> bool:
        """Return if changes were made"""
        lua_id = self.get_lua_id(page.title(), file_content)

        game_texture_path = self.get_texture_file_path(category, lua_id)
        if not game_texture_path:
            logger.error(
                f"Could not find any texture for object {lua_id} (Page '{page.title()}')"
            )
            return False

        file_path = self.get_valid_image_path(game_texture_path)
        if not file_path:
            # error log already handled
            return False

        logger.info(
            f"Uploading image {file_path} to {image_page.title()}, for page {page.title()}"
        )
        if not self.args.apply:
            return True

        ignored_codes = ["was-deleted", "duplicate-archive"]

        # code adapted from https://github.com/wikimedia/pywikibot/blob/master/pywikibot/specialbots/_upload.py#L26
        redirect_to: str | None = None
        retry_ignore_warnings = False  # upload documentation say we can provide a list but it seems out of date and it's always treated as a bool
        while True:
            try:
                if redirect_to:
                    image_page.text = f"#REDIRECT [[File:{redirect_to}]]"
                    image_page.save()
                    success = True
                else:
                    success = image_page.upload(
                        str(file_path),
                        comment="Auto imported from script",
                        ignore_warnings=retry_ignore_warnings,
                        report_success=True,
                    )
                    image_page.save()
                redirect_to = None
                retry_ignore_warnings = False
            except APIError as error:
                if error.code == "uploaddisabled":
                    logger.error(
                        "Upload error: Local file uploads are disabled on wiki."
                    )
                    raise error
                elif error.code in ignored_codes:
                    logger.debug(f"Encountered code {error.code}, retrying...")
                    retry_ignore_warnings = True
                    continue
                elif error.code == "duplicate":
                    if redirect_to := self.extract_redirect_target(error.unicode):
                        logger.info(
                            f"Wiki reports the image we're trying to upload as duplicate of {redirect_to}. Creating a redirect to it."
                        )
                        continue
                    else:
                        logger.exception("Upload error: ")
                else:
                    logger.exception("Upload error: ")
                    answer = (
                        input(
                            "Do you want to retry, ignoring this warning for the rest of the execution? Else, file is skipped. (y/n) "
                        )
                        .strip()
                        .lower()
                    )
                    if answer == "y":
                        ignored_codes.append(error.code)
                        continue

            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception("Upload error: ")

            if success:
                # No warning, upload complete.
                logger.info(
                    f"Upload of {image_page.full_url()} successful. Object page: {page.full_url()}"
                )
            else:
                logger.info("Upload aborted.")

            break

        return True

    @override
    def add_args(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            "game_data_directory",
            nargs="?",
            type=str,
            help="Path to the directory containing the lua game data files (= root of main mod)",
            default=FETCHED_GAME_DATA_DIR,
        )

    @override
    def process_args(self, args: argparse.Namespace):
        self._game_data_directory = Path(args.game_data_directory)

    _game_data: GameData | None = None

    @property
    def game_data(self) -> GameData:
        if not self._game_data:
            lua = lua_util.load_lua_runtime(self._game_data_directory)
            self._game_data = GameData(lua)

        return self._game_data

    def main(self):
        self.process_all_pages()


if __name__ == "__main__":
    cli = MissingImages(
        description="Try to find missing images & upload them. Doesn't check mismatched images. Script might prompt you in some error cases",
        options=CliToolsOptions(page_mode=PageMode.HUMAN),
    )
    cli.run()
