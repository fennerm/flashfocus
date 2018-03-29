"""Monitor focus and flash windows."""
from __future__ import division

from threading import Thread
import os
import logging
from logging import info as log
from time import sleep

from xcffib.xproto import WindowError

import flashfocus.xutil as xutil

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))


class Flasher:
    """Main flashfocus class in charge of flashing windows on focus shift.

    Parameters
    ----------
    flash_opacity: float
        Flash opacity as a decimal between 0 and 1
    time: float
        Flash interval in seconds
    ntimepoints: int
        Number of timepoints in the flash animation. Higher values will lead to
        smoother animations with the cost of increased X server requests.
        Ignored if simple is True.
    simple: bool
        If True, don't animate flashes. Setting this parameter improves
        performance but causes rougher opacity transitions.

    """
    def __init__(self, flash_opacity, time, ntimepoints, simple):
        self.flash_opacity = flash_opacity
        self.time = time
        self.simple = simple
        if simple:
            self.ntimepoints = 1
            self.timechunk = time
        else:
            self.ntimepoints = ntimepoints
            self.timechunk = time / self.ntimepoints
        self.flash_series_hash = {}
        self.locked_windows = set()

    def compute_flash_series(self, current_opacity):
        """Calculate the series of opacity values for the flash animation.

        Given the opacity of a window before a flash, and the flash opacity,
        this method calculates a smooth series of intermediate opacity values.
        Results of the calculation are hashed to speed up later flashes.
        """
        if not current_opacity:
            current_opacity = 1

        try:
            return self.flash_series_hash[current_opacity]
        except KeyError:
            log('Computing flash series for opacity = %s', current_opacity)
            opacity_diff = current_opacity - self.flash_opacity

            flash_series = [self.flash_opacity +
                            ((x / self.ntimepoints) * opacity_diff)
                            for x in range(self.ntimepoints)]
            log('Computed flash series = %s', flash_series)
            self.flash_series_hash[current_opacity] = flash_series
            return flash_series

    def flash_window(self, window):
        """Briefly change the opacity of a Xorg window."""
        log('Flashing window %s', str(window))
        try:
            pre_flash_opacity = xutil.request_opacity(window).unpack()

            log('Current opacity = %s', str(pre_flash_opacity))
            log('Beginning flash animation...')
            flash_series = self.compute_flash_series(pre_flash_opacity)
            for opacity in flash_series:
                xutil.set_opacity(window, opacity)
                sleep(self.timechunk)
            log('Resetting opacity to default')
            if pre_flash_opacity:
                xutil.set_opacity(window, pre_flash_opacity)
            else:
                xutil.delete_opacity(window)
        except WindowError:
            log('Attempted to flash a nonexistant window %s, ignoring...',
                str(window))
        log('Unlocking window %s', window)
        self.locked_windows.discard(window)

    def monitor_focus(self):
        """Wait for changes in focus and flash windows."""
        xutil.start_watching_properties(xutil.ROOT_WINDOW)

        # We keep track of the previously focused window so that the same window
        # is never flashed twice in a row. On i3 when a window is closed, the
        # next window is flashed three times without this guard.
        prev_focus = None
        focused = None

        while True:
            xutil.wait_for_focus_shift()
            prev_focus = focused
            focused = xutil.request_focus().unpack()
            log('Focus shifted to window %s', focused)

            if focused not in self.locked_windows and focused != prev_focus:
                # Further flash requests are ignored for the window until the
                # thread completes.
                log('Locking window %s', focused)
                self.locked_windows.add(focused)
                p = Thread(target=self.flash_window, args=[focused])
                p.daemon = True
                p.start()

            elif focused == prev_focus:
                log("Window %s was just flashed, ignoring...", focused)

            elif focused in self.locked_windows:
                log("Window %s is locked, ignoring...", focused)
