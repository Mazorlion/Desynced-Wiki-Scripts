from dataclasses import Field, dataclass, field, fields, is_dataclass
from typing import Optional, Type, Any


@dataclass
class FieldOptions:
    # If not empty, overrides all rules that use the field name to this value.
    name_override: str = ""
    # If true, don't include this field at all in the cargo definition or storage.
    skip_field: bool = False


@dataclass
class DataClassFieldOptions(FieldOptions):
    # If true, prefixes all fields in this dataclass with the dataclass field name.
    prefix_name: bool = False


@dataclass
class ListFieldOptions(FieldOptions):
    # Max length of the field to export to the wiki.
    # If the length of the annotated field is shorter, `max_length` items are
    # still exported (though blank past the end of the list).
    max_length: int = -1
    # If true, the items in this list will not be numbered.
    skip_suffix: bool = False
    # If the element in a list is a dataclass, should the name be prefixed.
    dataclass_options: DataClassFieldOptions = field(
        default_factory=lambda: DataClassFieldOptions()
    )


def annotate(options: FieldOptions) -> Any:
    """Shortcut for setting options in the metadata in a known location.

    Returns:
        Any: A field that has the options set in the metadata.
    """
    return field(  # pylint: disable=invalid-field-call
        metadata={"desynced_field_options": options}
    )


def get_field_options(
    f: Field,
) -> Optional[ListFieldOptions | DataClassFieldOptions | FieldOptions]:
    """Retrive the field annotations if they exist.

    Args:
        f (Field): Field to get options from.

    Returns:
        FieldOptions: Options of the field or None.
    """
    if "desynced_field_options" not in f.metadata:
        if isinstance(f.type, type) and issubclass(f.type, list):
            return ListFieldOptions()
        elif isinstance(f.type, type) and is_dataclass(f.type):
            return DataClassFieldOptions()
        else:
            return FieldOptions()

    return f.metadata["desynced_field_options"]


def require_field_options(cls: Type) -> Type:
    """Requires that all lists in `cls` have options set.

    This is necessary to have max_length available.

    Args:
        cls (Type): Type to check.

    Raises:
        ValueError: If there is a List field in cls that does not have options.

    Returns:
        Type: `cls` from input, no changes.
    """
    for f in fields(class_or_instance=cls):
        if hasattr(f.type, "__origin__") and f.type.__origin__ is list:
            if "desynced_field_options" not in f.metadata:
                raise ValueError(f"'{f.name}' in {cls} must have ListFieldOptions set.")
            if not isinstance(f.metadata["desynced_field_options"], ListFieldOptions):
                raise ValueError(
                    f"'{f.name}' in {cls} must have ListFieldOptions set but instead"
                    " has something else."
                )

            max_length: int = f.metadata["desynced_field_options"].max_length
            if max_length <= 0:
                raise ValueError(
                    f"'{f.name}' in {cls} must have max_length >0 has a max_length of"
                    f" {max_length}"
                )

    return cls
