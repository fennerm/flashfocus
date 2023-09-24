"""Interacting with Sway-wm.

All submodules in flashfocus.display_protocols are expected to contain a minimal set of
functions/classes for abstracting across various display protocols. See list in flashfocus.compat

"""
from __future__ import annotations

import logging
from queue import Queue
from collections.abc import Mapping

import i3ipc

from flashfocus.display import BaseWindow, WMEventType
from flashfocus.producer import ProducerThread
from flashfocus.util import match_regex

# This connection is shared by all classes/functions in the module. It is not thread-safe to
# maintain multiple connections to sway through the same socket.
SWAY = i3ipc.Connection()


class Window(BaseWindow):
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
        super().__init__(self._container.id)
        self._properties = {
            "window_name": self._container.name,
            "window_class": self._container.window_class,
            "window_id": self._container.window_instance,
            "app_id": self._container.app_id,
        }

    @property
    def properties(self) -> dict:
        return self._properties

    def match(self, criteria: Mapping) -> bool:
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

    @property
    def opacity(self) -> float:
        raise NotImplementedError()

    def set_opacity(self, opacity: float) -> None:
        # If opacity is None just silently ignore the request
        self._container.command(f"opacity {opacity}")

    def set_name(self, name: str) -> None:
        raise NotImplementedError()

    def set_class(self, title: str, class_: str) -> None:
        raise NotImplementedError()

    def destroy(self) -> None:
        self._container.command("kill")

    def is_fullscreen(self) -> bool:
        fullscreen_mode: int = self._container.fullscreen_mode
        return fullscreen_mode == 1


class DisplayHandler(ProducerThread):
    """Parse events from sway and pass them on to FlashServer"""

    def __init__(self, queue: Queue) -> None:
        # This is set to True when initialization of the thread is complete and its ready to begin
        # the event loop
        self.ready = False
        super().__init__(queue)
        self.queue = queue

    def run(self) -> None:
        # We need to share one global sway connection in order to be thread-safe
        SWAY.on(i3ipc.Event.WINDOW_FOCUS, self._handle_focus_shift)
        SWAY.on(i3ipc.Event.WINDOW_NEW, self._handle_new_mapped_window)
        self.ready = True
        SWAY.main()

    def stop(self) -> None:
        SWAY.main_quit()
        super().stop()

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


def get_focused_window() -> Window | None:
    return Window(SWAY.get_tree().find_focused())


def _get_workspace_object(workspace: int) -> i3ipc.Con:
    return next(filter(lambda ws: ws.num == workspace, SWAY.get_tree().workspaces()), None)


def list_mapped_windows(workspace: int | None = None) -> list[Window]:
    if workspace is not None:
        containers = _get_workspace_object(workspace)
    else:
        containers = SWAY.get_tree().leaves()

    windows = [Window(con) for con in containers if _is_mapped_window(con)]
    return windows


def disconnect_display_conn() -> None:
    SWAY.main_quit()


def _try_get_con_workspace(container: i3ipc.Con | None) -> int | None:
    """Try to get the workspace associated with an i3ipc.Con object (else return None)."""
    if container is None:
        return None
    workspace = container.workspace()
    if workspace is None:
        return None
    workspace_number: int = workspace.num
    return workspace_number


def get_focused_workspace() -> int | None:
    focused_container = SWAY.get_tree().find_focused()
    return _try_get_con_workspace(focused_container)


def get_workspace(window: Window) -> int | None:
    """Get the workspace that the window is mapped to."""
    i3ipc_window = SWAY.get_tree().find_by_id(window.id)
    return _try_get_con_workspace(i3ipc_window)
