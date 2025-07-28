import logging
import os
from pprint import pprint
from typing import Optional

import lupa
from lupa import LuaRuntime

from util.logger import initLogger

current_file = os.path.basename(__file__)
logger = initLogger(current_file)


# Five ticks per second
def per_tick_to_per_second(ticks: int) -> Optional[int]:
    return ticks * 5 if ticks else None


def tick_duration_to_seconds(ticks: int) -> Optional[float]:
    return ticks / 5 if ticks else None


# Set of lua files that are executed in the runtime for `load_lua_runtime`
TARGET_FILES: list[str] = [
    "data/data.lua",
    "data/frames.lua",
    "data/visuals.lua",
    "data/components.lua",
    "data/items.lua",
    "data/instructions.lua",
    "data/techs.lua",
    "data/tech/tech_alien.lua",
    "data/tech/tech_blight.lua",
    "data/tech/tech_human.lua",
    "data/tech/tech_robots.lua",
    "data/tech/tech_virus.lua",
]


def load_lua_runtime(game_data_dir) -> LuaRuntime:
    """Creates a lua runtime and executes files in `dir`.

    Only loads specific files.

    Args:
        dir (str, optional): Directory to look for files in. Defaults to "game_data/main/data".

    Returns:
        LuaRuntime: The created runtime with all files executed for evaluation.
    """

    # Code to allow the evaluation of game files without running the game.
    preamble = """
    data = {
        items = {},
        frames = {},
        update_mapping = {},
        visuals = {},
        visualmeshes = {},
        visualeffects = {},
        components = {},
        techs = {},
        tech_categories = {}
    }

    UIMsg = {}
    Map = {}
    EntityAction = {}
    FactionAction = {}
    Delay = {}

    function Map:GetSettings()
        return { blight_threshold = 0.1 }
    end

    function CreateConstructionRecipe(recipe, ticks)
        return {
            items = recipe,
            ticks = ticks
        }
    end

    function CreateUplinkRecipe(recipe, ticks)
        return {
            items = recipe,
            ticks = ticks
        }
    end

    function CreateProductionRecipe(recipe, production, amount)
        return {
            items = recipe,
            producers = production,
            num_produced = amount
        }
    end

    function CreateMiningRecipe(miners)
        return miners
    end

    TICKS_PER_SECOND = 5
    """

    lua = LuaRuntime(
        unpack_returned_tuples=True
    )  # (ignoreit?) pyright: ignore[reportCallIssue]
    lua.execute(preamble)

    # Check if game_data_dir exists
    if not os.path.exists(game_data_dir):
        raise FileNotFoundError(
            f"Game data directory '{game_data_dir}' does not exist."
        )

    for file in TARGET_FILES:
        file_path = os.path.join(game_data_dir, file)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Lua file was not found: '{file_path}'.")
            continue

        with open(file_path, "r", encoding="utf-8") as readfile:
            logger.info("Executing lua file: %s", readfile.name)
            file_content = readfile.read()
            # remove special lines
            file_content = file_content.replace("local package = ...", "package = {}")
            lua.execute(file_content)

    return lua


def print_lua_table(table, filter_keys=None, prefix=""):
    """Recursively prints the table at `table`.

    Args:
        table (_type_): A lua table
        filter_keys (_type_, optional): If set, prints only these keys. Defaults to None.
        prefix (str, optional): If set, prefixes each print statement. Defaults to "".
    """
    if table == None or not lupa.lua_type(table) == "table":
        return
    keys = list(table)
    for key in keys:
        if filter_keys and key not in filter_keys:
            continue
        val = table[key]
        if lupa.lua_type(val) == "table":
            print(f"{prefix}{key}:")
            print_lua_table(val, filter_keys, prefix + "\t")
        else:
            print(f"{prefix}{key}: {str(table[key])}")


def get_visual_key(tbl) -> Optional[str]:
    """Returns the key for use in the `visuals` table corresponding to `tbl`.

    Args:
        tbl: Lua table to get the visual key for.

    Returns:
        Optional[str]: Visual key if it exists or None.
    """
    return tbl["visual"]


def print_dict_and_visual(source, visuals):
    """Recursively prints the table at `source` and its corresponding entry in `visuals` if it exists.

    Args:
        source (_type_): Lua object (likely with a visual key)
        visuals (_type_): Lua table representing the set of visuals
    """
    for entry in source:
        print(" ")
        print(entry)
        print_lua_table(source[entry])
        if not source[entry]["visual"]:
            continue
        visual_key = visual_key(source[entry])
        print("visual table: ")
        print_lua_table(visuals[visual_key], prefix="\t")
