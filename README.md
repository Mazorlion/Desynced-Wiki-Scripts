# Game Data Extractor and Desynced Wiki Upload

A set of scripts for exporting game data from [Desynced](https://www.desyncedgame.com/) lua files and importing it into the [Desynced Wiki](https://wiki.desyncedgame.com/Main_Page).

Note: Both tools below default to `--dry-run` and should not perform any destructive actions by default. To disable this behavior set `--no-dry-run`.

## Setup

```
pip install -r requirements.txt
```

Place the lua files into a directory called `game_data`, or alternatively change the `--game-data-directory` for analyze.py.

## Game Data Extraction

### Pull game data from steam
See: `fetch_main_from_steam.py`

1) Prompts user to log in from CLI
  - Steam account must have a valid purchase of desynced.
2) Downloads `main.zip` from the steam depot
3) Unzips into a directory for use by analysis scripts.

### Analyze lua and generate wiki files
See: `analyze_lua.py`.

WARNING: Deletes all files (not directories) found in `--output-directory` if `--no-dry-run`.

1) Evaluates a subset of game files in `--game-data-directory` in a lua environment.
2) Traverses the `data` tree to parse out necessary information.
3) Outputs wiki templates to `--output-directory` structured by category.

### Workflow

1) For each cargo table to create in the wiki, there should be a model in `models`.
2) Once you have it modeled as you'd like, update `lua/game_data.py` to build the models and store them.
3) Update `analyze_lua.py` to create templates based on this new model and the collection of them you built in `GameData`.

### Special Table

There exists a special table which is defined in `wiki/include/Template/DataTableIndex`. This table is used to figure out which table a given name belongs to. This means that, for example, a `Recipe` template on the wiki can just take a name, query the `TableIndex` to find which table the name lives in, then query that table using the name.

This is especially useful for wiki templates like `Recipe` which are shared across many different types of objects.

NOTE: Every `Data` page uploaded contains a directive to `store` in the table index.

### Models

In order to make adding new data as easy as possible, the heavy lifting for how fields should be named and formatted is done by the two files in `wiki/cargo`: `analyze_type.py` and `cargo_printer.py`.

Models are created from dataclasses (proxied via `@desynced_object`) and just declare the fields they'd like to appear in the table. Lets take a simple example with `Technology`:

```python
@desynced_object
class Technology:
    name: str
    description: str
    category: str
    texture: str
    # List of required techs by name.
    required_tech: List[str] = annotate(ListFieldOptions(max_length=3))
    # Number of times uplink_recipe must be completed.
    progress_count: int
    uplink_recipe: Recipe
```

This model is automatically converted into a cargo table definition like the following:
```
<noinclude>
[[Category:Data:TableDefinition]]
{{#cargo_declare:
_table=tech
|name = String
|description = String
|category = String
|texture = String
|requiredTech1 = String
|requiredTech2 = String
|requiredTech3 = String
|progressCount = Integer
|ingredient1 = String
|amount1 = Integer
|ingredient2 = String
|amount2 = Integer
|ingredient3 = String
|amount3 = Integer
|ingredient4 = String
|amount4 = Integer
|producer1 = String
|time1 = Float
|producer2 = String
|time2 = Float
|recipeType = String (allowed values=Construction,Production,Uplink)
|numProduced = Integer
}}</noinclude>
<includeonly>
{{#cargo_store:
_table=tech
|name = {{{name}}}
|description = {{{description}}}
|category = {{{category}}}
|texture = {{{texture}}}
|requiredTech1 = {{{requiredTech1}}}
|requiredTech2 = {{{requiredTech2}}}
|requiredTech3 = {{{requiredTech3}}}
|progressCount = {{{progressCount}}}
|ingredient1 = {{{ingredient1}}}
|amount1 = {{{amount1}}}
|ingredient2 = {{{ingredient2}}}
|amount2 = {{{amount2}}}
|ingredient3 = {{{ingredient3}}}
|amount3 = {{{amount3}}}
|ingredient4 = {{{ingredient4}}}
|amount4 = {{{amount4}}}
|producer1 = {{{producer1}}}
|time1 = {{{time1}}}
|producer2 = {{{producer2}}}
|time2 = {{{time2}}}
|recipeType = {{{recipeType}}}
|numProduced = {{{numProduced}}}
}}</includeonly>
```

Notice a few things:
1) The `Recipe` in `uplink_recipe` was automatically flattened into the main structure, and the lists inside were expanded into their own fields.
2) The list of techs in `required_tech` was expanded to have an entry for each field.
    - The number of entries for each list is described by a field annotation

```python
    required_tech: List[str] = annotate(ListFieldOptions(max_length=3))
```
TODO(maz): Make this dynamically figure out list length from the longest list that appears in the game data.

There are a number of other useful decorator options in `models/decorators_options.py`.


## Wiki Upload

See: `import.py`

1) Reads the set of files in `--input-directory`
2) For files in `--input-directory` in `Template` uploads them as templates (cargo table definitions).
3) For files in `--input-directory` in `Data` uploads them to their own pages which each invoke the template created by the files in the `Template` directory.

## Schema Change Process

`import.py` now does all of the following steps for you, though you must have the correct permissions on the wiki.

TODO(maz): Fail without the correct permissions.

1) Upload the templates
2) For each template that changed (or all of them) trigger recreate of the table on the wiki, using a new table
3) Upload the data using the new templates

New tables/data must be swapped in at https://wiki.desyncedgame.com/Special:CargoTables manually. If it didn't work, delete the temporary table and try again.

TODO(maz): Add specific flags for force recreating data.

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
