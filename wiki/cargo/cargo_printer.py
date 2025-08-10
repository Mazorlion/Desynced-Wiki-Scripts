import re
from collections import Counter
from enum import Enum
from typing import Any, List, Type

from wiki.cargo.analyze_type import DataClassTypeInfo, ListTypeInfo, TypeInfo


class CargoPrinter:
    class Mode(Enum):
        DATA = 0
        DECLARATIONS = 1
        TEMPLATE = 2

    def __init__(self, mode: Mode = Mode.DATA):
        self.mode = mode

    def _print_list(
        self,
        value: list,
        field_type: ListTypeInfo,
        field_name: str,
        suffix: str = "",
    ):
        result = []
        item_info = field_type.type
        max_length = field_type.list_options.max_length
        assert max_length, f"{field_type} is missing max_length"
        skip_suffix: bool = field_type.list_options.skip_suffix
        if item_info.kind == TypeInfo.Kind.DATACLASS:
            item_info.dataclass_options = field_type.list_options.dataclass_options

        if value:
            assert len(value) <= max_length, (
                f"{field_type} max_length is too short. Is {max_length}, need"
                f" {len(value)}.\n List: {value}"
            )

        for idx in range(max_length):
            result.extend(
                self._print_field(
                    field_name=field_name,
                    obj=value[idx] if value and len(value) > idx else None,
                    field_type=item_info,
                    suffix=f"{suffix}{'' if skip_suffix else idx + 1 }",
                )
            )
        return result

    def _print_field(
        self,
        field_name: str,
        obj: Any,
        field_type: TypeInfo,
        suffix: str = "",
    ) -> List[str]:
        if field_type.options.skip_field:
            return []

        if field_type.options.name_override:
            field_name = field_type.options.name_override

        if field_type.kind == TypeInfo.Kind.LIST:
            return self._print_list(
                value=obj,
                field_type=field_type,
                field_name=field_name,
                suffix=suffix,
            )

        if field_type.kind == TypeInfo.Kind.DATACLASS:
            return self.print_dataclass(
                dc_obj=obj,
                type_info=field_type,
                top_level_field_name=field_name,
                suffix=suffix,
            )

        if isinstance(field_type.type, TypeInfo):
            field_type = field_type.type

        if self.mode == self.Mode.DECLARATIONS:
            return self._print_field_declaration(
                field_name=field_name, field_type=field_type, suffix=suffix
            )

        if self.mode == self.Mode.TEMPLATE:
            return [
                f"|{field_name}{suffix} = "
                + "{{{"
                + f"{self.to_camel_case(field_name + suffix)}"
                + "|}}}"
            ]

        if isinstance(field_type.type, type) and issubclass(field_type.type, Enum):
            return [f"|{field_name}{suffix} = {obj.value if obj else ''}"]

        return [f"|{field_name}{suffix} = {obj or ''}"]

    def _transform_type(self, raw_type: Type) -> str:
        mapping: dict[Type, str] = {
            int: "Integer",
            str: "String",
            float: "Float",
            bool: "Boolean",
        }
        return mapping[raw_type]

    def _print_field_declaration(
        self, field_name: str, field_type: TypeInfo, suffix: str = ""
    ) -> List[str]:
        if isinstance(field_type.type, type) and issubclass(field_type.type, Enum):
            return [
                f"|{field_name}{suffix} = String (allowed"
                f" values={','.join(list(map(lambda x: x.value, field_type.type.__members__.values())))})"
            ]

        return [f"|{field_name}{suffix} = {self._transform_type(field_type.type)}"]

    def print_dataclass(
        self,
        dc_obj: Any,
        type_info: DataClassTypeInfo,
        top_level_field_name: str = "",
        suffix: str = "",
    ) -> List[str]:
        result = []

        prefix = ""
        if type_info.dataclass_options.prefix_name:
            prefix = type_info.dataclass_options.name_override or top_level_field_name
            if len(prefix) > 0:
                prefix += "_"
        for field_name, field_type in type_info.fields.items():
            value = getattr(dc_obj, field_name, None)
            result.extend(
                self._print_field(
                    field_name=f"{prefix}{field_name}",
                    obj=value,
                    field_type=field_type,
                    suffix=suffix,
                )
            )

        # Validate no duplicates
        # TODO(maz) move this out?
        result = [self.transform_line(line) for line in result]
        keys = map(lambda line: re.findall(r"\|([^ ]+) =", line)[0], result)
        duplicates = [item for item, count in Counter(keys).items() if count > 1]
        assert not len(duplicates), f"{result} for {type_info} found {duplicates}"
        return result

    @staticmethod
    def to_camel_case(name: str) -> str:
        parts = name.split("_")
        # Keep the first word in lowercase and capitalize the rest
        return parts[0] + "".join(part.capitalize() for part in parts[1:])

    @staticmethod
    def transform_line(line: str) -> str:
        # Match the pattern "|{variable} ="
        match = re.search(r"\|(\w+) =", line)
        if not match:
            return line  # If the line doesn't match the pattern, return it unchanged

        variable_name = match.group(1)
        camel_name = CargoPrinter.to_camel_case(variable_name)
        # Replace the original variable name with its CamelCase version
        transformed_line = line.replace(f"|{variable_name} =", f"|{camel_name} =", 1)
        return transformed_line
