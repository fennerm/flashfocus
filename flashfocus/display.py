"""Utility code related to window management but not tied to a specific display protocol."""
from collections import namedtuple
from enum import Enum, auto


class WMEventType(Enum):
    FOCUS_SHIFT = auto()
    CLIENT_REQUEST = auto()
    NEW_WINDOW = auto()
    WINDOW_INIT = auto()


WMEvent = namedtuple("WMEvent", ["window", "event_type"])
