"""Code for flashing windows."""
from __future__ import division

from logging import info
from threading import Thread
from time import sleep

from xcffib.xproto import WindowError
import xpybutil
import xpybutil.ewmh


class Flasher:
    """Creates smooth window flash animations.

    If a flash is requested on an already flashing window, the first request is
    restarted and the second request is ignored. This ensures that Flasher
    threads do not try to draw to the same window at the same time.

    Parameters
    ----------
    time: float
        Flash interval in milliseconds
    flash_opacity: float
        Flash opacity as a decimal between 0 and 1
    default_opacity: float
        Default opacity for windows as a decimal between 0 and 1. Windows are
        restored to this opacity after a flash.
    ntimepoints: int
        Number of timepoints in the flash animation. Higher values will lead to
        smoother animations at the cost of increased X server requests.
        Ignored if simple is True.
    simple: bool
        If True, don't animate flashes. Setting this parameter improves
        performance but causes rougher opacity transitions.

    Attributes
    ----------
    flash_series: List[float]
        The series of opacity transitions during a flash.
    progress: Dict[int, int]
        Keys are window ids for windows that are currently being flashed. Values
        are indices in the flash_series which define the progress in the flash
        animation.
    timechunk: float
        Number of seconds between opacity transitions.

    """
    def __init__(self, time, flash_opacity, default_opacity,
                 simple, ntimepoints):
        self.default_opacity = default_opacity
        self.flash_opacity = flash_opacity
        self.time = time / 1000
        if simple:
            self.ntimepoints = 1
            self.timechunk = time
            self.flash_series = [flash_opacity]
        else:
            self.ntimepoints = ntimepoints
            self.timechunk = self.time / self.ntimepoints
            self.flash_series = self._compute_flash_series()
        self.progress = dict()

    def flash_window(self, window):
        """Flash a window."""
        info('Flashing window %s', str(window))
        if window in self.progress:
            try:
                self.progress[window] = 0
            except KeyError:
                # This occurs when a flash terminates just as we're trying to
                # restart it. In this case we just start over.
                self.flash_window(window)
        else:
            p = Thread(target=self._flash, args=[window])
            p.daemon = True
            p.start()

    def _compute_flash_series(self):
        """Calculate the series of opacity values for the flash animation.

        Given the default window opacity, and the flash opacity, this method
        calculates a smooth series of intermediate opacity values.
        """
        info('Computing flash series from %s to %s',
             self.flash_opacity,
             self.default_opacity)
        opacity_diff = self.default_opacity - self.flash_opacity

        flash_series = [self.flash_opacity +
                        ((x / self.ntimepoints) * opacity_diff)
                        for x in range(self.ntimepoints)]
        info('Computed flash series = %s', flash_series)
        return flash_series

    def _flash(self, window):
        """Flash a window.

        This function just iterates across `self.flash_series` and modifies the
        window opacity accordingly. It waits `self.timechunk` between
        modifications.
        """
        try:
            self.progress[window] = 0
            while self.progress[window] < self.ntimepoints:
                xpybutil.ewmh.set_wm_window_opacity_checked(
                    window, self.flash_series[self.progress[window]]).check()
                sleep(self.timechunk)
                self.progress[window] += 1

            info('Resetting opacity to default')
            xpybutil.ewmh.set_wm_window_opacity_checked(
                window, self.default_opacity).check()

        except WindowError:
            info('Attempted to draw to nonexistant window %s, ignoring...',
                 str(window))
        finally:
            # The window is no longer being flashed.
            del self.progress[window]
