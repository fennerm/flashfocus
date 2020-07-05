"""Helper functions/classes for unit tests."""
from __future__ import division

import copy
from contextlib import contextmanager
from queue import Queue
import socket
from threading import Thread
from time import sleep
from typing import Dict, Generator, List, Pattern, Union

from flashfocus.client import ClientMonitor
from flashfocus.compat import (
    DisplayHandler,
    get_focused_window,
    get_focused_workspace,
    list_mapped_windows,
    Window,
)
from flashfocus.errors import WMError
from flashfocus.server import FlashServer
from test.compat import change_focus, clear_event_queue, create_blank_window, switch_workspace


Producer = Union[ClientMonitor, DisplayHandler]


def quick_conf() -> Dict:
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


def default_flash_param() -> Dict:
    return {
        "config": {"default": None, "type": [str], "location": "cli"},
        "verbosity": {"default": "INFO", "type": str, "location": "cli"},
        "default_opacity": {"default": 1, "type": [float], "location": "any"},
        "flash_opacity": {"default": 0.8, "type": [float], "location": "any"},
        "time": {"default": 100, "type": [float], "location": "any"},
        "ntimepoints": {"default": 4, "type": [int], "location": "any"},
        "simple": {"default": False, "type": [bool], "location": "any"},
        "flash_on_focus": {"default": True, "type": [bool], "location": "any"},
        "flash_lone_windows": {"default": "always", "type": [str], "location": "any"},
        "flash_fullscreen": {"default": True, "type": [bool], "location": "any"},
        "rules": {"default": None, "type": [list, type(None)], "location": "config_file"},
        "window_id": {"default": "window1", "type": [Pattern], "location": "rule"},
        "window_class": {"default": "Window1", "type": [Pattern], "location": "rule"},
    }


class WindowSession:
    """A session of blank windows for testing."""

    def __init__(self, num_windows: int = 2) -> None:
        wm_names = ["window" + str(i) for i in range(1, num_windows + 1)]
        wm_classes = zip(wm_names, [name.capitalize() for name in wm_names])
        clear_desktops()
        self.windows = [
            create_blank_window(wm_name, wm_class)
            for wm_name, wm_class in zip(wm_names, wm_classes)
        ]
        # Wait for all of the windows to be mapped
        for window in self.windows:
            while window not in list_mapped_windows():
                pass
        change_focus(self.windows[0])
        # Wait for the focus to actually change
        while get_focused_window() != self.windows[0]:
            pass

    def destroy(self) -> None:
        """Tear down the window session."""
        for window in self.windows:
            try:
                window.destroy()
            except Exception:
                pass


class WindowWatcher(Thread):
    """Watch a window for changes in opacity."""

    def __init__(self, window: Window):
        super(WindowWatcher, self).__init__()
        self.window: Window = window
        self.opacity_events: List[float] = [window.opacity]
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
        self.data: List[bytes] = []

    def await_data(self):
        """Wait for a single piece of data from a client and store it."""
        self.data.append(self.socket.recv(1))


def queue_to_list(queue: Queue) -> List:
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
    while not server.events.empty():
        pass
    server.shutdown(disconnect_from_wm=False)


@contextmanager
def watching_windows(windows: List[Window]) -> Generator:
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
    window_session = WindowSession(1)
    watcher = WindowWatcher(window_session.windows[0])
    watcher.start()
    sleep(0.1)
    yield window_session.windows[0], watcher
    watcher.stop()
    window_session.destroy()


@contextmanager
def producer_running(producer: Producer) -> Generator:
    producer.start()
    # TODO - replace these sleep calls
    sleep(0.01)
    yield
    sleep(0.01)
    producer.stop()


def fill_in_rule(partial_rule: Dict) -> Dict:
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


def rekey(dic: Dict, new_vals: Dict) -> Dict:
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
