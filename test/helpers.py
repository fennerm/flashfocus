"""Helper functions/classes for unit tests."""
from __future__ import division

import copy
from contextlib import contextmanager
import re
from threading import Thread
from time import sleep
import subprocess
import sys

import xcffib
import xcffib.xproto
from xcffib.xproto import WindowError
import xpybutil
import xpybutil.ewmh
from xpybutil.ewmh import set_active_window_checked
from xpybutil.icccm import set_wm_class_checked, set_wm_name_checked


from flashfocus.xutil import destroy_window, list_mapped_windows


def create_blank_window(wm_name=None, wm_class=None):
    """Create a blank Xorg window."""
    setup = xpybutil.conn.get_setup()
    window = xpybutil.conn.generate_id()
    xpybutil.conn.core.CreateWindow(
        setup.roots[0].root_depth,
        window,
        setup.roots[0].root,
        0,
        0,
        640,
        480,
        0,
        xcffib.xproto.WindowClass.InputOutput,
        setup.roots[0].root_visual,
        xcffib.xproto.CW.BackPixel | xcffib.xproto.CW.EventMask,
        [
            setup.roots[0].white_pixel,
            xcffib.xproto.EventMask.Exposure | xcffib.xproto.EventMask.KeyPress,
        ],
    )
    xpybutil.conn.core.MapWindow(window)
    xpybutil.conn.flush()
    cookies = []
    if wm_class:
        cookies.append(set_wm_class_checked(window, wm_class[0], wm_class[1]))
    if wm_name:
        cookies.append(set_wm_name_checked(window, wm_name))
    for cookie in cookies:
        cookie.check()
    return window


class WindowSession:
    """A session of blank windows for testing."""

    def __init__(self, num_windows=2):
        wm_names = ["window" + str(i) for i in range(1, num_windows + 1)]
        wm_classes = zip(wm_names, [name.capitalize() for name in wm_names])
        self.windows = [
            create_blank_window(wm_name, wm_class)
            for wm_name, wm_class in zip(wm_names, wm_classes)
        ]
        sleep(0.1)
        change_focus(self.windows[0])
        sleep(0.4)

    def destroy(self):
        """Tear down the window session."""
        for window in self.windows:
            try:
                destroy_window(window)
            except:
                pass


def change_focus(window):
    """Change the active window."""
    set_active_window_checked(window).check()
    sleep(0.01)


class WindowWatcher(Thread):
    """Watch a window for changes in opacity."""

    def __init__(self, window):
        super(WindowWatcher, self).__init__()
        self.window = window
        self.opacity_events = [
            xpybutil.ewmh.get_wm_window_opacity(self.window).reply()
        ]
        self.keep_going = True
        self.done = False

    def run(self):
        """Record opacity changes until stop signal received."""
        while self.keep_going:
            opacity = xpybutil.ewmh.get_wm_window_opacity(self.window).reply()
            if opacity != self.opacity_events[-1]:
                self.opacity_events.append(opacity)
        self.done = True

    def report(self):
        """Send the stop signal and report changes in _NET_WM_WINDOW_OPACITY."""
        # Give the x server a little time to catch up with requests
        sleep(0.2)
        self.keep_going = False
        while not self.done:
            pass
        return self.opacity_events


class StubServer:
    """A server socket which receives a hunk of data and stores it in a list.

    Used to test that clients are making correct requests.
    """

    def __init__(self, socket):
        self.socket = socket
        self.data = []

    def await_data(self):
        """Wait for a single piece of data from a client and store it."""
        self.data.append(self.socket.recv(1))


def queue_to_list(queue):
    """Convert a Queue to a list."""
    result = []
    while queue.qsize() != 0:
        result.append(queue.get())
    return result


@contextmanager
def server_running(server):
    while xpybutil.conn.poll_for_event():
        pass
    p = Thread(target=server.event_loop)
    p.start()
    sleep(0.1)
    yield
    sleep(0.01)
    server.shutdown(disconnect_from_xorg=False)


@contextmanager
def watching_windows(windows):
    watchers = [WindowWatcher(window) for window in windows]
    for watcher in watchers:
        watcher.start()
    yield watchers


@contextmanager
def producer_running(producer):
    producer.start()
    sleep(0.01)
    yield
    sleep(0.01)
    producer.stop()


def to_regex(x):
    """Convert a string to a regex (returns None if `x` is None)"""
    try:
        return re.compile(x)
    except TypeError:
        return None


def default_flash_param():
    try:
        regex_pattern_type = re.Pattern
    except:
        regex_pattern_type = re._pattern_type
    if sys.version[0] == "2":
        string_type = basestring
    else:
        string_type = str

    return {
        "default_opacity": {"default": 1, "type": [float], "location": "any"},
        "flash_opacity": {"default": 0.8, "type": [float], "location": "any"},
        "time": {"default": 100, "type": [float], "location": "any"},
        "ntimepoints": {"default": 4, "type": [int], "location": "any"},
        "simple": {"default": False, "type": [bool], "location": "any"},
        "flash_on_focus": {"default": True, "type": [bool], "location": "any"},
        "flash_lone_windows": {
            "default": "always",
            "type": [string_type],
            "location": "any",
        },
        "rules": {
            "default": dict(),
            "type": [dict, type(None)],
            "location": "config_file",
        },
        "window_id": {
            "default": "window1",
            "type": [regex_pattern_type],
            "location": "rule",
        },
        "window_class": {
            "default": "Window1",
            "type": [regex_pattern_type],
            "location": "rule",
        },
    }


def fill_in_rule(partial_rule):
    """Fill in default param for a rule given a partial rule definition."""
    default_rules = {
        key: val["default"]
        for key, val in default_flash_param().items()
        if val["location"] == "any"
    }
    for key, value in default_rules.items():
        if key not in partial_rule.keys():
            partial_rule[key] = value
    return partial_rule


def switch_desktop(desktop_index):
    # unfortunately need to use i3 specific command here because i3 blocks
    # external desktop switch requests
    subprocess.check_output(["i3-msg", "workspace", str(desktop_index + 1)])


def rekey(dic, key, val):
    dic_copy = copy.deepcopy(dic)
    dic_copy[key] = val
    return dic_copy


def clear_desktop(desktop_index):
    for window in list_mapped_windows():
        try:
            destroy_window(window)
        except WindowError:
            pass
