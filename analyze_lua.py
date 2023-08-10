"""Reads game data from Desycned lua files and outputs corresponding wiki templates.

Evaluates the content of specific files in the game files.
On game update, the `lua` library may require changes.

"""

import argparse
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Type

import lua.lua_util as lua_util
from lua.game_data import GameData
from models.component import Component
from models.entity import Entity
from models.instructions import Instruction
from models.item import Item
from models.recipe import Recipe
from models.tech import Technology, TechnologyCategory, TechnologyUnlock
from wiki.cargo.analyze_type import analyze_type
from wiki.cargo.cargo_printer import CargoPrinter
from wiki.templates.templater import WikiTemplate, render_template

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger("analyze_lua.py")


def should_skip_name(name: str):
    if not name:
        return True

    lower_name = name.lower()
    if lower_name in ["simulator"] or any(
        exclusion in lower_name
        for exclusion in [
            "artificial",
            "alien",
            "human",
            "curious",
            "attack",
            "c_",
            "spawner",
            "hive",
            "consume",
        ]
    ):
        return True
    return False


def should_skip(desynced_object: Any) -> bool:
    """Attempts to heuristically detect if a recipe is "real" or not.

    Args:
        recipe (Recipe): Recipe to analyze.

    Returns:
        bool: True if the recipe should be excluded, False otherwise.
    """
    if should_skip_name(desynced_object.name):
        return True

    if hasattr(desynced_object, "recipe") and desynced_object.recipe:
        recipe: Recipe = desynced_object.recipe

        for item in recipe.items:
            if should_skip_name(item.ingredient):
                return True
        for producer in recipe.producers:
            if should_skip_name(producer.producer):
                return True

    if (
        hasattr(desynced_object, "production_recipe")
        and desynced_object.production_recipe
    ):
        recipe: Recipe = desynced_object.production_recipe
        for item in recipe.items:
            if should_skip_name(item.ingredient):
                return True
        for producer in recipe.producers:
            if should_skip_name(producer.producer):
                return True

    return False


def clean_output_dir(output_dir: str):
    """Recursively deletes all files in `dir`. Doesn't touch directories.

    Args:
        dir (str): Root directory to delete files in.
    """
    for root, _, files in os.walk(output_dir):
        for file in files:
            file_path: str = os.path.join(root, file)
            logger.debug(f"Deleting: {file_path}")
            os.remove(file_path)


def write_declaration(output_dir: str, table_name: str, template_type: Type):
    template_dir: str = os.path.join(output_dir, "Template")
    Path(template_dir).mkdir(parents=True, exist_ok=True)
    with open(
        os.path.join(template_dir, f"{table_name}"), "w", encoding="utf-8"
    ) as tabledef_file:
        content: str = render_template(
            WikiTemplate.CARGO_DECLARE,
            {
                "table_name": table_name,
                "declare_args": "\n".join(
                    CargoPrinter(CargoPrinter.Mode.DECLARATIONS).print_dataclass(
                        dc_obj=None, type_info=analyze_type(template_type)
                    )
                ),
                "store_args": "\n".join(
                    CargoPrinter(CargoPrinter.Mode.TEMPLATE).print_dataclass(
                        dc_obj=None, type_info=analyze_type(template_type)
                    )
                ),
            },
        )

        if args.dry_run:
            logger.info(f"Skipped writing {tabledef_file.name} due to `--dry-run`.")
            return
        logger.debug(f"File: {table_name}. Content: {content}\n")
        tabledef_file.write(content)


def fill_templates(
    output_dir: str,
    table_name: str,
    desynced_object_type: Type,
    objects: list,
    skip_any: bool = True,
):
    """Fills in both table definition and data storage templates.

    Args:
        output_dir (str): Directory to store results in.
        table_name (str): Name of the cargo (camelCase)
        desynced_object_type (Type): Python type to use for the table definition.
        objects (list): List of filled in objects, from game data, of Type `type`.
        skip_any (bool, optional): If True, attempts to filter for spoilers or fake data.
                                   Defaults to True.
    """
    # First write out the table definition.
    write_declaration(output_dir, table_name, desynced_object_type)

    # Then write out the storage templates.
    output_dir: str = os.path.join(output_dir, "Data", table_name)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    for desynced_object in objects:
        if skip_any and should_skip(desynced_object):
            continue
        with open(
            os.path.join(output_dir, desynced_object.name.replace("/", "_")),
            "w",
            encoding="utf-8",
        ) as storage_file:
            content: str = render_template(
                WikiTemplate.CARGO_STORE,
                {
                    "table_name": table_name,
                    "template_name": f"Data{table_name[0].upper() + table_name[1:]}",
                    "template_table_index": "DataTableIndex",
                    "name": desynced_object.name,
                    "args": "\n".join(
                        CargoPrinter().print_dataclass(
                            desynced_object, analyze_type(desynced_object_type)
                        )
                    ),
                },
            )

            if args.dry_run:
                logger.info("Skipped writing %s due to `--dry-run`.", storage_file.name)
                continue
            logger.debug("File: %s. Content: %s\n", desynced_object.name, content)
            storage_file.write(content)


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

    @dataclass
    class TD:
        type: Type
        objects: List

    # Mapping of cargo table name to the type and list of actual game data objects
    tables_by_name: Dict[str, TD] = {
        "entity": TD(Entity, game.entities),
        "component": TD(Component, game.components),
        "item": TD(Item, game.items),
        "instruction": TD(Instruction, game.instructions),
        "tech": TD(Technology, game.technologies),
        "techUnlock": TD(TechnologyUnlock, game.tech_unlocks),
        "techCategory": TD(TechnologyCategory, game.technology_categories),
    }

    for table_name, table_def in tables_by_name.items():
        fill_templates(
            output_dir=args.output_directory,
            table_name=table_name,
            desynced_object_type=table_def.type,
            objects=table_def.objects,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--game-data-directory",
        type=str,
        help="Path to the directory containing the lua game data files.",
        default="game_data/data",
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
