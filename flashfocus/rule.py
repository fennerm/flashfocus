"""Handle window-specific flash rules."""
import re

from flashfocus.flasher import Flasher
from flashfocus.xutil import get_wm_class


class Rule:
    def __init__(self, id_regex=None, class_regex=None):
        self.id_regex = id_regex
        self.class_regex = class_regex

    def match(self, window_id, window_class):
        if self.id_regex:
            if not re.match(self.id_regex, window_id):
                return False
        if self.class_regex:
            if not re.match(self.class_regex, window_class):
                return False
        return True


class DefaultRule(Rule):
    def match(self, window_id, window_class):
        return True


class RuleMatcher:
    def __init__(self,
                 default_opacity,
                 flash_opacity,
                 simple,
                 time,
                 ntimepoints,
                 flash_on_focus,
                 rules):
        self.rules = []
        self.flashers = []
        self.flash_on_focus = []
        for rule in rules:
            self.rules.append(
                Rule(id_regex=rule.get('window_id'),
                     class_regex=rule.get('window_class')))
            self.flashers.append(
                Flasher(time=rule['time'],
                        ntimepoints=rule['ntimepoints'],
                        default_opacity=rule['default_opacity'],
                        flash_opacity=rule['flash_opacity'],
                        simple=rule['simple']))
            self.flash_on_focus.append(rule['flash_on_focus'])
        self.rules.append(DefaultRule())
        self.flash_on_focus.append(flash_on_focus)
        self.flashers.append(Flasher(time=time,
                                     ntimepoints=ntimepoints,
                                     default_opacity=default_opacity,
                                     flash_opacity=flash_opacity,
                                     simple=simple))
        self.iter = list(zip(self.rules, self.flash_on_focus, self.flashers))

    def match(self, window, request_type=None):
        """Find a flash rule which matches `window`

        Parameters
        ----------
        window: int
            An Xorg window id
        request_type: str
            One of ['focus_shift', 'client_request']

        Returns
        -------
        Tuple[Rule, Flasher]
            The matching rule and flasher. Returns None if
            request_type=='focus_shift' and flash_on_focus is False for the rule

        """
        window_id, window_class = get_wm_class(window)
        for rule, focus_flash, flasher in self.iter:
            if rule.match(window_id, window_class):
                if request_type == 'focus_shift' and not focus_flash:
                    return None
                return rule, flasher
