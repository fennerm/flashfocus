"""Monitor focus and flash windows."""
from __future__ import division

import os
import logging
from logging import info as log
from time import sleep

from xcffib.xproto import WindowError

import flashfocus.xutil as xutil

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))


class FocusMonitor:
    """Main flashfocus class in charge of flashing windows on focus shift.

    Parameters
    ----------
    flash_opacity: float
        Flash opacity as a decimal between 0 and 1
    time: float
        Flash interval in seconds

    """

    def __init__(self, flash_opacity, time):
        self.flash_opacity = flash_opacity
        self.time = time

    def flash_window(self, window):
        """Briefly change the opacity of a Xorg window."""
        log('Flashing window %s', str(window))
        try:
            opacity = xutil.request_opacity(window).unpack()

            if opacity != self.flash_opacity:
                log('Current opacity = %s', str(opacity))
                log('Setting opacity to %s', str(self.flash_opacity))
                xutil.set_opacity(window, opacity=self.flash_opacity)
                log('Waiting %ss...', self.time)
                sleep(self.time)
                if opacity:
                    xutil.set_opacity(window, opacity)
                else:
                    xutil.delete_opacity(window)
            else:
                log('Window opacity is already %s, won\'t bother flashing...',
                    str(opacity))
        except WindowError:
            log('Attempted to flash a nonexistant window %s, ignoring...',
                str(window))

    def monitor_focus(self):
        """Wait for changes in focus and flash windows."""
        xutil.start_watching_properties(xutil.ROOT_WINDOW)

        while True:
            xutil.wait_for_focus_shift()
            log("Focus shifted...")
            focused_window = xutil.request_focus().unpack()
            self.flash_window(focused_window)
