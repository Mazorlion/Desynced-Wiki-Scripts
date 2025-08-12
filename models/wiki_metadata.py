from models.decorators import desynced_object


@desynced_object
class WikiMetadata:
    """Extra shared metadata"""

    unlockable: bool = False
