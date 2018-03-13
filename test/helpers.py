'''Helper functions/classes for unit tests'''
from subprocess import PIPE
from time import sleep

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from plumbum.cmd import (
    xdotool,
    xprop,
)

from flashfocus.Xutil import MAX_OPACITY


class WindowSession:
    '''A session of blank windows for testing'''
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
        '''Tear down the window session'''
        for window in self.windows:
            window.destroy()


def change_focus(window_id):
    '''Change the active window'''
    xdotool('windowactivate', window_id)


class WindowWatcher:
    '''Watch a window for changes in opacity'''
    def __init__(self, window):
        self.process = xprop.popen(['-spy', '-id', window], stdout=PIPE)
        sleep(0.05)
        self.raw_log = None
        self.opacity_events = []

    def report(self):
        self.process.kill()
        self.raw_log = self.process.communicate()[0].decode('utf-8').split('\n')

        for line in self.raw_log:
            if line.startswith('_NET_WM_WINDOW_OPACITY'):
                opacity = int(line.split(' ')[-1]) / MAX_OPACITY
                self.opacity_events.append(opacity)
        return self.opacity_events
