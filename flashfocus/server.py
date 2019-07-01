"""Flash windows on focus."""
from __future__ import division

import logging
from queue import Empty, Queue
from signal import default_int_handler, SIGINT, signal


from flashfocus.client import ClientMonitor
from flashfocus.compat import (
    disconnect_display_conn,
    DisplayHandler,
    list_mapped_windows,
    unset_all_window_opacity,
)
from flashfocus.config import Config
from flashfocus.display import WMError, WMMessage, WMMessageType
from flashfocus.router import FlashRouter, UnexpectedMessageType


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
    flash_lone_windows: str
        One of 'never', 'always', 'on_switch', 'on_open_close'

    Attributes
    ----------
    router: FlashRouter
        Object used to match window id's to flash parameters from the config
        file.
    keep_going: bool
        Setting this to False terminates the event loop (but does not initiate
        cleanup).
    producers: List[Thread]
        List of threads which produce work for the server.
    flash_requests: Queue
        Queue of flash jobs for the server to work through. Each item of the
        queue is a tuple of (window id, request type).

    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.router = FlashRouter(config)
        self.events: Queue = Queue()
        self.producers = [ClientMonitor(self.events), DisplayHandler(self.events)]
        self.keep_going = True
        self.ready = False

    def event_loop(self) -> None:
        """Wait for changes in focus or client requests and queues flashes."""
        logging.info("Initializing default window opacity...")
        self._set_all_window_opacity_to_default()
        try:
            logging.info("Initializing threads...")
            for producer in self.producers:
                producer.start()
            for producer in self.producers:
                while not producer.ready:
                    pass
            self.ready = True
            logging.info("Threads initialized, waiting for events...")
            while self.keep_going:
                self._flash_queued_window()
        except (KeyboardInterrupt, SystemExit):
            logging.warn("Interrupt received, shutting down...")
            self.shutdown()

    def shutdown(self, disconnect_from_wm: bool = True) -> None:
        """Cleanup after recieving a SIGINT."""
        self.keep_going = False
        self._kill_producers()
        logging.info("Resetting windows to full opacity...")
        unset_all_window_opacity()
        if disconnect_from_wm:
            logging.info("Disconnecting from X session...")
            disconnect_display_conn()

    def _flash_queued_window(self) -> None:
        """Pop a window from the flash_requests queue and initiate flash."""
        try:
            message = self.events.get(timeout=1)
        except Empty:
            return None

        try:
            self.router.route_request(message)
        except UnexpectedMessageType:
            logging.error(f"Unexpected request type - {message.type}. Aborting...")
            self.shutdown()
        except WMError:
            pass

    def _kill_producers(self) -> None:
        logging.info("Terminating threads...")
        for producer in self.producers:
            producer.stop()

    def _set_all_window_opacity_to_default(self) -> None:
        logging.info("Setting all windows to their default opacity...")
        for window in list_mapped_windows():
            self.router.route_request(WMMessage(window=window, type=WMMessageType.WINDOW_INIT))
