from collections import namedtuple
from enum import auto, Enum


class WMError(ValueError):
    """An error related to an Xorg window."""

    pass


class WMMessageType(Enum):
    FOCUS_SHIFT = auto()
    CLIENT_REQUEST = auto()
    NEW_WINDOW = auto()
    WINDOW_INIT = auto()


WMMessage = namedtuple("WMMessage", ["window", "type"])
