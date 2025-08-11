from enum import Enum
from typing import List

from models.decorators import desynced_object
from models.decorators_options import DataClassFieldOptions, ListFieldOptions, annotate


class ArgType(Enum):
    IN = "Input"
    OUT = "Output"
    EXEC = "Exec"
    TARGET = "Target"


@desynced_object
class InstructionArg:
    type: ArgType
    name: str
    description: str
    data_type: str


@desynced_object
class Instruction:
    name: str
    lua_id: str
    description: str
    category: str
    # Filename of the icon (no path).
    icon: str
    explaination: str

    args: List[InstructionArg] = annotate(
        ListFieldOptions(
            max_length=11,
            dataclass_options=DataClassFieldOptions(prefix_name=True),
        )
    )
