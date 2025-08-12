# Game Data Extractor and Desynced Wiki Upload

A set of scripts for exporting game data from [Desynced](https://www.desyncedgame.com/) lua files and importing it into the [Desynced Wiki](https://wiki.desyncedgame.com/Main_Page).  
Those are not battle-tested and might have various issues, feel free to modify them.  

## Setup

```
pip install -r requirements.txt
```

## Usage overview
Steps:
- 1 - [Get game files](#game_data_extraction)  
  Get the game "main" mod.
- 2 - [Generate wiki files](#generate-wiki-files)  
  Generate wiki files from the game files (`python cli_generate_wiki.py --help`).
- 3 - [Upload to wiki](#wiki-upload)  
  Upload files to Wiki.
  
Depending on what changed in the game files, you might need to make [extra adjustements](#extra-manual-things).

### Game Data Extraction

Either: 
- Extract the main mod from your game directory `<...>\Steam\steamapps\common\Desynced\Desynced\Content\mods\main.zip`
- (currently broken) Pull game data from steam using `cli_fetch_main_from_steam` (`python cli_fetch_main_from_steam.py --help`).

### Generate wiki files
See: `python cli_generate_wiki.py --help`.

The script will:  
1) Evaluates a subset of game files (path provided in argument) in a lua environment.
2) Traverses the `data` tree to parse out necessary information.
3) Outputs wiki templates and data to `--wiki-output-directory` structured by category.

### Wiki Upload

See: `python -m cli_upload_wiki --help`  
You need the "janitor" permission on the wiki. [Credentials needs to be set in config file.](#steam-and-wiki-credentials).  

The script will:
- For files in `--wiki-output-directory`, in `Template` uploads them as templates (cargo table definitions).
- For files in `--wiki-output-directory`, in `Data` uploads them to their own `Data:...` pages. (this does not create the "human" page meant to be read)
- Trigger cargo tables regeneration as needed

/!\ This currently does not remove older data removed from the game

### Extra manual things

- You might have to handle new name collisions. Generation script should stop and error out if it detects one.  
  Most of that can be handled by adding entries to `WIKI_NAME_OVERRIDES`. 
    - Also the DataTableIndex (table_index table) is related to handling name collisions, but me writting this didn't dive into it. 
- By default, only entities that are unlockable by players are included. You can force extra inclusions by adding names in `FORCE_INCLUDE_NAMES`.  
- Currently many pages like https://wiki.desyncedgame.com/Instructions have been written manually and need to be updated if extra content is done. Navboxes 
- Currently new images are not added automatically and you might need to use cli_missing_images and probably handle more manually there.

### Steam and Wiki Credentials

Copy `config.ini.example` to `config.ini` and update your credentials as needed.  
Steam credentials are needed to download the game assets.  
Wiki credentials are needed for the import process.  

This file is already ignored by git.

## Other helper scripts

Some other scripts to help with wiki maintenance. Most of those scripts can be resumed with `--resume`.

- `python -m cli_create_missing_pages --help`
- `python -m cli_cleanup_page_templates --help`
- `python -m cli_missing_images --help`
- `python -m cli_remove_data_pages --help`

## Useful links

|                              |                                                                                            |
| ---------------------------- | ------------------------------------------------------------------------------------------ |
| Cargo tables list            | https://wiki.desyncedgame.com/Special:CargoTables                                          |
| Browse all cargo tables data | https://wiki.desyncedgame.com/Special:Drilldown/                                           |
| One data page example        | https://wiki.desyncedgame.com/index.php?title=Data:Item:Infected_Circuit_Board&redirect=no |
| Special pages                | https://wiki.desyncedgame.com/Special:SpecialPages                                         |
| List all templates           | https://wiki.desyncedgame.com/Special:PrefixIndex?prefix=Template%3A&namespace=0           |

## Updating the scripts

Some notes in [DEV.md](DEV.md)

## Disclaimer

Please note that this repository and its contents are not officially related to or endorsed by Desynced or Stage Games.
