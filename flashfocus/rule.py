"""Handle window-specific flash rules."""
from logging import info
import re

from flashfocus.flasher import Flasher
from flashfocus.misc import list_param
from flashfocus.xutil import get_wm_class


def match_regex(regex, target):
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

    def __init__(self, id_regex=None, class_regex=None):
        self.id_regex = id_regex
        self.class_regex = class_regex

    def match(self, window_id, window_class):
        """Match a window id and class.

        Parameters
        ----------
        window_id, window_class: str
            ID and class of a window

        """
        for regex, property in zip(
            [self.id_regex, self.class_regex], [window_id, window_class]
        ):
            if regex:
                if not match_regex(regex, property):
                    return False
        return True


class RuleMatcher:
    """Matches a set of window match criteria to a set of flash parameters.

    This is used for determining which flash parameters should be used for a
    given window. If no rules match the window, a default set of parameters is
    used.

    Parameters
    ----------
    defaults: Dict[str, Any]
        Set of default parameters. Must include all `Flasher` parameters and
        `flash_on_focus` setting.
    rules: Dict[str, Any]
        Set of rule parameters from user config. Must include all `Flasher`
        parameters, `flash_on_focus` setting and `window_id` and/or
        `window_class`.

    """

    def __init__(self, defaults, rules):
        self.rules = []
        self.flashers = []
        self.flash_on_focus = []
        flasher_param = list_param(Flasher.__init__)
        if rules:
            for rule in rules:
                self.rules.append(
                    Rule(
                        id_regex=rule.get("window_id"),
                        class_regex=rule.get("window_class"),
                    )
                )
                self.flashers.append(
                    Flasher(**{k: rule[k] for k in flasher_param})
                )
                self.flash_on_focus.append(rule["flash_on_focus"])
        self.rules.append(Rule())
        self.flash_on_focus.append(defaults["flash_on_focus"])
        self.flashers.append(Flasher(**{k: defaults[k] for k in flasher_param}))
        self.iter = list(zip(self.rules, self.flash_on_focus, self.flashers))

    def route_request(self, window, request_type=None):
        """Direct a request to the appropriate flasher.

        Parameters
        ----------
        window: int
            A Xorg window id
        request_type: str
            One of ['focus_shift', 'client_request'], if 'focus_shift' and
            flash_on_focus is False for the matching rule, the window will not
            be flashed.

        """
        try:
            flasher = self.match(window, request_type)
            if request_type == "new_window":
                flasher.set_default_opacity(window)
            else:
                flasher.flash(window)
        except TypeError:
            # match returned None
            pass

    def match(self, window, request_type=None):
        """Find a flash rule which matches `window`

        Parameters
        ----------
        window: int
            A Xorg window id
        request_type: str
            One of ['focus_shift', 'client_request']

        Returns
        -------
        Tuple[Rule, Flasher]
            The matching rule and flasher. Returns None if
            request_type=='focus_shift' and flash_on_focus is False for the rule

        """
        window_id, window_class = get_wm_class(window)
        i = 1
        for rule, focus_flash, flasher in self.iter:
            if rule.match(window_id, window_class):
                if i < len(self.rules):
                    info("Window %s matches criteria of rule %s", window, i)
                if request_type == "focus_shift" and not focus_flash:
                    info(
                        "flash_on_focus is False for window %s, ignoring...",
                        window,
                    )
                    return None
                return flasher
            i += 1
