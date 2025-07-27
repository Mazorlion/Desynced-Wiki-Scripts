"""Reads game data from Desycned lua files and outputs corresponding wiki templates.

Evaluates the content of specific files in the game files.
On game update, the `lua` library may require changes.

"""

import pprint
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
from models.tech import (
    TechCategorization,
    Technology,
    TechnologyCategory,
    TechnologyUnlock,
)
from util.constants import DEFAULT_OUTPUT_DIR, FETCHED_GAME_DATA_DIR
from wiki.cargo.analyze_type import DataClassTypeInfo, analyze_type
from wiki.cargo.cargo_printer import CargoPrinter
from wiki.templates.templater import WikiTemplate, render_template

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
# Get current filename for logging
current_file = os.path.basename(__file__)
logger = logging.getLogger(current_file)


class LuaAnalyzer:
    def __init__(self, args) -> None:
        self.args = args

    def should_skip(self, desynced_object: Any) -> bool:
        return desynced_object.name not in self.unlockable_names

    def clean_output_dir(self, output_dir: str):
        """Recursively deletes all files in `dir`. Doesn't touch directories.

        Args:
            dir (str): Root directory to delete files in.
        """
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path: str = os.path.join(root, file)
                logger.debug(f"Deleting: {file_path}")
                os.remove(file_path)

    def write_declaration(self, output_dir: str, table_name: str, template_type: Type):
        template_dir: str = os.path.join(output_dir, "Template")
        Path(template_dir).mkdir(parents=True, exist_ok=True)
        with open(
            os.path.join(template_dir, f"{table_name}"), "w", encoding="utf-8"
        ) as tabledef_file:
            type = analyze_type(template_type)
            if not isinstance(type, DataClassTypeInfo):
                logger.error(
                    f"Trying to process table template {table_name} of wrong type {type}. Expected DataClassTypeInfo."
                )
                return

            content: str = render_template(
                WikiTemplate.CARGO_DECLARE,
                {
                    "table_name": table_name,
                    "declare_args": "\n".join(
                        CargoPrinter(CargoPrinter.Mode.DECLARATIONS).print_dataclass(
                            dc_obj=None, type_info=type
                        )
                    ),
                    "store_args": "\n".join(
                        CargoPrinter(CargoPrinter.Mode.TEMPLATE).print_dataclass(
                            dc_obj=None, type_info=type
                        )
                    ),
                },
            )

            logger.debug(f"File: {table_name}. Content: {content}\n")
            tabledef_file.write(content)

    def fill_templates(
        self,
        output_dir: str,
        table_name: str,
        desynced_object_type: Type,
        objects: list,
        should_filter: bool,
    ):
        """Fills in both table definition and data storage templates.

        Args:
            output_dir (str): Directory to store results in.
            table_name (str): Name of the cargo (camelCase)
            desynced_object_type (Type): Python type to use for the table definition.
            objects (list): List of filled in objects, from game data, of Type `type`.
            should_filter (bool, optional): If True, attempts to filter for spoilers or fake data.
        """
        # First write out the table definition.
        self.write_declaration(output_dir, table_name, desynced_object_type)

        if self.args.template_only:
            return

        # Then write out the storage templates.
        output_path: Path = Path(os.path.join(output_dir, "Data", table_name))
        output_path.mkdir(parents=True, exist_ok=True)
        for desynced_object in objects:
            if should_filter and self.should_skip(desynced_object):
                continue
            with open(
                os.path.join(
                    output_path, desynced_object.name.replace("/", "_").replace("*", "")
                ),
                "w",
                encoding="utf-8",
            ) as storage_file:
                type = analyze_type(desynced_object_type)

                if not isinstance(type, DataClassTypeInfo):
                    logger.error(
                        f"Trying to process object {desynced_object.name} of wrong type {type}. Expected DataClassTypeInfo."
                    )
                    continue

                content: str = render_template(
                    WikiTemplate.CARGO_STORE,
                    {
                        "table_name": table_name,
                        "template_name": f"Data{table_name[0].upper() + table_name[1:]}",
                        "template_table_index": "DataTableIndex",
                        "name": desynced_object.name,
                        "args": "\n".join(
                            CargoPrinter().print_dataclass(desynced_object, type)
                        ),
                    },
                )

                logger.debug("File: %s. Content: %s\n", desynced_object.name, content)
                storage_file.write(content)

    def main(self):
        game_data_directory = self.args.game_data_directory
        output_directory = self.args.output_directory

        lua = lua_util.load_lua_runtime(game_data_directory)
        game = GameData(lua)
        self.game = game

        # Identify objects that can be unlocked via tech as allowed to upload to the wiki.
        # TODO(maz): Upload bug enemies and stuff.
        self.unlockable_names = set([x.name for x in game.tech_categorizations])

        # Delete outdated wiki files.
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        if not self.args.overwrite and Path(output_directory).exists():
            # prompt user to confirm deletion
            confirm = input(
                f"Output directory {output_directory} already exists. Do you want to overwrite it? (y/n): "
            )
            if confirm.lower() != "y":
                logger.info("Exiting without deleting output directory.")
                return

            self.clean_output_dir(output_directory)

        @dataclass
        class TD:
            type: Type
            objects: List
            should_filter: bool = False

        # Mapping of cargo table name to the type and list of actual game data objects
        tables_by_name: Dict[str, TD] = {
            "entity": TD(Entity, game.entities, True),
            "component": TD(Component, game.components, True),
            "item": TD(Item, game.items, True),
            "instruction": TD(Instruction, game.instructions),
            "tech": TD(Technology, game.technologies),
            "techUnlock": TD(TechnologyUnlock, game.tech_unlocks),
            "techCategory": TD(TechnologyCategory, game.technology_categories),
            "objectTechCategory": TD(TechCategorization, game.tech_categorizations),
        }

        if self.args.table_filter and len(self.args.table_filter) > 0:
            filtered_tables = {
                k: tables_by_name[k]
                for k in self.args.table_filter.split(",")
                if k in tables_by_name
            }
            if len(filtered_tables) == 0:
                logger.error("--table-filter filtered all tables.")
                return
            tables_by_name = filtered_tables

        for table_name, table_def in tables_by_name.items():
            self.fill_templates(
                output_dir=self.args.output_directory,
                table_name=table_name,
                desynced_object_type=table_def.type,
                objects=table_def.objects,
                should_filter=table_def.should_filter,
            )

        logger.info("Finished writing wiki files to %s directory", output_directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze extracted game files and generate wiki files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "game_data_directory",
        nargs="?",
        type=str,
        help="Path to the directory containing the lua game data files (= root of main mod)",
        default=FETCHED_GAME_DATA_DIR,
    )
    parser.add_argument(
        "--output-directory",
        type=str,
        help="Path to the directory containing the output wiki files for gamedata",
        default=DEFAULT_OUTPUT_DIR,
    )
    parser.add_argument(
        "--overwrite",
        action=argparse.BooleanOptionalAction,
        help="If True, will clean the output directory without prompting",
        default=False,
    )
    parser.add_argument(
        "--table-filter",
        type=str,
        help="If set, only produces data for tables specified. Comma separated list",
    )
    parser.add_argument(
        "--template-only",
        action=argparse.BooleanOptionalAction,
        help="If True, only produces templates and no data",
        default=False,
    )

    parsed_args = parser.parse_args()

    logger.info(f"Running with args: {pprint.pformat(vars(parsed_args))}")
    LuaAnalyzer(parsed_args).main()
