import collections
from dataclasses import dataclass
import logging
import os
from typing import Dict, List, Optional

from lupa import LuaRuntime  # pylint: disable=no-name-in-module

from lua.lua_util import tick_duration_to_seconds, per_tick_to_per_second
from models.component import Component, PowerStats, Register, WeaponStats
from models.entity import Entity, EntityType, SlotType
from models.instructions import ArgType, Instruction, InstructionArg
from models.item import Item, ItemSlotType, ItemType, MiningRecipe
from models.recipe import Recipe, RecipeItem, RecipeProducer, RecipeType
from models.sockets import Sockets, SocketSize
from models.tech import (
    Technology,
    TechnologyCategory,
    TechnologyUnlock,
)
from models.types import Race
from util.constants import FORCE_INCLUDE_NAMES
from wiki.wiki_name_overrides import get_name_override

logger = logging.getLogger()


class GameData:
    """Encapsulates the exploration of a lua runtime that has evaluated the game files for Desynced.

    TODO(maz): Clean this up for real :<

    Example Usage:

        lua = lupa.LuaRuntime()
        lua.execute(...)
        data = GameData(lua)
    """

    unlockable_names: set[str] = set()

    def __init__(self, lua: LuaRuntime):
        self.lua: LuaRuntime = lua
        self.data = self.globals().data  # type: ignore
        self._apply_renames()  # before everything else
        self.frames = self.data.frames
        self.components: List[Component] = self._parse_components()
        self.items: list[Item] = self._parse_items()
        self.entities: list[Entity] = self._parse_entities()
        self.instructions: List[Instruction] = self._parse_instructions()
        self.tech_unlocks: List[TechnologyUnlock] = []
        self.technologies: List[Technology] = self._parse_technologies()
        self.technology_categories: List[TechnologyCategory] = (
            self._parse_technology_categories()
        )

    def _apply_renames(self):
        def apply_overrides(collection):
            for obj_id, obj in collection.items():
                if override := get_name_override(obj_id):
                    obj["name"] = override

        apply_overrides(self.data.components)
        apply_overrides(self.data["items"])
        apply_overrides(self.data.frames)

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

    SEED_TECHS = ["t_assembly", "t_robot_tech_basic"]

    def _parse_technologies(self) -> List[Technology]:
        # Return list of tech objects.
        techs: List[Technology] = []
        # Tech Lua ID to Lua ID of techs it unlocks.
        tech_id_to_unlocked_tech_ids: Dict[str, List[str]] = {}
        # Lua ID of technology to object (non-tech) lua IDs.
        tech_id_to_unlock_id: Dict[str, List[str]] = {}

        @dataclass
        class TechNode:
            # Lua ID.
            id: str
            # Research category.
            category: str

        queue: collections.deque[TechNode] = collections.deque()
        for _, cat in self.data.tech_categories.items():
            if cat["initial_tech"]:
                queue.append(TechNode(cat["initial_tech"], cat.name))
            if cat["discovery_tech"]:
                queue.append(TechNode(cat["discovery_tech"], cat.name))

        for technology_id, tech in self.data.techs.items():
            # Process previously required technologies.
            required_techs = []
            if tech["require_tech"]:
                # Build a tree of the inverse of requirement: which techs unlock which.
                for _, req in tech["require_tech"].items():
                    tech_id_to_unlocked_tech_ids.setdefault(req, []).append(
                        technology_id
                    )
                    required_techs.append(self.lookup_tech_name(req))
            elif technology_id in self.SEED_TECHS:
                # Seed our queue with the root techs.
                # Robot isn't properly set on the category.
                queue.append(TechNode(technology_id, "Robot"))

            # Process unlocked objects (non-techs).
            if tech["unlocks"]:
                # Keep track of unlocks by object ID.
                unlocked_ids = tech_id_to_unlock_id.setdefault(technology_id, [])
                for _, unlock_id in tech["unlocks"].items():
                    unlocked_ids.append(unlock_id)
                    if unlock_id:
                        # Skip hidden components unlocks
                        if comp := self.data_lookup("components", unlock_id):
                            if comp["attachment_size"] == "Hidden":
                                continue

                        if unlocked_name := self.lookup_name(unlock_id):
                            self.tech_unlocks.append(
                                TechnologyUnlock(
                                    name=f"{tech['name']}_{unlocked_name}",
                                    tech_name=tech["name"],
                                    unlocks=unlocked_name,
                                )
                            )
            techs.append(
                Technology(
                    name=tech["name"],
                    lua_id=technology_id,
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

        while len(queue) > 0:
            current_node: TechNode = queue.popleft()
            # Traverse the tree and ad child techs for future processing.
            for unlocked_tech_id in tech_id_to_unlocked_tech_ids.get(
                current_node.id, []
            ):
                queue.append(TechNode(unlocked_tech_id, current_node.category))

            # Categorize the things we unlock at this node.
            for unlocked_object_id in tech_id_to_unlock_id.get(current_node.id, []):
                unlock_name = self.lookup_name(unlocked_object_id)
                # Skip codex entries, menus, visuals, etc...
                if not unlock_name:
                    continue

                self.unlockable_names.add(unlock_name)

        self.unlockable_names.update(FORCE_INCLUDE_NAMES)
        return techs

    def _parse_instructions(self) -> List[Instruction]:
        instructions = []

        for instruction_id, ins in self.data.instructions.items():
            args: List[InstructionArg] = []
            if ins["args"]:
                for _, arg_tbl in ins["args"].items():
                    type = arg_tbl[1].upper()
                    name = arg_tbl[2]
                    description = arg_tbl[3]
                    data_type = arg_tbl[4]
                    args.append(
                        InstructionArg(
                            type=ArgType[type],
                            name=name,
                            description=description,
                            data_type=data_type,
                        )
                    )
            instructions.append(
                Instruction(
                    lua_id=instruction_id,
                    name=ins["name"] or instruction_id,
                    description=ins["desc"],
                    category=ins["category"],
                    icon=os.path.basename(ins["icon"]),
                    args=args,
                    explaination=ins["explain"] or "",
                )
            )

        return instructions

    def _parse_components(self):
        components = []

        for component_id, c_tbl in self.data.components.items():
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
                drain_rate=per_tick_to_per_second(c_tbl["drain_rate"]),
                charge_rate=per_tick_to_per_second(c_tbl["charge_rate"]),
                bandwidth=per_tick_to_per_second(c_tbl["bandwidth"]),
                affected_by_events=c_tbl["adjust_extra_power"],
                solar_power_generated=per_tick_to_per_second(
                    c_tbl["solar_power_generated"]
                ),
            )

            weapon_stats: WeaponStats = WeaponStats(
                damage=c_tbl["damage"],
                charge_duration_sec=tick_duration_to_seconds(c_tbl["duration"]),
                projectile_delay_sec=tick_duration_to_seconds(c_tbl["shoot_speed"]),
                splash_range=c_tbl["blast"],
                damage_type=c_tbl["damage_type"],
                extra_effect_name=c_tbl["extra_effect_name"],
                disruptor=c_tbl["disruptor"],
            )

            components.append(
                Component(
                    lua_id=component_id,
                    name=c_tbl["name"],
                    description=c_tbl["desc"],
                    attachment_size=(
                        SocketSize[c_tbl["attachment_size"].upper()]
                        if c_tbl["attachment_size"]
                        else None
                    ),
                    power_usage_per_second=per_tick_to_per_second(c_tbl["power"]),
                    power_stats=power_stats,
                    transfer_radius=c_tbl["transfer_radius"],
                    trigger_radius=c_tbl["trigger_radius"],
                    range=c_tbl["range"],
                    radar_show_range=c_tbl["radar_show_range"],
                    register=registers,
                    production_recipe=self._parse_recipe_from_table(c_tbl),
                    is_removable=False if c_tbl["non_removable"] else True,
                    weapon_stats=weapon_stats,
                    extraction_time=tick_duration_to_seconds(c_tbl["extraction_time"]),
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

        for item_id, item in self.data["items"].items():
            recipe = self._parse_recipe_from_table(item)
            items.append(
                Item(
                    lua_id=item_id,
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
        for frame_id, frame_tbl in self.frames.items():
            # Skip frames that don't have visuals
            visual_key = frame_tbl["visual"]
            if not visual_key:
                logger.debug(f"Skipping {frame_id} due to missing visual table.")
                continue
            # Map to visuals
            visual_tbl = self.lookup_visual(visual_key)
            if not visual_tbl:
                logger.debug(f"Skipping {frame_id} due to missing visual table.")
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

            name = frame_tbl["name"]  # "Transport Bot"

            entities.append(
                Entity(
                    lua_id=frame_id,
                    name=frame_tbl["name"],
                    description=frame_tbl["desc"],
                    health=frame_tbl["health_points"],
                    power_usage_per_second=(
                        per_tick_to_per_second(frame_tbl["power"])
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
    def _parse_recipe_construction(self, ticks) -> list[RecipeProducer]:
        return [RecipeProducer("Construction", tick_duration_to_seconds(ticks))]

    def _parse_recipe_uplink(self, ticks) -> list[RecipeProducer]:
        return [RecipeProducer("Uplink", tick_duration_to_seconds(ticks))]

    # function CreateProductionRecipe(recipe, production)
    #     return {
    #         items = recipe,
    #         producers = production
    #     }
    # end
    def _parse_recipe_producers(self, tbl) -> list[RecipeProducer]:
        if not tbl:
            return []

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
        # producers: Optional[list[RecipeProducer]]
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
