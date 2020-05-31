"""Routes requests from the server to the Flasher which matches the window.

In the case that no rules are present in the user's config, just one Flasher instance will exist and
all flash requests will be routed to that flasher. If rules are present, then a Flasher instance is
created for each rule. Each time a request comes in the router iterates through all of its rules and
passes the request on to the Flasher whose criteria match the window.

"""
import logging
from typing import Dict, List, Tuple

from flashfocus.compat import get_focused_workspace, list_mapped_windows, Window
from flashfocus.errors import UnexpectedMessageType
from flashfocus.display import WMEvent, WMEventType
from flashfocus.flasher import Flasher


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
    flashers
        List of flashers each with a distinct set of flash parameters. The last flasher in the list
        is the default flasher which will be used for windows which don't match any of the user's
        configured rules.
    rules
        List of rules each corresponding to a set of criteria for matching against windows. The last
        rule in the list is the default rule which matches any window.
    current_workspace: int
        The id of the current focused workspace
    prev_workspace: int
        The id of the previously focused workspace
    prev_focus: int
        The id of the previously focused window. We keep track of this so that
        the same window is never flashed consecutively. When a window is closed
        in i3, the next window is flashed 3 times without this guard

    """

    def __init__(self, config: Dict):
        if config.get("rules") is None:
            self.rules: List[Dict] = list()
        else:
            self.rules = config["rules"]
        self.flashers: List[Flasher] = list()
        # We only need to track the user's workspace if the user config requires it
        self.track_workspaces = config["flash_lone_windows"] != "always"
        for rule_config in self.rules:
            if rule_config["flash_lone_windows"] != "always":
                self.track_workspaces = True
            rule_flasher = Flasher(
                default_opacity=rule_config.get("default_opacity", config["default_opacity"]),
                flash_opacity=rule_config.get("flash_opacity", config["flash_opacity"]),
                simple=rule_config.get("simple", config["simple"]),
                ntimepoints=rule_config.get("ntimepoints", config["ntimepoints"]),
                time=rule_config.get("time", config["time"]),
            )
            self.flashers.append(rule_flasher)
        default_rule = {
            "flash_on_focus": config["flash_on_focus"],
            "flash_lone_windows": config["flash_lone_windows"],
            "flash_fullscreen": config["flash_fullscreen"],
        }
        self.rules.append(default_rule)
        default_flasher = Flasher(
            default_opacity=config["default_opacity"],
            flash_opacity=config["flash_opacity"],
            simple=config["simple"],
            ntimepoints=config["ntimepoints"],
            time=config["time"],
        )
        self.flashers.append(default_flasher)
        self.prev_focus = None
        if self.track_workspaces:
            self.current_workspace = get_focused_workspace()
            self.prev_workspace = self.current_workspace

    def route_request(self, message: WMEvent) -> None:
        """Match a window against rule criteria and handle the request according to it's type."""
        if message.event_type is WMEventType.FOCUS_SHIFT:
            self._route_focus_shift(message.window)
        elif message.event_type is WMEventType.NEW_WINDOW:
            self._route_new_window(message.window)
        elif message.event_type is WMEventType.CLIENT_REQUEST:
            self._route_client_request(message.window)
        elif message.event_type is WMEventType.WINDOW_INIT:
            self._route_window_init(message.window)
        else:
            raise UnexpectedMessageType()

    def _route_new_window(self, window: Window) -> None:
        """Handle a new window being mapped."""
        rule, flasher = self._match(window)
        if self._config_allows_flash(window, rule):
            # This will set the window to the default opacity afterwards
            flasher.flash(window)
        else:
            flasher.set_default_opacity(window)

    def _route_window_init(self, window: Window) -> None:
        """Handle a window initialization event (this happens at startup)."""
        rule, flasher = self._match(window)
        flasher.set_default_opacity(window)

    def _route_focus_shift(self, window: Window) -> None:
        """Handle a shift in the focused window."""
        if self.prev_focus is None or self.prev_focus != window:
            self.prev_focus = window
            rule, flasher = self._match(window)
            if self._config_allows_flash(window, rule):
                flasher.flash(window)
            else:
                flasher.set_default_opacity(window)
        else:
            logging.debug(f"Window {window.id} was just flashed, ignoring...")

    def _route_client_request(self, window: Window) -> None:
        """Handle a manual flash request from the user."""
        rule, flasher = self._match(window)
        flasher.flash(window)

    def _match(self, window: Window) -> Tuple[Dict, Flasher]:
        """Find a flash rule which matches window."""
        for i, (rule, flasher) in enumerate(zip(self.rules, self.flashers)):
            if window.match(rule):
                if i < len(self.rules) - 1:
                    logging.debug(f"Window {window.id} matches criteria of rule {i}")
                return rule, flasher
        return rule, flasher

    def _config_allows_flash(self, window: Window, rule: Dict) -> bool:
        """Check whether a config parameter disallows a window from flashing.

        Returns
        -------
        If window should be flashed, this function returns True, else False.

        """
        if self.track_workspaces:
            self.prev_workspace = self.current_workspace
            self.current_workspace = get_focused_workspace()

        if not rule.get("flash_on_focus"):
            logging.debug(f"flash_on_focus is False for window {window.id}, ignoring...")
            return False

        if rule.get("flash_lone_windows") != "always":
            if len(list_mapped_windows(self.current_workspace)) < 2:
                if (
                    rule.get("flash_lone_windows") == "never"
                    or (
                        self.current_workspace != self.prev_workspace
                        and rule.get("flash_lone_windows") == "on_open_close"
                    )
                    or (
                        self.current_workspace == self.prev_workspace
                        and rule.get("flash_lone_windows") == "on_switch"
                    )
                ):
                    logging.debug("Current workspace has <2 windows, ignoring...")
                    return False

        if rule.get("flash_fullscreen") is not True:
            if window.is_fullscreen():
                logging.debug("Window is fullscreen, ignoring...")
                return False

        return True
