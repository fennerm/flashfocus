"""Monitor focus and flash windows."""
from __future__ import division

from logging import info
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
from threading import Thread
from time import sleep

from xcffib.xproto import WindowError

from flashfocus.sockets import init_server_socket
import flashfocus.xutil as xutil


class Flasher:
    def __init__(self, time, flash_opacity, default_opacity,
                 simple, ntimepoints):
        if simple:
            self.ntimepoints = 1
            self.timechunk = time
            self.flash_series = [flash_opacity]
        else:
            self.ntimepoints = ntimepoints
            self.timechunk = time / self.ntimepoints
            self.flash_series = self.compute_flash_series(
                default_opacity,
                flash_opacity)

    def compute_flash_series(self, default_opacity, flash_opacity):
        """Calculate the series of opacity values for the flash animation.

        Given the opacity of a window before a flash, and the flash opacity,
        this method calculates a smooth series of intermediate opacity values.
        Results of the calculation are hashed to speed up later flashes.
        """
        info('Computing flash series from %s to %s',
             flash_opacity,
             default_opacity)
        opacity_diff = default_opacity - flash_opacity

        flash_series = [flash_opacity +
                        ((x / self.ntimepoints) * opacity_diff)
                        for x in range(self.ntimepoints)] + default_opacity
        info('Computed flash series = %s', flash_series)
        return flash_series

    def flash_window(self, window):
        """Briefly change the opacity of a Xorg window."""
        info('Flashing window %s', str(window))
        try:
            pre_flash_opacity = xutil.request_opacity(window).unpack()

            info('Current opacity = %s', str(pre_flash_opacity))
            info('Beginning flash animation...')
            flash_series = self.compute_flash_series(pre_flash_opacity)
            for opacity in flash_series:
                xutil.set_opacity(window, opacity)
                sleep(self.timechunk)
            info('Resetting opacity to default')
            if pre_flash_opacity:
                xutil.set_opacity(window, pre_flash_opacity)
            else:
                xutil.delete_opacity(window)
        except WindowError:
            info('Attempted to flash a nonexistant window %s, ignoring...',
                 str(window))


class FlashServer:
    """Main flashfocus class.

    Waits for focused window to change then flashes it.

    Parameters
    ----------
    flash_opacity: float
        Flash opacity as a decimal between 0 and 1
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
    def __init__(self, flash_opacity, time, ntimepoints, simple):
        self.locked_windows = set()
        self.tasks = Queue()
        self.flasher = Flasher(time, flash_opacity, simple, ntimepoints)
        # We keep track of the previously focused window so that the same
        # window is never flashed twice in a row. On i3 when a window is
        # closed, the next window is flashed three times without this guard.
        self.prev_focus = None

    def event_loop(self):
        """Wait for changes in focus and flash windows."""
        try:
            handlers = [Thread(target=self.queue_focus_shift_tasks),
                        Thread(target=self.queue_client_tasks)]
            for handler in handlers:
                handler.start()

            while True:
                self.process_task()
        except (KeyboardInterrupt, SystemExit):
            info('Interrupt received, shutting down...')
        finally:
            self.conn.disconnect()

    def queue_focus_shift_tasks(self):
        xutil.start_watching_properties(xutil.ROOT_WINDOW)
        while True:
            xutil.wait_for_focus_shift()
            focused = xutil.request_focus().unpack()
            self.tasks.put(tuple(focused, 'focus_shift'))

    def queue_client_tasks(self):
        try:
            sock = init_server_socket()
            while True:
                client_connection = sock.accept()[0]
                client_connection.recv(1)
                focused = xutil.request_focus().unpack()
                self.tasks.put(tuple(focused, 'client_request'))
        finally:
            sock.close()

    def process_task(self):
        window, request_type = self.tasks.get()

        if request_type == 'focus_shift':
            info('Focus shifted to window %s', window)
        else:
            info('Received an external request to flash window %s',
                 window)

        if window != self.prev_focus or request_type == 'client_request':
            # Further flash requests are ignored for the window until
            # the thread completes.
            p = Thread(target=self.flasher.flash_window, args=[window])
            p.daemon = True
            p.start()

        elif window == self.prev_focus:
            info("Window %s was just flashed, ignoring...", window)

        self.prev_focus = window
