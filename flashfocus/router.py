"""Routes requests from the server to the Flasher which matches the window.

In the case that no rules are present in the user's config, just one Flasher instance will exist and
all flash requests will be routed to that flasher. If rules are present, then a Flasher instance is
created for each rule. Each time a request comes in the router iterates through all of its rules and
passes the request on to the Flasher whose criteria match the window.

"""
import logging
from typing import List, Tuple

from flashfocus.compat import get_focused_desktop, list_mapped_windows, Window
from flashfocus.config import Config
from flashfocus.display import WMMessage, WMMessageType
from flashfocus.flasher import Flasher
from flashfocus.rule import Rule


class UnexpectedMessageType(ValueError):
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

    Attributes
    ----------
    flashers: List[flashfocus.flasher.Flasher]
        List of flashers each with a distinct set of flash parameters. The last flasher in the list
        is the default flasher which will be used for windows which don't match any of the user's
        configured rules.
    rules: List[flashfocus.rule.Rule]
        List of rules each corresponding to a set of criteria for matching against windows. The last
        rule in the list is the default rule which matches any window.
    current_desktop: int
        The id of the current focused desktop
    prev_desktop: int
        The id of the previously focused desktop
    prev_focus: int
        The id of the previously focused window. We keep track of this so that
        the same window is never flashed consecutively. When a window is closed
        in i3, the next window is flashed 3 times without this guard

    """

    def __init__(self, config: Config):
        self.rules: List[Rule] = []
        self.flashers: List[Flasher] = []
        if config.get("rules"):
            for rule_config in config.get("rules"):
                rule = Rule(
                    id_regex=rule_config.get("window_id"),
                    class_regex=rule_config.get("window_class"),
                    flash_lone_windows=rule_config.get("flash_lone_windows"),
                    flash_on_focus=rule_config.get("flash_on_focus"),
                )
                rule_flasher = Flasher(
                    default_opacity=rule_config.get("default_opacity"),
                    flash_opacity=rule_config.get("flash_opacity"),
                    simple=rule_config.get("simple"),
                    ntimepoints=rule_config.get("ntimepoints"),
                    time=rule_config.get("time"),
                )
                self.flashers.append(rule_flasher)
                self.rules.append(rule)
        default_rule = Rule(
            flash_on_focus=config.get("flash_on_focus"),
            flash_lone_windows=config.get("flash_lone_windows"),
        )
        default_flasher = Flasher(
            default_opacity=config.get("default_opacity"),
            flash_opacity=config.get("flash_opacity"),
            simple=config.get("simple"),
            ntimepoints=config.get("ntimepoints"),
            time=config.get("time"),
        )
        self.rules.append(default_rule)
        self.flashers.append(default_flasher)
        self.current_desktop = get_focused_desktop()
        self.prev_desktop = None
        self.prev_focus = None

    def route_request(self, message: WMMessage) -> None:
        """Match a window against rule criteria and handle the request according to it's type.


        Parameters
        ----------
        window: int
            A Xorg window id
        request_type: str
            One of 'new_window', 'client_request', 'window_init', 'focus_shift'

        """
        if message.type is WMMessageType.FOCUS_SHIFT:
            self._route_focus_shift(message.window)
        elif message.type is WMMessageType.NEW_WINDOW:
            self._route_new_window(message.window)
        elif message.type is WMMessageType.CLIENT_REQUEST:
            self._route_client_request(message.window)
        elif message.type is WMMessageType.WINDOW_INIT:
            self._route_window_init(message.window)
        else:
            raise UnexpectedMessageType()

    def _route_new_window(self, window: Window) -> None:
        """Direct a request to the appropriate flasher.

        Parameters
        ----------
        window: int
            A window id
        rule, flasher = self._match(window)

        """
        rule, flasher = self._match(window)
        if self._config_allows_flash(window, rule):
            flasher.flash(window)
        else:
            flasher.set_default_opacity(window)

    def _route_window_init(self, window: Window) -> None:
        """Direct a request to the appropriate flasher.

        Parameters
        ----------
        window: int
            A Xorg window id
        rule, flasher = self._match(window)

        """
        rule, flasher = self._match(window)
        flasher.set_default_opacity(window)

    def _route_focus_shift(self, window: Window) -> None:
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
            logging.info(f"Window {window.id} was just flashed, ignoring...")

    def _route_client_request(self, window: Window) -> None:
        rule, flasher = self._match(window)
        flasher.flash(window)

    def _match(self, window: Window) -> Tuple[Rule, Flasher]:
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
        self.prev_desktop = self.current_desktop
        self.current_desktop = get_focused_desktop()
        for i, (rule, flasher) in enumerate(zip(self.rules, self.flashers)):
            if rule.match(window):
                if i < len(self.rules) - 1:
                    logging.info(f"Window {window.id} matches criteria of rule {i}")
                return rule, flasher
        return rule, flasher

    def _config_allows_flash(self, window: Window, rule: Rule) -> bool:
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
            logging.info(f"flash_on_focus is False for window {window.id}, ignoring...")
            return False
        elif (
            rule.flash_lone_windows != "always"
            and len(list_mapped_windows(self.current_desktop)) < 2
        ):
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
