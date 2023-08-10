from enum import Enum


class Race(Enum):
    ROBOT = "Robot"
    ALIEN = "Alien"
    BUG = "Bug"
    HUMAN = "Human"


class ItemType(Enum):
    COMPONENT = "Component"
    RESOURCE = "Resource"
    MATERIAL = "Material"
    RESEARCH = "Research"
    PACKAGE = "Package"


class MaterialType(Enum):
    SIMPLE = "Simple"
    ADVANCED = "Advanced"
    HIGH_TECH = "High-Tech"


class UnitType(Enum):
    BOT = "Bot"
    ALIEN = "Alien"
    BUG = "Bug"
    HUMAN = "Human"
    SPACE = "Space"
