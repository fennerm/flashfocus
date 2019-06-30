from dataclasses import dataclass
from enum import auto, Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flashfocus.compat import Window


class WMError(ValueError):
    """An error related to an Xorg window."""

    pass


class WMMessageType(Enum):
    FOCUS_SHIFT = auto()
    CLIENT_REQUEST = auto()
    NEW_WINDOW = auto()
    WINDOW_INIT = auto()


@dataclass
class WMMessage:
    window: "Window"
    type: WMMessageType
