"""Reads game data from Desycned lua files and outputs corresponding wiki templates.

Evaluates the content of specific files in the game files.
On game update, the `lua` library may require changes.

"""

from dataclasses import dataclass
import pprint
import argparse
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Type

from util.constants import FETCHED_GAME_DATA_DIR, DEFAULT_WIKI_OUTPUT_DIR
from util.logger import get_logger
from wiki.data_categories import DataCategory
from wiki.wiki_name_overrides import get_name_collisions
from wiki.cargo.analyze_type import DataClassTypeInfo, analyze_type
from wiki.cargo.cargo_printer import CargoPrinter
from wiki.templates.templater import WikiTemplate, render_template

import lua.lua_util as lua_util
from lua.game_data import GameData
from models.category_filters import CategoryFilter
from models.component import Component
from models.decorators import DesyncedObject
from models.entity import Entity
from models.instructions import Instruction
from models.item import Item
from models.tech import (
    Technology,
    TechnologyCategory,
    TechnologyUnlock,
)

logger = get_logger()


class GenerateWiki:

    def __init__(
        self,
        wiki_output_dir: str,
        game_data_directory: str,
        overwrite: bool,
        only_templates: bool,
        only_categories: list[DataCategory],
    ):
        self.wiki_output_directory = wiki_output_dir
        self.confirmed_overwrite: bool = overwrite
        self.only_templates = only_templates
        self.only_categories = only_categories

        lua = lua_util.load_lua_runtime(game_data_directory)
        self.game: GameData = GameData(lua)

    def clean_output_dir(self, output_dir: Path):
        """Recursively deletes all files in `dir`. Doesn't touch directories.

        Args:
            dir (str): Root directory to delete files in.
        """
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path: str = os.path.join(root, file)
                logger.debug(f"Deleting: {file_path}")
                os.remove(file_path)

    def write_declaration(
        self, output_dir: Path, table_name: str, template_type: Type[DesyncedObject]
    ):
        template_dir: str = os.path.join(output_dir, "Template")
        Path(template_dir).mkdir(parents=True, exist_ok=True)
        with open(
            os.path.join(template_dir, f"{table_name}"), "w", encoding="utf-8"
        ) as tabledef_file:
            object_type = analyze_type(template_type)
            if not isinstance(object_type, DataClassTypeInfo):
                logger.error(
                    f"Trying to process table template {table_name} of wrong type {object_type}. Expected DataClassTypeInfo."
                )
                return

            content: str = render_template(
                WikiTemplate.CARGO_DECLARE,
                {
                    "table_name": table_name,
                    "declare_args": "\n".join(
                        CargoPrinter(CargoPrinter.Mode.DECLARATIONS).print_dataclass(
                            dc_obj=None, type_info=object_type
                        )
                    ),
                    "store_args": "\n".join(
                        CargoPrinter(CargoPrinter.Mode.TEMPLATE).print_dataclass(
                            dc_obj=None, type_info=object_type
                        )
                    ),
                },
            )

            logger.debug(f"File: {table_name}. Content: {content}\n")
            tabledef_file.write(content)

    def fill_templates(
        self,
        output_dir: Path,
        table_name: str,
        desynced_object_type: Type[DesyncedObject],
        objects: list,
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

        if self.only_templates:
            return

        # Then write out the storage templates.
        output_path: Path = Path(os.path.join(output_dir, "Data", table_name))
        output_path.mkdir(parents=True, exist_ok=True)
        if output_path.exists():
            # prompt only once for overwriting
            if not self.confirmed_overwrite:
                # prompt user to confirm deletion
                confirm = input(
                    f"Output directory {output_dir} already contains some data. Do you want to overwrite it? (y/n): "
                )
                if confirm.lower() != "y":
                    logger.info("Exiting without deleting output directory.")
                    return
                self.confirmed_overwrite = True

            self.clean_output_dir(output_path)

        for desynced_object in objects:
            output_file_path = os.path.join(
                output_path, desynced_object.name.replace("/", "_").replace("*", "")
            )

            # File should not exist, otherwise we have a name conflict, or some data generated twice.
            # In any case it's good to have, instead of overwriting silently.
            if os.path.isfile(output_file_path):
                raise ValueError(
                    f"File {output_file_path} already exists. Missing name override?"
                )

            with open(
                output_file_path,
                "w",
                encoding="utf-8",
            ) as storage_file:
                object_type = analyze_type(desynced_object_type)

                if not isinstance(object_type, DataClassTypeInfo):
                    logger.error(
                        f"Trying to process object {desynced_object.name} of wrong type {object_type}. Expected DataClassTypeInfo."
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
                            CargoPrinter().print_dataclass(desynced_object, object_type)
                        ),
                    },
                )

                logger.debug(f"File: {desynced_object.name}. Content: {content}\n")
                storage_file.write(content)

    def build(self):
        output_directory = Path(self.wiki_output_directory)

        # Delete outdated wiki files.
        output_directory.mkdir(parents=True, exist_ok=True)
        if output_directory.exists() and not self.only_categories:
            if not self.confirmed_overwrite:
                # prompt user to confirm deletion
                confirm = input(
                    f"Output directory {output_directory} already exists. Do you want to overwrite it? (y/n): "
                )
                if confirm.lower() != "y":
                    logger.info("Exiting without deleting output directory.")
                    return

            self.clean_output_dir(output_directory)

        @dataclass
        class TableData:
            type: Type[DesyncedObject]  # object type from models
            objects: List
            should_filter: bool = False

        # Mapping of cargo table name to the type and list of actual game data objects
        tables_by_name: Dict[DataCategory, TableData] = {
            DataCategory.entity: TableData(Entity, self.game.entities, True),
            DataCategory.component: TableData(Component, self.game.components, True),
            DataCategory.item: TableData(Item, self.game.items, True),
            DataCategory.instruction: TableData(Instruction, self.game.instructions),
            DataCategory.tech: TableData(Technology, self.game.technologies),
            DataCategory.techUnlock: TableData(
                TechnologyUnlock, self.game.tech_unlocks
            ),
            DataCategory.techCategory: TableData(
                TechnologyCategory, self.game.technology_categories
            ),
            DataCategory.categoryFilter: TableData(
                CategoryFilter, self.game.category_filters
            ),
        }

        # Apply filtering
        for table_name, td in tables_by_name.items():
            if td.should_filter:
                td.objects = [
                    obj for obj in td.objects if not self.game.should_skip_upload(obj)
                ]

        if self.only_categories:
            filtered_tables = {
                k: tables_by_name[k]
                for k in self.only_categories
                if k in tables_by_name
            }
            if len(filtered_tables) == 0:
                logger.error("--table-filter filtered all tables.")
                return
            tables_by_name = filtered_tables

        if not self.only_templates:
            has_error = False
            for name, table in tables_by_name.items():
                if collisions := get_name_collisions(table.objects):
                    # transform Dict[str, list[str]] to Dict[str, str] with ', '.join(ids)
                    formatted_collisions = {
                        name: ",".join(ids) for name, ids in collisions.items()
                    }
                    logger.error(
                        f"Name collisions found in table {name}:\n{pprint.pformat(formatted_collisions, indent=4)}",
                    )
                    has_error = True
            if has_error:
                logger.error(
                    "Name collisions found. Please resolve them before proceeding. (search WIKI_NAME_OVERRIDES)"
                )
                return

        for table_name, table_def in tables_by_name.items():
            self.fill_templates(
                output_dir=output_directory,
                table_name=table_name,
                desynced_object_type=table_def.type,
                objects=table_def.objects,
            )

        logger.info(f"Finished writing wiki files to {output_directory} directory")


def main(args):
    logger.info(f"Running with args:\n{pprint.pformat(vars(args))}")

    try:
        only_categories = [
            DataCategory[name.strip()]
            for name in (
                args.only_categories.split(",") if args.only_categories else []
            )
        ]
    except KeyError as e:
        logger.exception(f"Invalid category name: {e.args[0]}")

    GenerateWiki(
        args.wiki_output_directory,
        args.game_data_directory,
        args.overwrite,
        args.template_only,
        only_categories,
    ).build()


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
        "--wiki-output-directory",
        type=str,
        help="Path to the directory containing the output wiki files for gamedata",
        default=DEFAULT_WIKI_OUTPUT_DIR,
    )
    parser.add_argument(
        "--overwrite",
        action=argparse.BooleanOptionalAction,
        help="If True, will clean the output directory without prompting",
        default=False,
    )
    data_categories = {e.value for e in DataCategory}
    parser.add_argument(
        "--only-categories",
        type=str,
        help=f"If set, only produces data for categories specified. Comma separated list. Possible values: {data_categories}",
    )
    parser.add_argument(
        "--template-only",
        action=argparse.BooleanOptionalAction,
        help="If True, only produces templates and no data",
        default=False,
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output (sets logging level to DEBUG)",
        default=False,
    )

    parsed_args = parser.parse_args()
    logger.setLevel(logging.DEBUG if parsed_args.debug else logging.INFO)
    main(parsed_args)
