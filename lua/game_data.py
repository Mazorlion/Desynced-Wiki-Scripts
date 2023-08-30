import logging
import os
from typing import List, Optional

from lupa import LuaRuntime

from lua.lua_util import tick_duration_to_seconds, ticks_to_seconds
from models.component import Component, PowerStats, Register, WeaponStats
from models.entity import Entity, EntityType, SlotType
from models.instructions import ArgType, Instruction, InstructionArg
from models.item import Item, ItemSlotType, ItemType, MiningRecipe
from models.recipe import Recipe, RecipeItem, RecipeProducer, RecipeType
from models.sockets import Sockets, SocketSize
from models.tech import Technology, TechnologyCategory, TechnologyUnlock
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
        self.data = self.globals().data
        self.frames = self.data.frames
        self.components = self._parse_components()
        self.items = self._parse_items()
        self.entities: list[Entity] = self._parse_entities()
        self.instructions: List[Instruction] = self._parse_instructions()
        self.tech_unlocks: List[TechnologyUnlock] = []
        self.technologies = self._parse_technologies()
        self.technology_categories = self._parse_technology_categories()

    def _parse_technology_categories(self) -> List[TechnologyCategory]:
        categories: List[TechnologyCategory] = []
        for _, cat in self.data.tech_categories.items():
            sub_cats: List[str] = []
            for _, sub_cat in cat["sub_categories"].items():
                sub_cats.append(sub_cat)
            categories.append(
                TechnologyCategory(
                    name=cat["name"],
                    discovery_tech=self.lookup_tech_name(cat["discovery_tech"]),
                    initial_tech=self.lookup_tech_name(cat["initial_tech"]),
                    sub_categories=sub_cats,
                    texture=(
                        os.path.basename(cat["texture"]) if cat["texture"] else None
                    ),
                )
            )
        return categories

    def _parse_technologies(self) -> List[Technology]:
        techs: List[Technology] = []
        for _, tech in self.data.techs.items():
            required_techs = []
            if tech["require_tech"]:
                for _, req in tech["require_tech"].items():
                    required_techs.append(self.lookup_tech_name(req))
            if tech["unlocks"]:
                for _, unlock in tech["unlocks"].items():
                    if unlock and self.lookup_name(unlock):
                        self.tech_unlocks.append(
                            TechnologyUnlock(
                                name=tech["name"] + "_" + self.lookup_name(unlock),
                                tech_name=tech["name"],
                                unlocks=self.lookup_name(unlock),
                            )
                        )
            techs.append(
                Technology(
                    name=tech["name"],
                    description=tech["description"],
                    category=tech["category"],
                    texture=(
                        os.path.basename(tech["texture"]) if tech["texture"] else None
                    ),
                    required_tech=required_techs,
                    progress_count=tech["progress_count"],
                    uplink_recipe=self._parse_recipe_from_table(tech),
                )
            )
        return techs

    def _parse_instructions(self) -> List[Instruction]:
        instructions = []

        for instruction_id, ins in self.data.instructions.items():
            args: List[InstructionArg] = []
            if ins["args"]:
                for _, arg_tbl in ins["args"].items():
                    args.append(
                        InstructionArg(
                            type=ArgType[arg_tbl[1].upper()],
                            name=arg_tbl[2],
                            description=arg_tbl[3],
                            data_type=arg_tbl[4],
                        )
                    )
            instructions.append(
                Instruction(
                    name=ins["name"] or instruction_id,
                    description=ins["desc"],
                    category=ins["category"],
                    icon=os.path.basename(ins["icon"]),
                    args=args,
                )
            )

        return instructions

    def _parse_components(self):
        components = []

        for _, c_tbl in self.data.components.items():
            registers: List[Register] = []
            if c_tbl["registers"]:
                for register in c_tbl["registers"].values():
                    registers.append(
                        Register(
                            type=register["type"],
                            tip=register["tip"],
                            ui_apply=register["ui_apply"],
                        )
                    )
            power_stats: PowerStats = PowerStats(
                power_storage=c_tbl["power_storage"],
                drain_rate=c_tbl["drain_rate"],
                charge_rate=c_tbl["charge_rate"],
                bandwidth=c_tbl["bandwidth"],
                affected_by_events=c_tbl["adjust_extra_power"],
            )

            weapon_stats: WeaponStats = WeaponStats(
                damage=c_tbl["damage"],
                charge_duration_sec=tick_duration_to_seconds(c_tbl["duration"]),
                projectile_delay_sec=tick_duration_to_seconds(c_tbl["shoot_speed"]),
                splash_range=c_tbl["blast"],
            )

            components.append(
                Component(
                    name=c_tbl["name"],
                    attachment_size=(
                        SocketSize[c_tbl["attachment_size"].upper()]
                        if c_tbl["attachment_size"]
                        else None
                    ),
                    power_usage_per_second=ticks_to_seconds(c_tbl["power"]),
                    power_stats=power_stats,
                    transfer_radius=c_tbl["transfer_radius"],
                    activation_radius=c_tbl["activation_radius"],
                    register=registers,
                    production_recipe=self._parse_recipe_from_table(c_tbl),
                    is_removable=False if c_tbl["non_removable"] else True,
                    weapon_stats=weapon_stats,
                )
            )

        return components

    def _parse_mining_recipes(self, item) -> Optional[List[MiningRecipe]]:
        if not item or not item["mining_recipe"]:
            return None

        ret = []
        for component_id, mining_ticks in item["mining_recipe"].items():
            c_name = self.lookup_component_name(component_id)
            mining_seconds = tick_duration_to_seconds(mining_ticks)
            ret.append(MiningRecipe(c_name, mining_seconds))

        return ret

    def _parse_items(self) -> list[Item]:
        items = []

        for _, item in self.data["items"].items():
            recipe = self._parse_recipe_from_table(item)
            items.append(
                Item(
                    name=item["name"],
                    description=item["desc"],
                    type=ItemType[item["tag"].upper()],
                    slot_type=ItemSlotType[item["slot_type"].upper()],
                    production_recipe=recipe,
                    mining_recipes=self._parse_mining_recipes(item),
                    stack_size=item["stack_size"],
                )
            )

        return items

    def _parse_entities(self):
        entities: list[Entity] = []
        for frame, frame_tbl in self.frames.items():
            # Skip frames that don't have visuals
            visual_key = frame_tbl["visual"]
            if not visual_key:
                logger.debug("Skipping %s due to missing visual table.", frame)
                continue
            # Map to visuals
            visual_tbl = self.lookup_visual(visual_key)
            if not visual_tbl:
                logger.debug("Skipping %s due to missing visual table.", frame)
                continue

            if not visual_tbl["sockets"]:
                continue

            sockets: Sockets = Sockets()
            for _, socket in visual_tbl["sockets"].items():
                sockets.increment_socket(socket[2])

            types = []
            if frame_tbl["trigger_channels"]:
                for channel_type in frame_tbl["trigger_channels"].split("|"):
                    types.append(EntityType[channel_type.upper()])

            recipe = self._parse_recipe_from_table(frame_tbl)

            entities.append(
                Entity(
                    name=frame_tbl["name"],
                    health=frame_tbl["health_points"],
                    power_usage_per_second=(
                        ticks_to_seconds(frame_tbl["power"])
                        if frame_tbl["power"]
                        else 0
                    ),
                    movement_speed=frame_tbl["movement_speed"],
                    visibility=frame_tbl["visibility_range"],
                    storage=frame_tbl["slots"]["storage"] if frame_tbl["slots"] else 0,
                    size=frame_tbl["size"],
                    race=Race[frame_tbl["race"].upper()] if frame_tbl["race"] else "",
                    types=types,
                    sockets=sockets,
                    slot_type=(
                        SlotType[frame_tbl["slot_type"].upper()]
                        if frame_tbl["slot_type"]
                        else SlotType.NONE
                    ),
                    recipe=recipe,
                )
            )

        return entities

    def data_lookup(self, field: str, name: str):
        """Shortcut for accessing `data` fields with error handling.

        Args:
            field (str): Field in `data` to access.
            name (str): Entry in `data[field]` to return.

        Returns:
            Any | None: Returns the object found or else None.
        """
        try:
            return self.data[field][name]
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
            Optional[str]: Name of the frame or None if not found.
        """
        item = self.data_lookup("frames", frame_id)
        if item:
            return item["name"]
        return None

    def lookup_tech_name(self, tech_id: str) -> Optional[str]:
        """Returns the `name` for the corresponding `tech_id`.

        Args:
            tech_id (str): Lua ID of the tech to look up.

        Returns:
            Optional[str]: Name of the tech or None if not found.
        """
        item = self.data_lookup("techs", tech_id)
        if item:
            return item["name"]
        return None

    def lookup_name(self, object_id: str) -> Optional[str]:
        return (
            self.lookup_component_name(object_id)
            or self.lookup_frame_name(object_id)
            or self.lookup_item_name(object_id)
            or self.lookup_tech_name(object_id)
            or None
        )

    def lookup_visual(self, name: str):
        return self.data_lookup("visuals", name)

    def globals(self):
        return self.lua.globals()

    # TODO(maz): Make this future-proof by using lupa features to actually connect this function to code.
    # function CreateConstructionRecipe(recipe, seconds)
    #     return {
    #         items = recipe,
    #         ticks = ticks
    #     }
    # end
    def _parse_recipe_construction(self, ticks) -> Optional[list[RecipeProducer]]:
        return [RecipeProducer("Construction", tick_duration_to_seconds(ticks))]

    def _parse_recipe_uplink(self, ticks) -> Optional[list[RecipeProducer]]:
        return [RecipeProducer("Uplink", tick_duration_to_seconds(ticks))]

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
                    name,
                    tick_duration_to_seconds(ticks=game_ticks),
                )
            )
        return ret

    def _parse_recipe_items(self, tbl) -> list[RecipeItem]:
        ret = []
        for item_id, item_amount in tbl.items():
            name = (
                self.lookup_item_name(item_id)
                or self.lookup_component_name(item_id)
                or self.lookup_frame_name(item_id)
                or item_id
            )
            ret.append(RecipeItem(name, item_amount))
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
        UPLINK_RECIPE = "uplink_recipe"
        RECIPE_ITEMS = "items"
        RECIPE_PRODUCERS = "producers"
        RECIPE_CONSTRUCTION_TICKS = "ticks"

        recipe = None
        recipe_type = None
        producers: Optional[list[RecipeProducer]] = None
        num_produced: int = 1
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
            num_produced = recipe["num_produced"]
        elif tbl[UPLINK_RECIPE]:
            recipe_type = RecipeType.Uplink
            recipe = tbl[UPLINK_RECIPE]
            producers: list[RecipeProducer] = self._parse_recipe_uplink(
                recipe[RECIPE_CONSTRUCTION_TICKS]
            )

        else:
            return None

        items: list[RecipeItem] = self._parse_recipe_items(recipe[RECIPE_ITEMS])
        return Recipe(
            items=items,
            producers=producers,
            recipe_type=recipe_type,
            num_produced=num_produced,
        )
