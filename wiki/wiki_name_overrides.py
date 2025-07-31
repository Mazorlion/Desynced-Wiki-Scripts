from typing import Any

from util.constants import WIKI_NAME_OVERRIDES


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
