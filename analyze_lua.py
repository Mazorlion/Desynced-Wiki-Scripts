"""Reads game data from Desycned lua files and outputs corresponding wiki templates.

Evaluates the content of specific files in the game files. On game update, the `lua` library may require changes.

"""

import argparse
import logging
import sys
import os
from pathlib import Path
from lua.game_data import GameData
import lua.lua_util as lua_util
from models.entity import EntityType
from models.recipe import Recipe
from models.types import Race
from wiki.templater import (
    WikiTemplate,
    get_category,
    render_template,
)
from wiki.templates.data_models.category import (
    category_from_entity,
    category_from_item,
)
from wiki.wiki_constants import game_data_category
from wiki.wiki_util import only_include

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("analyze_lua.py")


def should_skip_recipe(recipe: Recipe) -> bool:
    """Attempts to heuristically detect if a recipe is "real" or not.

    Args:
        recipe (Recipe): Recipe to analyze.

    Returns:
        bool: True if the recipe should be excluded, False otherwise.
    """
    if recipe.race != None and recipe.race != Race.ROBOT:
        return True
    lower_name: str = recipe.name.lower()
    if lower_name in ["simulator"] or any(
        exclusion in lower_name
        for exclusion in [
            "virus",
            "artificial",
            "alien",
            "human",
            "trilobyte",
            "curious",
        ]
    ):
        return True
    for producer in recipe.producers:
        prod_name = producer.name.lower()
        if any(
            exclusion in prod_name for exclusion in ["human", "alien", "hive"]
        ):
            return True
    return False


def clean_output_dir(dir: str):
    """Recursively deletes all files in `dir`. Doesn't touch directories.

    Args:
        dir (str): Root directory to delete files in.
    """
    for root, dirs, files in os.walk(dir):
        for file in files:
            file_path: str = os.path.join(root, file)
            logger.debug(f"Deleting: {file_path}")
            os.remove(file_path)


def write_templates(
    args, objects, template: WikiTemplate, filter_function=None
):
    # Create the directory if it doesn't exist.
    category = get_category(template)
    dir = os.path.join(args.output_directory, category.replace(":", "/"))
    Path(dir).mkdir(parents=True, exist_ok=True)

    # Write each object to the correct file.
    for object in objects:
        if filter_function and filter_function(object):
            logger.debug(f"Skipping item: {object.name}")
            continue
        with open(os.path.join(dir, object.name), "w") as recipe_file:
            content: str = render_template(template, object)
            logger.debug(f"File: {object.name}. Content: {content}\n")
            if args.dry_run:
                logger.info(
                    f"Skipped writing {object.name} due to `--dry_run`."
                )
                continue
            recipe_file.write(content)


def main(args):
    game_data_directory = args.game_data_directory
    dry_run = args.dry_run
    output_directory = args.output_directory

    lua = lua_util.load_lua_runtime(game_data_directory)
    game = GameData(lua)

    # Delete outdated wiki files.
    Path(output_directory).mkdir(parents=True, exist_ok=True)
    if not dry_run:
        clean_output_dir(output_directory)

    write_templates(
        args,
        game.recipes,
        WikiTemplate.RECIPE,
        should_skip_recipe,
    )

    write_templates(
        args,
        game.recipes,
        WikiTemplate.RECIPE_PRODUCTION,
        should_skip_recipe,
    )

    write_templates(
        args,
        game.entities,
        WikiTemplate.ENTITY_STATS,
        lambda entity: EntityType.BUG in entity.types
        or (entity.race and entity.race != Race.ROBOT),
    )

    categories = list(map(category_from_entity, game.entities)) + list(
        map(category_from_item, game.items)
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--game-data-directory",
        type=str,
        help="Path to the directory containing the lua game data files.",
        default="game_data/main/data",
    )
    parser.add_argument(
        "--output-directory",
        type=str,
        help="Path to the directory containing the output wiki files for gamedata.",
        default="Output",
    )
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        help="If True, prevents any changes to the wiki. Default: True.",
        default="True",
    )

    args = parser.parse_args()
    main(args)
