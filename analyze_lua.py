"""Reads game data from Desycned lua files and outputs corresponding wiki templates.

Evaluates the content of specific files in the game files. On game update, the `lua` library may require changes.

"""

import argparse
import logging
import sys
import os
from lua.game_data import GameData
import lua.lua_util as lua_util
from wiki.wiki_constants import game_data_category
from wiki.wiki_util import only_include

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("analyze_lua.py")


def clean_wiki_dir(dir: str):
    """Recursively deletes all files in `dir`. Doesn't touch directories.

    Args:
        dir (str): Root directory to delete files in.
    """
    for root, dirs, files in os.walk(dir):
        for file in files:
            file_path: str = os.path.join(root, file)
            logger.debug(f"Deleting: {file_path}")
            os.remove(file_path)


def main(game_data_directory: str, recipe_directory: str, dry_run: bool):
    lua = lua_util.load_lua_runtime(game_data_directory)
    game = GameData(lua)

    # Delete outdated wiki files.
    if not dry_run:
        clean_wiki_dir(recipe_directory)

    # Create a file in `recipe_directory` for each parsed recipe.
    for recipe in game.recipes:
        # TODO(Maz): Remove this once there are better heuristics for "real" recipes.
        if (
            recipe.race != "robot"
            or recipe.is_derived
            or "virus" in recipe.name.lower()
            or "artificial" in recipe.name.lower()
        ):
            continue
        with open(
            os.path.join(recipe_directory, recipe.name), "w"
        ) as recipe_file:
            content: str = game_data_category + only_include(
                recipe.template_str
            )
            logger.debug(f"File: {recipe.name}. Content: {content}\n")
            if dry_run:
                logger.info(
                    f"Skipped writing {recipe.name} due to `--dry_run`."
                )
                continue
            recipe_file.write(content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--game_data_directory",
        type=str,
        help="Path to the directory containing the lua game data files.",
        default="game_data/main/data",
    )
    parser.add_argument(
        "--recipe-directory",
        type=str,
        help="Path to the directory containing wiki files for gamedata recipes.",
        default="wiki/GameData/Recipe",
    )
    parser.add_argument(
        "--dry_run",
        action=argparse.BooleanOptionalAction,
        help="If True, prevents any changes to the wiki. Default: True.",
        default="True",
    )

    args = parser.parse_args()
    main(args.game_data_directory, args.recipe_directory, args.dry_run)
