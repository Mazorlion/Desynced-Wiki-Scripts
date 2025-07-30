# List of object for which to override names with a custom name
# This is used to handle entries having the same names in the game, but need to be differentiated in the wiki.

# Example: Both c_human_aicenter and c_mission_human_aicenter are called "AI Research Center" in the game.

from typing import Any

from models.decorators import desynced_object

# Supports entities, items, components
WIKI_NAME_OVERRIDES: dict[str, str] = {
    "c_mission_human_aicenter": "AI Research Center (Mission)",
    "f_bot_2m_as": "Command Center (Bot)",
    "c_internal_crane2": "Item Transporter (Large Beacon)",
    "c_internal_crane1": "Item Transporter (Beacon)",
    "c_internal_transporter": "Item Transporter (Human Warehouse)",
    "f_building2x1d": "Building 2x1 (1M) (Stockpile)",
    "f_building2x1c": "Building 2x1 (2M) (Advanced Materials)",
    "f_building2x2c": "Building 2x2 (2M1L) (Epic Structures) (A)",
    "f_building2x2d": "Building 2x2 (2M1L) (Epic Structures) (B)",
    "c_trilobyte_attack1": "Trilobyte Attack (1)",
    "c_trilobyte_attack2": "Trilobyte Attack (2)",
    "c_trilobyte_attack3": "Trilobyte Attack (3)",
    "c_trilobyte_attack4": "Trilobyte Attack (4)",
    "c_trilobyte_attack_t2": "Trilobyte Attack (T2)",
    "c_trilobyte_attack_t3": "Trilobyte Attack (T3)",
}


def get_name_override(lua_id: str) -> str | None:
    """
    Returns the name override for the given lua_id.
    If no override is found, returns the lua_id itself.
    """
    return WIKI_NAME_OVERRIDES.get(lua_id)


def get_name_collisions(objects: list[Any]) -> dict[str, list[str]]:
    """
    Check if there are any name collisions in the table.
    Argument: table: List of desynced_object
    Returns: A list of names that are duplicated.
    If there are no collisions, returns an empty list.
    """
    ids_per_name: dict[str, list[str]] = {}

    for item in objects:
        if not hasattr(item, "name") or not hasattr(item, "lua_id"):
            continue

        name = item.name
        if name not in ids_per_name:
            ids_per_name[name] = []
        ids_per_name[name].append(item.lua_id)

    # Filter out names with only one ID
    return {name: ids for name, ids in ids_per_name.items() if len(ids) > 1}
