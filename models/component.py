from enum import Enum
from typing import List

from models.decorators import DesyncedObject, desynced_object
from models.decorators_options import (
    DataClassFieldOptions,
    FieldOptions,
    ListFieldOptions,
    annotate,
)
from models.recipe import Recipe
from models.sockets import SocketSize


class ComponentSize(Enum):
    HIDDEN = "Hidden"
    INTERNAL = "Internal"
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"


# Unused unless there's a reason for it.
class ComponentActivation(Enum):
    # Requires manual activation (deployer)
    MANUAL = "Manual"
    # Activates on register change (miner)
    ONFIRSTREGISTERCHANGE = "OnFirstRegisterChange"
    # Always active (repair kit)
    ALWAYS = "Always"


@desynced_object
class Register:
    type: str
    # Tooltip of the register.
    tip: str
    ui_apply: str


@desynced_object
class PowerStats:
    power_storage: int
    # Rate at which the component will offer power to the grid?
    drain_rate: float
    # Rate at which the component will pull excess power from the grid?
    charge_rate: float
    # For power trasmission components, the rate of power transfer
    bandwidth: float
    # Is this affected by events like day/night or blight storms? (ex. solar panel)
    affected_by_events: bool
    # Power generated per second during day.
    solar_power_generated: int


@desynced_object
class WeaponStats:
    damage: int
    # Charge time of the weapon
    charge_duration_sec: float
    # Delay between shooting and hitting.
    projectile_delay_sec: float
    # Splash radius of the hit.
    splash_range: int
    #
    damage_type: str
    #
    extra_effect_name: str
    #
    disruptor: int


@desynced_object
class Component(DesyncedObject):
    name: str
    # ID of the component in lua.
    lua_id: str
    description: str
    # Socket size this component consumes
    attachment_size: SocketSize
    # Rate at which this will drain self storage or power grid.
    power_usage_per_second: int
    power_stats: PowerStats
    # Number of tiles across which it can transfer items?
    transfer_radius: int
    # Range in which this can activate (attack range for weapons)
    trigger_radius: int
    # Range for things like radars and transporters.
    # Cannot be named `range` because it's a SQL keyword
    range: int = annotate(FieldOptions(name_override="component_range"))
    # Maximum range at which the radar will visibly reveal a scanned object.
    radar_show_range: int
    # List of available registers
    register: List[Register] = annotate(
        ListFieldOptions(
            max_length=5,
            dataclass_options=DataClassFieldOptions(prefix_name=True),
        )
    )
    # Recipe is always production for components
    production_recipe: Recipe
    # Is this component removable?
    is_removable: bool
    # If the component is a weapon, describes the weapon stats.
    weapon_stats: WeaponStats
    # Number of seconds for extraction (ex. blight gas)
    extraction_time: float
    # For uplink derived components
    uplink_rate = float
