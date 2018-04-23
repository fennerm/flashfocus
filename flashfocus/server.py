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

from xcffib import ConnectionException
import xpybutil
import xpybutil.ewmh
import xpybutil.window

from flashfocus.flasher import Flasher
from flashfocus.sockets import init_server_socket
from flashfocus.xutil import focus_shifted


class FlashServer:
    """Handle focus shifts and client (flash_window) requests.

    Parameters
    ----------
    flash_opacity: float (between 0 and 1)
        Flash opacity.
    default_opacity: float (between 0 and 1)
        Windows are restored to this opacity post-flash.
    time: float > 0
        Flash interval in milliseconds.
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
