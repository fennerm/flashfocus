"""Helper functions/classes for unit tests"""
from __future__ import division

from threading import Thread
import sys
from time import sleep

from gi.repository import Gtk
from plumbum.cmd import xdotool
from xcffib import xproto

import flashfocus.xutil as xutil


class WindowSession:
    """A session of blank windows for testing"""
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

    def destroy(self):
        """Tear down the window session"""
        for window in self.windows:
            window.destroy()


def change_focus(window):
    """Change the active window"""
    xdotool('windowactivate', window)


class WindowWatcher(Thread):
    """Watch a window for changes in opacity."""
    def __init__(self, window):
        super(WindowWatcher, self).__init__()
        self.window = window
        self.opacity_events = [xutil.request_opacity(self.window).unpack()]
        self.keep_going = True
        self.done = False

    def run(self):
        """Record opacity changes until stop signal received."""
        while self.keep_going:
            opacity = xutil.request_opacity(self.window).unpack()
            if opacity != self.opacity_events[-1]:
                self.opacity_events.append(opacity)
        self.done = True

    def report(self):
        """
        Send the stop signal and return all changes in _NET_WM_WINDOW_OPACITY.
        """
        self.keep_going = False
        while not self.done:
            pass
        return self.opacity_events


class ExitAfter(object):
    """
    Callable that will exits the entire thread after `limit` calls
    """
    def __init__(self, limit):
        self.limit = limit
        self.calls = 0

    def __call__(self, window):
        """Increment the call count and exit if > `limit`"""
        self.calls += 1
        if self.calls > self.limit:
            sys.exit()
