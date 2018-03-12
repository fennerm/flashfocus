'''Helper functions/classes for unit tests'''
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from plumbum import BG
from plumbum.cmd import (
    xdotool,
    xprop,
)

from flashfocus.Xutil import (
    request_opacity,
    unpack_cookie,
)

class WindowSession(object):
    '''A session of blank windows for testing'''
    def __init__(self):
        window1 = Gtk.Window(title='window1')
        window1.show()
        window2 = Gtk.Window(title='window2')
        window2.show()

        self.windows = [window1, window2]
        self.ids = [
            w.get_property('window').get_xid() for w in self.windows]

    def destroy(self):
        '''Tear down the window session'''
        for window in self.windows:
            window.destroy()


def change_focus(window_id):
    '''Change the active window'''
    xdotool('windowactivate', window_id)


def get_opacity(window_id):
    cookie = request_opacity(window_id)
    opacity = unpack_cookie(cookie)
    return opacity


def watch_window(window, logfile):
    (xprop['-spy', '-id', window] > logfile) & BG
