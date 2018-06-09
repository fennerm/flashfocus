"""Helper functions/classes for unit tests."""
from __future__ import division

from contextlib import contextmanager
import re
from threading import Thread
from time import sleep

import xcffib
import xcffib.xproto
import xpybutil
import xpybutil.ewmh
from xpybutil.ewmh import set_active_window_checked
from xpybutil.icccm import set_wm_class_checked, set_wm_name_checked


from flashfocus.xutil import destroy_window


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

    def __init__(self):
        wm_names = ["window1", "window2"]
        wm_classes = [("window1", "Window1"), ("window2", "Window2")]
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
            destroy_window(window)


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
    param = {
        "default_opacity": 1,
        "flash_opacity": 0.8,
        "time": 100,
        "ntimepoints": 4,
        "simple": False,
        "flash_on_focus": True,
    }
    return param


def fill_in_rule(partial_rule):
    """Fill in default param for a rule given a partial rule definition."""
    for key, value in default_flash_param().items():
        if key not in partial_rule.keys():
            partial_rule[key] = value
    return partial_rule
