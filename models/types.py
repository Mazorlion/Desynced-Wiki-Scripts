"""File for hosting enums and types shared across many different objects."""
from enum import Enum


class Race(Enum):
    ROBOT = "Robot"
    ALIEN = "Alien"
    BUG = "Bug"
    HUMAN = "Human"
    VIRUS = "Virus"
    BLIGHT = "Blight"
    ANOMALY = "Anomaly"
