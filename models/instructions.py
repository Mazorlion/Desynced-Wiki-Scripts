from enum import Enum
from typing import List

from models.decorators import desynced_object
from models.decorators_options import DataClassFieldOptions, ListFieldOptions, annotate


class ArgType(Enum):
    IN = "Input"
    OUT = "Output"
    EXEC = "Exec"


@desynced_object
class InstructionArg:
    type: ArgType
    name: str
    description: str
    data_type: str


@desynced_object
class Instruction:
    name: str
    description: str
    category: str
    # Filename of the icon (no path).
    icon: str
    args: List[InstructionArg] = annotate(
        ListFieldOptions(
            max_length=7,
            dataclass_options=DataClassFieldOptions(prefix_name=True),
        )
    )
