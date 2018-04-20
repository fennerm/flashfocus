"""Flash windows on focus."""
from __future__ import division

from logging import info
try:
    from queue import (
        Empty,
        Queue,
    )
except ImportError:
    from Queue import (
        Empty,
        Queue,
    )
from select import select
from signal import (
    default_int_handler,
    SIGINT,
    signal,
)
import socket
from threading import Thread
from time import sleep

from xcffib import ConnectionException
from xcffib.xproto import WindowError
import xpybutil
import xpybutil.ewmh
import xpybutil.window

from flashfocus.xutil import focus_shifted
from flashfocus.sockets import init_server_socket


class Flasher:
    """Creates smooth window flash animations.

    If a flash is requested on an already flashing window, the first request is
    restarted and the second request is ignored. This ensures that Flasher
    threads do not try to draw to the same window at the same time.

    Parameters
    ----------
    time: float
        Flash interval in seconds
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
        if simple:
            self.ntimepoints = 1
            self.timechunk = time
            self.flash_series = [flash_opacity]
        else:
            self.ntimepoints = ntimepoints
            self.timechunk = time / self.ntimepoints
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


TIMEOUT = 1


class FlashServer:
    """Handle focus shifts and client (flash_window) requests.

    Parameters
    ----------
    flash_opacity: float (between 0 and 1)
        Flash opacity.
    default_opacity: float (between 0 and 1)
        Windows are restored to this opacity post-flash.
    time: float > 0
        Flash interval in seconds.
    ntimepoints: int
        Number of timepoints in the flash animation. Higher values will lead to
        smoother animations at the cost of increased X server requests.
        Ignored if simple is True.
    simple: bool
        If True, don't animate flashes. Setting this parameter improves
        performance but opacity transitions are less smooth.

    """
    def __init__(self,
                 default_opacity,
                 flash_opacity,
                 time,
                 ntimepoints,
                 simple):
        self.locked_windows = set()
        self.flasher = Flasher(time=time,
                               flash_opacity=flash_opacity,
                               default_opacity=default_opacity,
                               simple=simple,
                               ntimepoints=ntimepoints)
        # We keep track of the previously focused window so that the same
        # window is never flashed twice in a row (except for `flash_window`
        # requests). On i3 when a window is closed, the next window is flashed
        # three times without this guard.
        self.prev_focus = 0
        self.producers = [Thread(target=self._queue_focus_shift_tasks),
                          Thread(target=self._queue_client_tasks)]

        # Ensure that SIGINTs are handled correctly
        signal(SIGINT, default_int_handler)
        self.target_windows = Queue()
        self.sock = init_server_socket()
        self.keep_going = True

    def event_loop(self):
        """Wait for changes in focus or client requests and queues flashes."""
        try:
            for producer in self.producers:
                producer.start()
            while self.keep_going:
                self._flash_queued_window()
        except (KeyboardInterrupt, SystemExit):
            info('Interrupt received, shutting down...')
        finally:
            info('Disconnecting from X session...')
            xpybutil.conn.disconnect()
            info('Killing threads...')
            self.keep_going = False
            for producer in self.producers:
                producer.join()
            info('Disconnecting socket...')
            self.sock.close()

    def _queue_focus_shift_tasks(self):
        """Queue focus shift flashes."""
        xpybutil.window.listen(xpybutil.root, 'PropertyChange')

        while self.keep_going:
            try:
                if focus_shifted():
                    info('Focus shifted...')
                    focused = xpybutil.ewmh.get_active_window().reply()
                    self.target_windows.put(tuple([focused, 'focus_shift']))
            except ConnectionException:
                pass

    def _queue_client_tasks(self):
        """Queue client request flashes."""
        while self.keep_going:
            try:
                self.sock.recv(1)
            except socket.timeout:
                pass
            else:
                info('Received a flash request from client...')
                focused = xpybutil.ewmh.get_active_window().reply()
                self.target_windows.put(tuple([focused, 'client_request']))

    def _flash_queued_window(self):
        """Pop a window from the target_windows queue and initiate flash."""
        try:
            window, request_type = self.target_windows.get(timeout=1)
        except Empty:
            pass
        else:
            if window != self.prev_focus or request_type == 'client_request':
                self.flasher.flash_window(window)
            else:
                info("Window %s was just flashed, ignoring...", window)

            self.prev_focus = window
