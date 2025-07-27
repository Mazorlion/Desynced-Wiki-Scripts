# Fix recursive dataclass references
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Dict, Type, Union, Optional, cast

from models.decorators_options import (
    DataClassFieldOptions,
    FieldOptions,
    ListFieldOptions,
    get_field_options,
)


@dataclass
class TypeInfo:
    """Represents the type info for a field in a dataclass.

    There are three types of values:
    1) Scalar value (int, str, Enum class, etc...)
    2) List of elements of `type`
    3) Dataclass that has another set of fields inside
    """

    class Kind(Enum):
        SCALAR = 0
        LIST = 1
        DATACLASS = 2

    type: Optional[Union[Type, TypeInfo]]
    options: FieldOptions = field(default_factory=lambda: FieldOptions())
    kind: Kind = Kind.SCALAR


@dataclass
class ListTypeInfo(TypeInfo):
    list_options: ListFieldOptions = field(default_factory=lambda: ListFieldOptions())

    def __post_init__(self):
        self.kind = TypeInfo.Kind.LIST


@dataclass
class DataClassTypeInfo(TypeInfo):
    # Dictionary of field_name to TypeInfo for the field.
    fields: Dict[str, TypeInfo] = field(default_factory=lambda: {})
    dataclass_options: DataClassFieldOptions = field(default_factory=lambda: DataClassFieldOptions())

    def __post_init__(self):
        self.kind = TypeInfo.Kind.DATACLASS


def analyze_type(obj_type: Type) -> TypeInfo | DataClassTypeInfo:
    """Returns a dictionary containing fields and types for all fields in obj_type.

    Args:
        obj_type (Any): Any object

    Returns:
        Dict[str, Union[type, Dict]]: Oh god
    """
    # TODO(maz): Handle nested lists?
    if not is_dataclass(obj_type):
        return TypeInfo(type=obj_type)

    ret: DataClassTypeInfo = DataClassTypeInfo(type=None)
    for field_info in fields(obj_type):
        field_type = field_info.type
    
        if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
            list_field = ListTypeInfo(analyze_type(field_type.__args__[0]))
            list_field.list_options = cast(ListFieldOptions, get_field_options(f=field_info))
            # TODO(maz): Set max_length metadata dynamically by looking at actual game objects.
            assert (
                list_field.list_options.max_length
            ), f"{field_info.name} in {obj_type} is missing max_length"
            ret.fields[field_info.name] = list_field
        elif is_dataclass(field_type):
            field_type = cast(Type, field_type)
            dataclass_field: DataClassTypeInfo = cast(DataClassTypeInfo, analyze_type(field_type))
            dataclass_field.dataclass_options = cast(DataClassFieldOptions, get_field_options(f=field_info))
            ret.fields[field_info.name] = dataclass_field

        else:
            ret.fields[field_info.name] = TypeInfo(
                type=field_type, options=cast(FieldOptions, get_field_options(field_info))
            )

    return ret
