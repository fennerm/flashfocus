"""Helper functions/classes for unit tests."""
from __future__ import division

from threading import Thread
from time import sleep

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from plumbum.cmd import (
    xdotool,
    xkill,
)
from xcffib import xproto

from flashfocus.xutil import XConnection
class WindowSession:
    """A session of blank windows for testing."""
    def __init__(self):
        window1 = Gtk.Window(title='window1')
        window1.show()
        window2 = Gtk.Window(title='window2')
        window2.show()
        window3 = Gtk.Window(title='window3')
        window3.show()

        self.windows = [window1, window2, window3]
        self.ids = [
            w.get_property('window').get_xid() for w in self.windows]
        change_focus(self.ids[0])

    def destroy(self):
        """Tear down the window session."""
        for window in self.windows:
            window.destroy()


def change_focus(window):
    """Change the active window."""
    xdotool('windowactivate', window)


def close_window(window):
    """Close an X window."""
    xkill('-id', window)


class WindowWatcher(Thread):
    """Watch a window for changes in opacity."""
    def __init__(self, window):
        super(WindowWatcher, self).__init__()
        self.xconn = XConnection()
        self.window = window
        self.opacity_events = [self.xconn.request_opacity(self.window).unpack()]
        self.keep_going = True
        self.done = False

    def run(self):
        """Record opacity changes until stop signal received."""
        while self.keep_going:
            opacity = self.xconn.request_opacity(self.window).unpack()
            if opacity != self.opacity_events[-1]:
                self.opacity_events.append(opacity)
        self.done = True
        self.xconn.conn.disconnect()

    def report(self):
        """Send the stop signal and report changes in _NET_WM_WINDOW_OPACITY."""
        # Give the x server a little time to catch up with requests
        sleep(0.01)
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
