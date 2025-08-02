from models.decorators import desynced_object


@desynced_object
class CategoryFilter:
    """Categories filtering, mirroring data.categories in lua"""

    name: str
    tab: str
    # Dunno how to match this one, but we can probably get a way with a small hack later
    # defs: str
    # The field we should match for our entities
    filter_field: str
    # The value that needs to match (exact match)
    filter_val: str
    # the game relies on the order the categories are defined, we need to save that information somehow. Lower is first.
    ordering: int
