# Game Data Extractor and Desynced Wiki Upload

A set of scripts for exporting game data from [Desynced](https://www.desyncedgame.com/) lua files and importing it into the [Desynced Wiki](https://wiki.desyncedgame.com/Main_Page).

Note: Both tools below default to `--dry_run` and should not perform any destructive actions by default. To disable this behavior set `--no-dry_run`.

TODO(maz): Fix mixed hyphen/underscore in flags.

## Setup

```
pip install -r requirements.txt
```

## Game Data Extraction

See: `analyze_lua.py`.

WARNING: Deletes all files (not directories) found in `--recipe_directory` if `--no-dry_run`.

1) Evaluates a subset of game files in `--game_data_directory` in a lua environment.
2) Traverses the `data` tree to parse out necessarty information.
3) Outputs wiki templates to (currently just recipes) to `--recipe_directory`.

## Wiki Upload

See: `import.py`

1) Reads the set of files in `--recipe_directory`
2) For each file, updates a specific page in the [GameData Category](https://wiki.desyncedgame.com/Category:GameData) with the content of that file, based on filename.


### Wiki Credentials

TODO(maz): Make this less bad and easier to use.

Place credentials in `wiki/wiki_credentials.py` in the format:
```
username = "<username>"
password = "<password>"
```

This file is already ignored by git.

## Disclaimer

Please note that this repository and its contents are not officially related to or endorsed by Desynced or Stage Games.
