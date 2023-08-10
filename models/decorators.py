from dataclasses import dataclass
from typing import Optional, Type

from models.decorators_options import require_field_options


def desynced_object(cls: Type) -> Type:
    """@desynced_object is a dataclass with some validation.

    Args:
        cls (Type): Class to wrap (passed by decoration).

    Returns:
        Type: Returnes the wrapped class.
    """
    return require_field_options(dataclass(cls))


def length_check(cls) -> Type:
    """Validates that any annotated list field does not have more its max length.

    Used as a decorator @length_check.

    Raises:
        ValueError: If any list field exceeds its max length.

    Returns:
        Type: Decorated class.
    """
    orig_post_init = (
        cls.__post_init__ if hasattr(cls, "__post_init__") else lambda self: None
    )

    def new_post_init(self):
        orig_post_init(self)
        for field_name, field_info in self.__dataclass_fields__.items():
            value = getattr(self, field_name)
            max_length = field_info.metadata.get("max_length")
            if max_length and len(value) > max_length:
                raise ValueError(
                    f"The list length for '{field_name}' must not exceed {max_length}."
                )

    cls.__post_init__ = new_post_init
    return cls


# To check the max length of a given field:
def get_max_length(
    dataclass_instance: desynced_object, field_name: str
) -> Optional[int]:
    """Utility function for getting the max length of a field.

    Args:
        dataclass_instance (desynced_object): Class to get the field from
        field_name (str): Name of the field to retrieve

    Returns:
        Optional[int]: Max length if set, None otherwise.
    """
    field_info = dataclass_instance.__dataclass_fields__.get(field_name)
    if field_info and "max_length" in field_info.metadata:
        return field_info.metadata["max_length"]
    return None
