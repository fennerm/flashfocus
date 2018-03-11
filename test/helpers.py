import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class WindowSession(object):
    '''A session of blank windows for testing'''
    def __init__(self):
        window1 = Gtk.Window(title='window1')
        window1.show()
        window2 = Gtk.Window(title='window2')
        window2.show()

        self.windows = [window1, window2]
        # Each root window spawns a subwindow with an incremented id
        # so we increment each window id accordingly. This seems like it could
        # lead to race conditions so ideally I should find a better way to do 
        # this later.
        self.ids = [w.get_property('window').get_xid() + 4 for w in self.windows]

    def destroy(self):
        for window in self.windows:
            window.destroy()
