"""Helper functions/classes for unit tests."""
from __future__ import division

from contextlib import contextmanager
import os
import re
from threading import Thread
from time import sleep

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import xpybutil
import xpybutil.ewmh


class WindowSession:
    """A session of blank windows for testing."""

    def __init__(self):
        window1 = Gtk.Window(title="window1")
        window1.set_wmclass("window1", "Window1")
        window1.show()
        window2 = Gtk.Window(title="window2")
        window2.set_wmclass("window2", "Window2")
        window2.show()
        window3 = Gtk.Window(title="window3")
        window3.show()

        self.windows = [window1, window2, window3]
        self.ids = [w.get_property("window").get_xid() for w in self.windows]
        change_focus(self.ids[0])

    def destroy(self):
        """Tear down the window session."""
        for window in self.windows:
            window.destroy()


def change_focus(window):
    """Change the active window."""
    os.system("xdotool windowactivate " + str(window))
    sleep(0.1)


def close_window(window):
    """Close an X window."""
    xpybutil.request_close_window_checked(window).check()


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
        sleep(0.4)
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
    sleep(1)
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
