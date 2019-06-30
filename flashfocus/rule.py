"""Handle window-specific flash rules."""
import re
from typing import Optional

from flashfocus.compat import Window


def _match_regex(regex: str, target: str) -> bool:
    try:
        return bool(re.match(regex, target))
    except TypeError:
        # For our purposes, target is probably None
        return False


class Rule:
    """A rule for matching a window's id and class to a set of criteria.

    If no parameters are passed, the rule will match any window.

    Parameters
    ----------
    id_regex, class_regex: regex
        Window ID and class match criteria

    """

    def __init__(
        self,
        id_regex: Optional[str] = None,
        class_regex: Optional[str] = None,
        flash_on_focus: bool = False,
        flash_lone_windows: bool = False,
    ) -> None:
        self.id_regex = id_regex
        self.class_regex = class_regex
        self.flash_on_focus = flash_on_focus
        self.flash_lone_windows = flash_lone_windows

    def match(self, window: Window) -> bool:
        """Match a window id and class.

        Parameters
        ----------
        window_id, window_class: str
            ID and class of a window

        """
        window_title, window_class = window.wm_class
        for regex, property in zip([self.id_regex, self.class_regex], [window_title, window_class]):
            if regex:
                if not _match_regex(regex, property):
                    return False
        return True
