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
from signal import (
    default_int_handler,
    SIGINT,
    signal,
)
import socket
from threading import Thread
from time import sleep

from xcffib.xproto import WindowError

from flashfocus.sockets import init_server_socket
from flashfocus.xutil import XConnection


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
    xconn: flashfocus.xutil.XConnection
        The connection to the X server.
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
        self.xconn = XConnection()
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

    def already_flashing(self, window):
        """Return True if the flasher is already flashing a given window."""
        return window in self.progress

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
                self.xconn.set_opacity(
                    window, self.flash_series[self.progress[window]])
                sleep(self.timechunk)
                self.progress[window] += 1
        except WindowError:
            info('Attempted to flash a nonexistant window %s, ignoring...',
                 str(window))
        else:
            info('Resetting opacity to default')
            if self.default_opacity == 1:
                self.xconn.delete_opacity(window)
            else:
                self.xconn.set_opacity(window, self.default_opacity)
        finally:
            # The window is no longer being flashed.
            del self.progress[window]


class FlashServer:
    """Monitor focus shifts and handle `flash_window` requests.

    Parameters
    ----------
    flash_opacity: float
        Flash opacity as a decimal between 0 and 1
    default_opacity: float
        Default opacity for windows as a decimal between 0 and 1. Windows are
        restored to this opacity after a flash.
    time: float
        Flash interval in seconds
    ntimepoints: int
        Number of timepoints in the flash animation. Higher values will lead to
        smoother animations at the cost of increased X server requests.
        Ignored if simple is True.
    simple: bool
        If True, don't animate flashes. Setting this parameter improves
        performance but causes rougher opacity transitions.

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
        # requests. On i3 when a window is closed, the next window is flashed
        # three times without this guard.
        self.prev_focus = None
        self.producers = [Thread(target=self._queue_focus_shift_tasks),
                          Thread(target=self._queue_client_tasks)]

        # Ensure that SIGINTs are handled correctly
        signal(SIGINT, default_int_handler)
        self.target_windows = Queue()
        self.xconn = XConnection(timeout=1)
        self.sock = init_server_socket()
        self.keep_going = True

    def event_loop(self):
        """Wait for changes in focus and flash windows."""
        try:
            for producer in self.producers:
                producer.start()
            while self.keep_going:
                self._flash_queued_window()
        except (KeyboardInterrupt, SystemExit):
            info('Interrupt received, shutting down...')
        finally:
            info('Killing threads...')
            self.keep_going = False
            for producer in self.producers:
                producer.join()
            info('Disconnecting from X session...')
            self.xconn.conn.disconnect()
            info('Disconnecting socket...')
            self.sock.close()

    def _queue_focus_shift_tasks(self):
        """Wait for the focused window to change and queue it for flashing."""
        self.xconn.start_watching_properties(self.xconn.root_window)
        while self.keep_going:
            if self.xconn.has_events():
                if self.xconn.focus_shifted():
                    info('Focus shifted...')
                    focused = self.xconn.request_focus().unpack()
                    self.target_windows.put(tuple([focused, 'focus_shift']))

    def _queue_client_tasks(self):
        """Wait for flash_window calls and queue window for flashing."""
        while self.keep_going:
            try:
                self.sock.recv(1)
            except socket.timeout:
                pass
            else:
                info('Received a flash request from client...')
                focused = self.xconn.request_focus().unpack()
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
