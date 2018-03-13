from logging import info as log
from plumbum.cmd import pgrep
from struct import unpack
from time import sleep
from warnings import warn

from flashfocus.Xutil import (
    delete_opacity_property,
    get_opacity_atom,
    request_focus,
    request_opacity,
    set_opacity,
)

class FlashServer(object):
    def __init__(self, opacity, time, socketfile='/tmp/flashfocus_socket'):
        self.flash_opacity = opacity
        self.time = time

    def flash_window(self, x_window_id):
        '''Briefly change the opacity of a Xorg window'''
        log('Flashing window %s', str(x_window_id))
        opacity = request_opacity(x_window_id).unpack()

        if opacity != self.flash_opacity:
            log('Current opacity = %s', str(opacity))
            log('Flashing now...')
            set_opacity(x_window_id, opacity=self.flash_opacity)
            log('Waiting %ss...', self.time)
            sleep(self.time)
            if opacity:
                set_opacity(x_window_id, opacity=opacity)
            else:
                delete_opacity_property(x_window_id)
        else:
            log('Window opacity is already %s, won\'t bother flashing...',
                str(opacity))

    def monitor_focus(self):
        '''Wait for changes in focus and flash windows'''
        # Add enterwindow/active window mask then wait for events
        # NEVERMIND MONITOR _NET_ACTIVE_WINDOW on the ROOT window
        #xprop -spy -root _NET_ACTIVE_WINDOW
        # mask = getattr(xproto.EventMask, 'PropertyChange')
        # CONN.core.ChangeWindowAttributesChecked(
        #     ROOT,
        #     xproto.CW.EventMask,
        #     mask).check()
        def on_window_focus(_, event):
            '''Change in focus hook'''
            x_window_id = str(event.container.window)
            self.flash_window(x_window_id)
            self.focused_window = x_window_id
            log('Waiting for focus shift...')

        self.i3.on('window::focus', on_window_focus)
        log('Waiting for focus shift...')
        self.i3.main()
