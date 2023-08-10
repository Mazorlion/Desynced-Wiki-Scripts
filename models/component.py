from dataclasses import dataclass
from enum import Enum

# data.components.samplecomponent = {
# 	name = "<NAME>",
# 	texture = "<PATH/TO/IMAGE.png>",
# 	-- Optional
# 	visual = "<VISUAL-ID>",
# 	slot_type = "storage|liquid|radioactive|...", -- default 'storage'
# 	attachment_size = "Hidden|Internal|Small|Medium|Large", -- default 'Hidden'
# 	activation = "None|Always|Manual|OnFirstRegisterChange|OnComponentRegisterChange|OnFirstItemSlotChange|OnComponentItemSlotChange|OnAnyItemSlotChange|OnLowPower|OnPowerStoredEmpty|OnTrustChange|OnOtherCompFinish", -- default 'None'
# 	slots = { <SLOT_TYPE> = <NUM>, ... },
# 	registers = { ... },
# 	power = -0.1,
# 	power_storage = 1000,
# 	drain_rate = 1,
# 	charge_rate = 5,
# 	bandwidth = 2,
# 	transfer_radius = 10,
# 	adjust_extra_power = true,
# 	dumping_ground = "None|Simple|Smart", -- default 'None'
# 	effect = "fx_power_core", -- automatically spawned when this components visual is placed on the map
# 	effect_socket = "fx",
# 	trigger_radius = 8, -- attack range
# 	trigger_channels = "bot|building|bug",
# 	non_removable = true,
# 	production_recipe = CreateProductionRecipe(
# 		{ <INGREDIENT_ITEM_ID> = <INGREDIENT_NUM>, ... },
# 		{ <PRODUCTION_COMPONENT_ID> = <PRODUCTION_TICKS>, }
# 		-- Optional
# 		<AMOUNT_NUM>, --default: 1
# 	),
# 	on_add = function(self, comp) ... end,
# 	on_remove = function(self, comp) ... end,
# 	on_update = function(self, comp, cause) ... end,
# 	on_trigger = function(self, comp, other_entity) ... end,
# 	on_take_damage = function(self, comp, amount) ... end,
# }


class ComponentSize(Enum):
    HIDDEN = "Hidden"
    INTERNAL = "Internal"
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"


@dataclass
class Component:
    name: str
    attachment_size: ComponentSize
    # Rate at which this will drain self storage or power grid.
    power_usage_per_second: float
    power_storage: int
    # Rate at which the component will offer power to the grid?
    drain_rate: float
    # Rate at which the component will pull excess power from the grid?
    charge_rate: float
    # Number of tiles across which it can transfer items?
    transfer_radius: int
    trigger_channels =
