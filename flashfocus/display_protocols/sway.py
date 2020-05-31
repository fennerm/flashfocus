"""Interacting with Sway-wm.

All submodules in flashfocus.display_protocols are expected to contain a minimal set of
functions/classes for abstracting across various display protocols. See list in flashfocus.compat

"""
import logging
from queue import Queue
from threading import Thread
from typing import Dict, List, Optional

import i3ipc

from flashfocus.display import WMEvent, WMEventType
from flashfocus.errors import WMError
from flashfocus.util import match_regex


# This connection is shared by all classes/functions in the module. It is not thread-safe to
# maintain multiple connections to sway through the same socket.
SWAY = i3ipc.Connection()


class Window:
    """Represents a sway window.

    Parameters
    ----------
    container
        The i3ipc Con object for the window.

    Attributes
    ----------
    id
        The unique id of the window's sway container.
    properties
        A dictionary of window properties. If the window is from a native wayland app, it will
        contain the window's app_id and name. If the window is running under XWayland it will
        contain the window's ID (instance) and class.
    """

    def __init__(self, container: i3ipc.Con) -> None:
        self._container = container
        if self._container.id is None:
            raise WMError("Invalid window ID")
        self.id: int = self._container.id
        self.properties = {
            "window_name": self._container.name,
            "window_class": self._container.window_class,
            "window_id": self._container.window_instance,
            "app_id": self._container.app_id,
        }

    def __eq__(self, other: object) -> bool:
        if type(self) != type(other):
            raise TypeError("Arguments must be of the same type")
        return self._container.id == other._container.id

    def __ne__(self, other: object) -> bool:
        if type(self) != type(other):
            raise TypeError("Arguments must be of the same type")
        return self.id != other.id

    def match(self, criteria: Dict) -> bool:
        """Determine whether the window matches a set of criteria.

        Parameters
        ----------
        criteria
            Dictionary of regexes of the form {PROPERTY: REGEX} e.g {"window_id": r"termite"}

        """
        for prop in self.properties.keys():
            if criteria.get(prop) and not match_regex(criteria[prop], self.properties[prop]):
                return False
        return True

    def set_opacity(self, opacity: float) -> None:
        # If opacity is None just silently ignore the request
        self._container.command(f"opacity {opacity}")

    def destroy(self) -> None:
        self._container.command("kill")

    def is_fullscreen(self) -> bool:
        return self._container.fullscreen_mode == 1


class DisplayHandler(Thread):
    """Parse events from sway and pass them on to FlashServer"""

    def __init__(self, queue: Queue) -> None:
        # This is set to True when initialization of the thread is complete and its ready to begin
        # the event loop
        self.ready = False
        super(DisplayHandler, self).__init__()
        self.queue = queue

    def run(self) -> None:
        # We need to share one global sway connection in order to be thread-safe
        SWAY.on(i3ipc.Event.WINDOW_FOCUS, self._handle_focus_shift)
        SWAY.on(i3ipc.Event.WINDOW_NEW, self._handle_new_mapped_window)
        self.ready = True
        SWAY.main()

    def stop(self) -> None:
        self.keep_going = False
        SWAY.main_quit()
        self.join()

    def queue_window(self, window: Window, event_type: WMEventType) -> None:
        self.queue.put(WMEvent(window=window, event_type=event_type))

    def _handle_focus_shift(self, _: i3ipc.Connection, event: i3ipc.Event) -> None:
        if _is_mapped_window(event.container):
            logging.debug("Focus shifted to %s", event.container.id)
            self.queue_window(Window(event.container), WMEventType.FOCUS_SHIFT)

    def _handle_new_mapped_window(self, _: i3ipc.Connection, event: i3ipc.Event) -> None:
        if _is_mapped_window(event.container):
            logging.debug("Window %s mapped...", event.container.id)
            self.queue_window(Window(event.container), WMEventType.NEW_WINDOW)


def _is_mapped_window(container: i3ipc.Con) -> bool:
    """Determine whether a window is displayed on the screen with nonzero size."""
    return container and container.id and container.window_rect.width != 0  # type: ignore


def get_focused_window() -> Window:
    return Window(SWAY.get_tree().find_focused())


def get_workspace(workspace: int) -> i3ipc.Con:
    return next(filter(lambda ws: ws.num == workspace, SWAY.get_tree().workspaces()), None)


def list_mapped_windows(workspace: Optional[int] = None) -> List[Window]:
    if workspace is not None:
        containers = get_workspace(workspace)
    else:
        containers = SWAY.get_tree().leaves()

    windows = [Window(con) for con in containers if _is_mapped_window(con)]
    return windows


def disconnect_display_conn() -> None:
    SWAY.main_quit()


def get_focused_workspace() -> int:
    workspace: int = SWAY.get_tree().find_focused().workspace().num
    return workspace
