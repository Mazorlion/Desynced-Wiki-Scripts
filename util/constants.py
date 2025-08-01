DEFAULT_WIKI_OUTPUT_DIR = "wiki_output"
FETCHED_GAME_DATA_DIR = "fetched_game_data"

DESYNCED_APP_ID = 1450900

WIKI_BASE_URL = "https://wiki.desyncedgame.com"

FORCE_INCLUDE_NAMES = {
    "Command Center",
    "Trilobyte",
    "Malika",
    "Mothika",
    "Scale Worm",
    "Ravager",
    "Trilobyte Attack",
    "Trilobyte Attack (1)",
    "Trilobyte Attack (2)",
    "Trilobyte Attack (3)",
    "Trilobyte Attack (4)",
    "Trilobyte Attack (T2)",
    "Trilobyte Attack (T3)",
    "Wasp Attack",
    "Greelobyte",
    "Trilopew",
    "Wasp",
    "Gigakaiju",
    "Shield Worm",
    "Bug Hole",
    "Bug Hive",
    "Large Bug Hive",
    "Giant Beast",
}

# List of object for which to override names with a custom name
# This is used to handle entries having the same names in the game, but need to be differentiated in the wiki.
# Example: Both c_human_aicenter and c_mission_human_aicenter are called "AI Research Center" in the game.
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
    "f_bug_home": "Bug Hole (Giant)",
}
