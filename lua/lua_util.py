import logging
import os
from typing import Optional

import lupa
from lupa import LuaRuntime

logger = logging.getLogger("lua_util.py")


# Five ticks per second
def ticks_to_seconds(ticks: int) -> int:
    return ticks * 5 if ticks else None


def tick_duration_to_seconds(ticks: int) -> float:
    return ticks / 5 if ticks else None


# Set of lua files that are executed in the runtime for `load_lua_runtime`
TARGET_FILES: list[str] = [
    "data.lua",
    "frames.lua",
    "visuals.lua",
    "components.lua",
    "items.lua",
    "instructions.lua",
    "techs.lua",
    "tech_alien.lua",
    "tech_blight.lua",
    "tech_human.lua",
    "tech_robots.lua",
    "tech_virus.lua",
]


def load_lua_runtime(game_data_dir="game_data/main/data") -> LuaRuntime:
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

    Map = {}
    EntityAction = {}
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

    """

    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(preamble)

    for root, _, files in os.walk(game_data_dir):
        for file in files:
            if file.endswith(".lua") and file in TARGET_FILES:
                with open(os.path.join(root, file), "r", encoding="utf-8") as readfile:
                    logger.info("Executing lua file: %s", readfile.name)
                    lua.execute(readfile.read().replace("local package = ...", ""))
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
