"""Utility code related to window management but not tied to a specific display protocol."""

from __future__ import annotations
from abc import ABC, abstractmethod
from collections import namedtuple
from enum import Enum, auto
from typing import Any
from collections.abc import Mapping

from flashfocus.errors import WMError


class WMEventType(Enum):
    FOCUS_SHIFT = auto()
    CLIENT_REQUEST = auto()
    NEW_WINDOW = auto()
    WINDOW_INIT = auto()


WMEvent = namedtuple("WMEvent", ["window", "event_type"])


class BaseWindow(ABC):
    """Abstract base class for a window.

    Contains any logic which isn't specifically tied to wayland/X11.
    """

    def __init__(self, window_id: int) -> None:
        if window_id is None:
            raise WMError("Invalid window ID")
        self.id = window_id

    @property
    @abstractmethod
    def properties(self) -> dict:
        """A dictionary containing misc. properties of the window (e.g the name/class)."""
        pass

    def __eq__(self, other: Any) -> bool:
        """Window equality is determined by the unique identifier."""
        if not isinstance(other, BaseWindow):
            raise TypeError(f"== not defined for {type(self)} and {type(other)}")
        return self.id == other.id

    def __ne__(self, other: Any) -> bool:
        if not isinstance(other, BaseWindow):
            raise TypeError(f"!= not defined for {type(self)} and {type(other)}")
        return self.id != other.id

    def __repr__(self) -> str:
        return f"Window(id={self.id})"

    @abstractmethod
    def match(self, criteria: Mapping) -> bool:
        """Determine whether the window matches a set of criteria.

        Parameters
        ----------
        criteria
            Dictionary of regexes of the form {PROPERTY: REGEX} e.g {"window_id": r"termite"}

        """
        pass

    @abstractmethod
    def set_opacity(self, opacity: float) -> None:
        pass

    @abstractmethod
    def destroy(self) -> None:
        """Request for the window to be closed."""
        pass

    @abstractmethod
    def is_fullscreen(self) -> bool:
        pass
