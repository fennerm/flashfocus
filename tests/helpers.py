"""Helper functions/classes for unit tests."""
from __future__ import annotations, division

import copy
import re
import socket
from collections.abc import Generator
from contextlib import contextmanager
from queue import Queue
from threading import Thread
from time import sleep
from typing import Union

from flashfocus.client import ClientMonitor
from flashfocus.compat import (
    DisplayHandler,
    Window,
    get_focused_workspace,
    list_mapped_windows,
)
from flashfocus.errors import WMError
from flashfocus.server import FlashServer
from tests.compat import (
    change_focus,
    clear_event_queue,
    create_blank_window,
    switch_workspace,
)

Producer = Union[ClientMonitor, DisplayHandler]


def quick_conf() -> dict:
    return dict(
        default_opacity=1,
        flash_opacity=0.8,
        time=100,
        ntimepoints=4,
        simple=False,
        rules=None,
        flash_on_focus=True,
        flash_lone_windows="always",
        flash_fullscreen=True,
    )


def default_flash_param() -> dict:
    return {
        "config": {"default": None, "type": [str], "location": "cli"},
        "verbosity": {"default": "INFO", "type": [str], "location": "cli"},
        "default_opacity": {"default": 1, "type": [float], "location": "any"},
        "flash_opacity": {"default": 0.8, "type": [float], "location": "any"},
        "time": {"default": 100, "type": [float], "location": "any"},
        "ntimepoints": {"default": 4, "type": [int], "location": "any"},
        "simple": {"default": False, "type": [bool], "location": "any"},
        "flash_on_focus": {"default": True, "type": [bool], "location": "any"},
        "flash_lone_windows": {"default": "always", "type": [str], "location": "any"},
        "flash_fullscreen": {"default": True, "type": [bool], "location": "any"},
        "rules": {"default": None, "type": [list, type(None)], "location": "config_file"},
        "window_id": {"default": "window1", "type": [re.Pattern], "location": "rule"},
        "window_class": {"default": "Window1", "type": [re.Pattern], "location": "rule"},
    }


class WindowSession:
    """A session of blank windows for testing."""

    def __init__(self, num_windows_by_workspace: dict[int, int] | None = None) -> None:
        """
        Parameters
        ----------
        num_windows_by_workspace
            A dict mapping workspace number to the number of windows which should be created on the
            workspace

        """
        self.windows: dict[int, Window] = {}
        self.num_windows_by_workspace = (
            num_windows_by_workspace if num_windows_by_workspace is not None else {0: 2}
        )

    def setup(self) -> None:
        """Create the window session."""
        clear_desktops()
        if self.num_windows_by_workspace:
            self._create_windows()
            self._set_initial_focused_window()

    def destroy(self) -> None:
        """Tear down the window session."""
        for window in self.windows:
            try:
                window.destroy()
            except Exception:
                pass

    def get_first_window(self) -> Window:
        """Get the first window from the first workspace."""
        for workspace in sorted(self.windows.keys()):
            if len(self.windows[workspace]) > 0:
                return self.windows[workspace][0]

    def _create_windows(self) -> None:
        for workspace, num_windows in self.num_windows_by_workspace.items():
            wm_names = [f"window_{workspace}_{number}" for number in range(1, num_windows + 1)]
            wm_classes = zip(wm_names, [name.capitalize() for name in wm_names])
            switch_workspace(workspace)
            self.windows[workspace] = [
                create_blank_window(wm_name, wm_class)
                for wm_name, wm_class in zip(wm_names, wm_classes)
            ]

    def _set_initial_focused_window(self) -> None:
        for workspace in sorted(self.windows.keys()):
            if len(self.windows[workspace]) > 0:
                break
        switch_workspace(workspace)
        change_focus(self.windows[workspace][0])


class WindowWatcher(Thread):
    """Watch a window for changes in opacity."""

    def __init__(self, window: Window):
        super().__init__()
        self.window: Window = window
        self.opacity_events: list[float] = [window.opacity]
        self.keep_going: bool = True
        self.done: bool = False

    def run(self) -> None:
        """Record opacity changes until stop signal received."""
        while self.keep_going:
            opacity = self.window.opacity
            if opacity != self.opacity_events[-1]:
                self.opacity_events.append(opacity)
        self.done = True

    def stop(self) -> None:
        # Give the x server a little time to catch up with requests
        sleep(0.2)
        self.keep_going = False
        while not self.done:
            pass
        self.opacity_events = [1 if event is None else event for event in self.opacity_events]

    def count_flashes(self):
        num_flashes = 0
        for i, event in enumerate(self.opacity_events):
            if 0 < i < len(self.opacity_events) - 1:
                if event < self.opacity_events[i - 1] and event < self.opacity_events[i + 1]:
                    num_flashes += 1
        return num_flashes


class StubServer:
    """A server socket which receives a hunk of data and stores it in a list.

    Used to test that clients are making correct requests.
    """

    def __init__(self, socket: socket.socket):
        self.socket = socket
        self.data: list[bytes] = []

    def await_data(self):
        """Wait for a single piece of data from a client and store it."""
        self.data.append(self.socket.recv(1))


def queue_to_list(queue: Queue) -> list:
    """Convert a Queue to a list."""
    result = []
    while queue.qsize() != 0:
        result.append(queue.get())
    return result


@contextmanager
def server_running(server: FlashServer) -> Generator:
    clear_event_queue()
    p = Thread(target=server.event_loop)
    p.start()
    while not server.ready:
        pass
    yield
    # Give the display handler thread a little time to register any recent events
    sleep(0.2)
    while not server.events.empty() or server.processing_event:
        pass
    server.shutdown(disconnect_from_wm=False)


@contextmanager
def watching_windows(windows: list[Window]) -> Generator:
    watchers = [WindowWatcher(window) for window in windows]
    for watcher in watchers:
        watcher.start()
    yield watchers
    for watcher in watchers:
        watcher.stop()


def clear_desktops():
    for workspace in range(5):
        clear_workspace(workspace)
    switch_workspace(0)
    while not get_focused_workspace() == 0:
        pass


@contextmanager
def new_watched_window() -> Generator:
    """Open a new window and watch it."""
    window_session = WindowSession({0: 1})
    window_session.setup()
    watcher = WindowWatcher(window_session.get_first_window())
    watcher.start()
    sleep(0.1)
    yield window_session.get_first_window(), watcher
    watcher.stop()
    window_session.destroy()


@contextmanager
def new_window_session(num_windows_by_workspace: dict[int, int]) -> Generator:
    """Context manager for creating a session of windows across multiple workspaces."""
    window_session = WindowSession(num_windows_by_workspace)
    window_session.setup()
    yield window_session
    window_session.destroy()


@contextmanager
def producer_running(producer: Producer) -> Generator:
    producer.start()
    # TODO - replace these sleep calls
    sleep(0.01)
    yield
    sleep(0.01)
    producer.stop()


def fill_in_rule(partial_rule: dict) -> dict:
    """Fill in default param for a rule given a partial rule definition."""
    default_rules = {
        key: val["default"]
        for key, val in default_flash_param().items()
        if val["location"] == "any"
    }
    for key, value in default_rules.items():
        if key not in partial_rule.keys():
            partial_rule[key] = copy.deepcopy(value)
    return partial_rule


def rekey(dic: dict, new_vals: dict) -> dict:
    dic_copy = copy.deepcopy(dic)
    for key, val in new_vals.items():
        dic_copy[key] = val
    return dic_copy


def clear_workspace(workspace: int) -> None:
    for window in list_mapped_windows(workspace):
        try:
            window.destroy()
        except WMError:
            pass
