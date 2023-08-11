# Game Data Extractor and Desynced Wiki Upload

A set of scripts for exporting game data from [Desynced](https://www.desyncedgame.com/) lua files and importing it into the [Desynced Wiki](https://wiki.desyncedgame.com/Main_Page).

Note: Both tools below default to `--dry-run` and should not perform any destructive actions by default. To disable this behavior set `--no-dry-run`.

## Setup

```
pip install -r requirements.txt
```

Place the lua files into a directory called `game_data`, or alternatively change the `--game-data-directory` for analyze.py.

## Game Data Extraction

See: `analyze_lua.py`.

WARNING: Deletes all files (not directories) found in `--output-directory` if `--no-dry-run`.

1) Evaluates a subset of game files in `--game-data-directory` in a lua environment.
2) Traverses the `data` tree to parse out necessary information.
3) Outputs wiki templates to `--output-directory` structured by category.

## Wiki Upload

See: `import.py`

1) Reads the set of files in `--input-directory`
2) For each file, updates a specific page in the [GameData Category](https://wiki.desyncedgame.com/Category:GameData) with the content of that file, based on filename and parent directory.

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
