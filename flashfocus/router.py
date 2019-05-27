"""Routes requests from the server to the Flasher which matches the window.

In the case that no rules are present in the user's config, just one Flasher instance will exist and
all flash requests will be routed to that flasher. If rules are present, then a Flasher instance is
created for each rule. Each time a request comes in the router iterates through all of its rules and
passes the request on to the Flasher whose criteria match the window.

"""
import logging

from flashfocus.flasher import Flasher
from flashfocus.rule import Rule
from flashfocus.util import list_param
from flashfocus.xutil import count_windows, get_current_desktop, get_wm_class


class UnexpectedRequestType(ValueError):
    pass


class FlashRouter:
    """Matches a set of window match criteria to a flasher with a set of flash parameters.

    This is used for determining which flash parameters should be used for a
    given window. If no rules match the window, a default set of parameters is
    used.

    Parameters
    ----------
    defaults: Dict[str, Any]
        Set of default parameters. Must include all `Flasher` parameters and
        `flash_on_focus` and `flash_lone_windows` settings.
    config_rules: Dict[str, Any]
        Set of rule parameters from user config. Must include all `Flasher`
        parameters, `flash_on_focus` setting and `window_id` and/or
        `window_class`.

    """

    def __init__(self, defaults, config_rules):
        self.rules = []
        self.flashers = []
        flasher_param = list_param(Flasher.__init__)
        if config_rules:
            for rule in config_rules:
                self.rules.append(
                    Rule(
                        id_regex=rule.get("window_id"),
                        class_regex=rule.get("window_class"),
                        flash_lone_windows=rule.get("flash_lone_windows"),
                        flash_on_focus=rule.get("flash_on_focus"),
                    )
                )
                self.flashers.append(Flasher(**{k: rule[k] for k in flasher_param}))
        default_rule = Rule(
            flash_on_focus=defaults["flash_on_focus"],
            flash_lone_windows=defaults["flash_lone_windows"],
        )
        default_flasher = Flasher(**{k: defaults[k] for k in flasher_param})
        self.rules.append(default_rule)
        self.flashers.append(default_flasher)
        self.current_desktop = get_current_desktop()
        self.prev_desktop = None
        self.prev_focus = None

    def route_request(self, window, request_type):
        if request_type == "focus_shift":
            self._route_focus_shift(window)
        elif request_type == "new_window":
            self._route_new_window(window)
        elif request_type == "client_request":
            self._route_client_request(window)
        elif request_type == "window_init":
            self._route_window_init(window)
        else:
            raise UnexpectedRequestType()

    def _route_new_window(self, window):
        """Direct a request to the appropriate flasher.

        Parameters
        ----------
        window: int
            A Xorg window id
        rule, flasher = self._match(window)

        """
        rule, flasher = self._match(window)
        if self._config_allows_flash(window, rule):
            flasher.flash(window)
        else:
            flasher.set_default_opacity(window)

    def _route_window_init(self, window):
        """Direct a request to the appropriate flasher.

        Parameters
        ----------
        window: int
            A Xorg window id
        rule, flasher = self._match(window)

        """
        rule, flasher = self._match(window)
        flasher.set_default_opacity(window)

    def _route_focus_shift(self, window):
        """Direct a request to the appropriate flasher.

        Parameters
        ----------
        window: int
            A Xorg window id
        rule, flasher = self._match(window)

        """
        if self.prev_focus != window:
            self.prev_focus = window
            rule, flasher = self._match(window)
            if self._config_allows_flash(window, rule):
                flasher.flash(window)
        else:
            logging.info("Window %s was just flashed, ignoring...", window)

    def _route_client_request(self, window):
        rule, flasher = self._match(window)
        flasher.flash(window)

    def _match(self, window):
        """Find a flash rule which matches `window`.

        Parameters
        ----------
        window: int
            A Xorg window id

        Returns
        -------
        Tuple[Rule, Flasher]
            The matching rule and flasher. Returns None if
            request_type=='focus_shift' and flash_on_focus is False for the rule

        """
        window_id, window_class = get_wm_class(window)
        self.prev_desktop = self.current_desktop
        self.current_desktop = get_current_desktop()
        for i, (rule, flasher) in enumerate(zip(self.rules, self.flashers)):
            if rule.match(window_id, window_class):
                if i < len(self.rules) - 1:
                    logging.info("Window %s matches criteria of rule %s", window, i)
                return rule, flasher

    def _config_allows_flash(self, window, rule):
        """Check whether a config parameter prevents a window from flashing.

        Parameters
        ----------
        window: int
            A Xorg window id
        rule: Rule
            A configured rule associated with the current window

        Returns
        -------
        If window should be flashed, this function returns True, else False.

        """
        if not rule.flash_on_focus:
            logging.info("flash_on_focus is False for window %s, ignoring...", window)
            return False
        elif rule.flash_lone_windows != "always" and count_windows(self.current_desktop) < 2:
            if (
                rule.flash_lone_windows == "never"
                or (
                    self.current_desktop != self.prev_desktop
                    and rule.flash_lone_windows == "on_open_close"
                )
                or (
                    self.current_desktop == self.prev_desktop
                    and rule.flash_lone_windows == "on_switch"
                )
            ):
                logging.info("Current desktop has <2 windows, ignoring...")
                return False
            else:
                return True
        else:
            return True
