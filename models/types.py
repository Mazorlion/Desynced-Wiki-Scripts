from enum import Enum


class Race(Enum):
    ROBOT = "Robot"
    ALIEN = "Alien"
    BUG = "Bug"
    HUMAN = "Human"
    VIRUS = "Virus"
    BLIGHT = "Blight"


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
