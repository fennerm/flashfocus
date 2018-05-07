"""Flash windows on focus."""
from __future__ import division

from logging import (
    info,
    warn,
)
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

from xcffib.xproto import WindowError
import xpybutil
import xpybutil.window

from flashfocus.producer import (
    ClientMonitor,
    XHandler,
)
from flashfocus.rule import RuleMatcher


# Ensure that SIGINTs are handled correctly
signal(SIGINT, default_int_handler)


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
    flash_on_focus: bool
        If True, windows will be flashed on focus. Otherwise, windows will only
        be flashed on request.

    """
    def __init__(self,
                 default_opacity,
                 flash_opacity,
                 time,
                 ntimepoints,
                 simple,
                 rules,
                 flash_on_focus):
        self.matcher = RuleMatcher(
            defaults={
                'default_opacity': default_opacity,
                'flash_opacity': flash_opacity,
                'simple': simple,
                'rules': rules,
                'time': time,
                'ntimepoints': ntimepoints,
                'flash_on_focus': flash_on_focus},
            rules=rules)

        # We keep track of the previously focused window so that the same
        # window is never flashed twice in a row (except for `flash_window`
        # requests). In i3 when a window is closed, the next window is flashed
        # three times consecutively without this guard.
        self.prev_focus = 0
        self.target_windows = Queue()
        self.producers = [ClientMonitor(self.target_windows),
                          XHandler(self.target_windows, default_opacity)]
        self.keep_going = True

    def event_loop(self):
        """Wait for changes in focus or client requests and queues flashes."""
        try:
            for producer in self.producers:
                producer.start()
            while self.keep_going:
                self._flash_queued_window()
        except (KeyboardInterrupt, SystemExit):
            warn('Interrupt received, shutting down...')
            self.shutdown()

    def shutdown(self, disconnect_from_xorg=True):
        """Cleanup after recieving a SIGINT."""
        self.keep_going = False
        info('Killing threads...')
        for producer in self.producers:
            producer.stop()
        if disconnect_from_xorg:
            info('Disconnecting from X session...')
            xpybutil.conn.disconnect()

    def _flash_queued_window(self):
        """Pop a window from the target_windows queue and initiate flash."""
        try:
            window, request_type = self.target_windows.get(timeout=1)
        except Empty:
            pass
        else:
            if window != self.prev_focus or request_type != 'focus_shift':
                try:
                    self.matcher.direct_request(window, request_type)
                except WindowError:
                    pass
            else:
                info('Window %s was just flashed, ignoring...', window)
            self.prev_focus = window
