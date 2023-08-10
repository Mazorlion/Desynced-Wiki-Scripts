import logging
from pprint import pprint, pformat
from lupa import LuaRuntime
from typing import Optional

from zmq import Socket
from lua.lua_util import (
    print_lua_table,
    tick_duration_to_seconds,
    ticks_to_seconds,
)
from models.entity import Entity, EntityType, SlotType
from models.mining_recipe import MiningRecipe
from models.recipe import Recipe, RecipeItem, RecipeProducer, RecipeType
from models.sockets import Sockets
from models.types import Race

logger = logging.getLogger("GameData")


class GameData:
    """Encapsulates the exploration of a lua runtime that has evaluated the game files for Desynced.

    TODO(maz): Clean this up for real :<

    Example Usage:

        lua = lupa.LuaRuntime()
        lua.execute(...)
        data = GameData(lua)
    """

    def __init__(self, lua: LuaRuntime):
        self.lua: LuaRuntime = lua
        self.frames = self.globals().data.frames
        self.components = self.globals().data.components
        self.items = self.globals().data["items"]
        self.recipes: list[Recipe] = self._parse_recipes()
        self.mining_recipes: list[MiningRecipe] = self._parse_mining_recipes()
        self.entities: list[Entity] = self._parse_entities()

    def _parse_entities(self):
        entities: list[Entity] = []
        for frame, frame_tbl in self.frames.items():
            # Skip frames that don't have visuals
            visual_key = frame_tbl["visual"]
            if not visual_key:
                logger.debug(f"Skipping {frame} due to missing visual table.")
                continue
            # Map to visuals
            visual_tbl = self.lookup_visual(visual_key)
            if not visual_tbl:
                logger.debug(f"Skipping {frame} due to missing visual table.")
                continue

            if not visual_tbl["sockets"]:
                continue

            sockets: Sockets = Sockets()
            for idx, socket in visual_tbl["sockets"].items():
                sockets.increment_socket(socket[2])

            types = []
            if frame_tbl["trigger_channels"]:
                for type in frame_tbl["trigger_channels"].split("|"):
                    types.append(EntityType[type.upper()])

            entities.append(
                Entity(
                    name=frame_tbl["name"],
                    health=frame_tbl["health_points"],
                    power_usage_per_second=ticks_to_seconds(frame_tbl["power"])
                    if frame_tbl["power"]
                    else 0,
                    movement_speed=frame_tbl["movement_speed"],
                    visibility=frame_tbl["visibility_range"],
                    storage=frame_tbl["slots"]["storage"]
                    if frame_tbl["slots"]
                    else 0,
                    size=frame_tbl["size"],
                    race=Race[frame_tbl["race"].upper()]
                    if frame_tbl["race"]
                    else "",
                    types=types,
                    sockets=sockets,
                    slot_type=SlotType[frame_tbl["slot_type"].upper()]
                    if frame_tbl["slot_type"]
                    else SlotType.NONE,
                )
            )

        return entities

    def _parse_recipes(self) -> list[Recipe]:
        """Parses and returns the recipes from various structures in the runtime.

        Returns:
            list[Recipe]: List of recipes for objects in the runtime.
        """
        ret: list[Recipe] = []
        RECIPE_SOURCES: list = [
            self.frames,
            self.components,
            self.items,
        ]
        for source in RECIPE_SOURCES:
            for key, tbl in source.items():
                recipe: Optional[Recipe] = self._parse_recipe_from_table(tbl)
                if not recipe:
                    continue
                ret.append(recipe)
        return ret

    def data_lookup(self, field: str, name: str):
        """Shortcut for accessing `data` fields with error handling.

        Args:
            field (str): Field in `data` to access.
            name (str): Entry in `data[field]` to return.

        Returns:
            Any | None: Returns the object found or else None.
        """
        try:
            return self.lua.globals().data[field][name]
        except KeyError:
            return None

    def lookup_item_name(self, item_id: str) -> Optional[str]:
        """Returns the `name` for the corresponding `item_id`.

        Args:
            item_id (str): Lua ID of the item to look up.

        Returns:
            Optional[str]: Name of the item or None if not found.
        """
        item = self.data_lookup("items", item_id)
        if item:
            name: str = item["name"]
            return name.title() if name == "Silica sand" else name
        return None

    def lookup_component_name(self, component_id: str) -> Optional[str]:
        """Returns the `name` for the corresponding `component_id`.

        Args:
            component_id (str): Lua ID of the component to look up.

        Returns:
            Optional[str]: Name of the component or None if not found.
        """
        component = self.data_lookup("components", component_id)
        if component:
            return component["name"]
        return None

    def lookup_frame_name(self, frame_id: str) -> Optional[str]:
        """Returns the `name` for the corresponding `frame_id`.

        Args:
            frame_id (str): Lua ID of the frame to look up.

        Returns:
            Optional[str]: Name of the item or None if not found.
        """
        item = self.data_lookup("frames", frame_id)
        if item:
            return item["name"]
        return None

    def lookup_visual(self, name: str):
        return self.data_lookup("visuals", name)

    def globals(self):
        return self.lua.globals()

    # -- Mining Recipes --
    # mining_recipe = CreateMiningRecipe({ <MINER_COMPONENT_ID = <MINING_TICKS>, ... }),
    def _parse_mining_recipes(self):
        mining_recipes = []
        for item_id, tbl in self.items.items():
            mining_recipe = tbl["mining_recipe"]
            if not mining_recipe:
                continue
            name = self.lookup_item_name(item_id) or item_id
            miners: list[RecipeProducer] = []
            for mining_component, mining_ticks in mining_recipe.items():
                miners.append(
                    RecipeProducer(
                        readable_name=self.lookup_component_name(
                            mining_component
                        )
                        or mining_component,
                        time_seconds=tick_duration_to_seconds(mining_ticks),
                    )
                )
            mining_recipes.append(MiningRecipe(name, miners))
        logger.debug(f"Mining Recipes: {pformat(mining_recipes)}")
        return mining_recipes

    # -- Recipe of produced item
    # production_recipe = CreateProductionRecipe(
    # 	{ <INGREDIENT_ITEM_ID> = <INGREDIENT_NUM>, ... },
    # 	{ <PRODUCTION_COMPONENT_ID> = <PRODUCTION_TICKS>, }
    # 	-- Optional
    # 	<AMOUNT_NUM>, --default: 1
    # ),
    # -- Recipe of resources harvested from the world
    # mining_recipe = CreateMiningRecipe({ <MINER_COMPONENT_ID = <MINING_TICKS>, ... }),

    def _try_fix_race(self, recipe_tbl, is_derived):
        """Tries to determine the true `race` of an object.

        Args:
            recipe_tbl: Lua table of information to use
            is_derived (bool): True if this inherits from another object.

        Returns:
            _type_: _description_
        """
        race = recipe_tbl["race"]
        if not is_derived:
            return race
        shoot_fx = recipe_tbl["shoot_fx"]
        if shoot_fx and "bug" in shoot_fx:
            return "implied_bug"
        return race

    def _parse_recipe_items(self, tbl) -> list[RecipeItem]:
        ret = []
        for item_id, item_amount in tbl.items():
            name = (
                self.lookup_item_name(item_id)
                or self.lookup_component_name(item_id)
                or self.lookup_frame_name(item_id)
                or item_id
            )
            ret.append(RecipeItem(readable_name=name, amount=item_amount))
        return ret

    # TODO(maz): Make this future-proof by using lupa features to actually connect this function to code.
    # function CreateConstructionRecipe(recipe, seconds)
    #     return {
    #         items = recipe,
    #         ticks = ticks
    #     }
    # end
    def _parse_recipe_construction(
        self, ticks
    ) -> Optional[list[RecipeProducer]]:
        return [RecipeProducer("Construction", tick_duration_to_seconds(ticks))]

    # function CreateProductionRecipe(recipe, production)
    #     return {
    #         items = recipe,
    #         producers = production
    #     }
    # end
    def _parse_recipe_producers(self, tbl) -> Optional[list[RecipeProducer]]:
        if not tbl:
            return None
        ret = []
        for component_id, game_ticks in tbl.items():
            name: str = (
                self.lookup_component_name(component_id=component_id)
                or self.lookup_frame_name(component_id)
                or component_id
            )
            ret.append(
                RecipeProducer(
                    readable_name=name,
                    time_seconds=tick_duration_to_seconds(ticks=game_ticks),
                )
            )
        return ret

    def _parse_recipe_from_table(self, tbl) -> Optional[Recipe]:
        """Returns the recipe for the object a `tbl` if it has one.

        Args:
            tbl (_type_): Lua table for an object.

        Returns:
            Optional[Recipe]: Recipe for this object or else None.
        """
        # Lua table fields
        CONSTRUCTION_RECIPE = "construction_recipe"
        PRODUCTION_RECIPE = "production_recipe"
        NAME = "name"
        BASE_ID = "base_id"
        RECIPE_ITEMS = "items"
        RECIPE_PRODUCERS = "producers"
        RECIPE_CONSTRUCTION_TICKS = "ticks"

        recipe = None
        recipe_type = None
        producers: Optional[list[RecipeProducer]] = None
        if tbl[CONSTRUCTION_RECIPE]:
            recipe_type = RecipeType.Construction
            recipe = tbl[CONSTRUCTION_RECIPE]
            producers: list[RecipeProducer] = self._parse_recipe_construction(
                recipe[RECIPE_CONSTRUCTION_TICKS]
            )
        elif tbl[PRODUCTION_RECIPE]:
            recipe_type = RecipeType.Production
            recipe = tbl[PRODUCTION_RECIPE]
            producers: list[RecipeProducer] = self._parse_recipe_producers(
                recipe[RECIPE_PRODUCERS]
            )
        else:
            return None

        name: str = tbl[NAME]
        is_derived: bool = tbl[BASE_ID] is not None
        race: str = self._try_fix_race(tbl, is_derived)
        items: list[RecipeItem] = self._parse_recipe_items(recipe[RECIPE_ITEMS])
        return Recipe(
            recipe_type=recipe_type,
            race=race,
            name=name,
            items=items,
            producers=producers,
            is_derived=is_derived,
        )
