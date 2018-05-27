"""Code for flashing windows."""
from __future__ import division

from logging import info
from threading import Thread
from time import sleep

from xcffib.xproto import WindowError

from flashfocus.xutil import set_opacity


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

    def __init__(
        self, time, flash_opacity, default_opacity, simple, ntimepoints
    ):
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

    def flash(self, window):
        """Flash a window."""
        info("Flashing window %s", str(window))
        if self.default_opacity == self.flash_opacity:
            return

        if window in self.progress:
            try:
                self.progress[window] = 0
            except KeyError:
                # This happens in rare case that window is deleted from progress
                # after first if statement
                self.flash(window)
        else:
            p = Thread(target=self._flash, args=[window])
            p.daemon = True
            p.start()

    def set_default_opacity(self, window):
        """Set the opacity of a window to its default."""
        # This needs to occur in a separate thread or Xorg freaks out and
        # doesn't allow further changes to window properties
        p = Thread(target=set_opacity, args=(window, self.default_opacity))
        p.daemon = True
        p.start()

    def _compute_flash_series(self):
        """Calculate the series of opacity values for the flash animation.

        Given the default window opacity, and the flash opacity, this method
        calculates a smooth series of intermediate opacity values.
        """
        opacity_diff = self.default_opacity - self.flash_opacity

        flash_series = [
            self.flash_opacity + ((x / self.ntimepoints) * opacity_diff)
            for x in range(self.ntimepoints)
        ]
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
                target_opacity = self.flash_series[self.progress[window]]
                set_opacity(window, target_opacity)
                sleep(self.timechunk)
                self.progress[window] += 1

            info("Resetting window %s opacity to default", window)
            set_opacity(window, self.default_opacity)

        except WindowError:
            info(
                "Attempted to draw to nonexistant window %s, ignoring...",
                str(window),
            )
        finally:
            del self.progress[window]
