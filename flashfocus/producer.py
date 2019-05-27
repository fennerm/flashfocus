"""Produce work for the flashfocus server."""
import logging
import socket
from threading import Thread

from xcffib.xproto import CreateNotifyEvent, PropertyNotifyEvent
import xpybutil
from xpybutil.ewmh import get_active_window
from xpybutil.icccm import set_wm_name_checked
from xpybutil.util import get_atom_name

from flashfocus.xutil import create_message_window, destroy_window, list_mapped_windows
from flashfocus.sockets import init_server_socket


class Producer(Thread):
    """Queue windows to be handled by the `FlashServer`.

    Parameters
    ----------
    queue: queue.Queue
        A queue which is shared among `Producer` instances

    """

    def __init__(self, queue):
        super(Producer, self).__init__()
        self.queue = queue
        self.keep_going = True

    def queue_window(self, window, type):
        """Add a window to the queue."""
        self.queue.put(tuple([window, type]))

    def stop(self):
        self.keep_going = False
        self.join()


class XHandler(Producer):
    """Parse events from the X-server and pass them on to FlashServer"""

    def __init__(self, queue):
        super(XHandler, self).__init__(queue)
        self.type = "focus_shift"
        self.message_window = create_message_window()

    def run(self):
        xpybutil.window.listen(xpybutil.root, "PropertyChange", "SubstructureNotify")
        xpybutil.window.listen(self.message_window, "PropertyChange")
        while self.keep_going:
            event = xpybutil.conn.wait_for_event()
            if isinstance(event, PropertyNotifyEvent):
                self._handle_property_change(event)
            elif isinstance(event, CreateNotifyEvent):
                self._handle_new_mapped_window(event)

    def stop(self):
        set_wm_name_checked(self.message_window, "KILL").check()
        super(XHandler, self).stop()
        destroy_window(self.message_window)

    def _handle_new_mapped_window(self, event):
        """Handle a new mapped window event."""
        logging.info("Window %s mapped...", event.window)
        # Check that window is visible so that we don't accidentally set
        # opacity of windows which are not for display. Without this step
        # window opacity can become frozen and stop responding to flashes.
        # TODO this doesn't actually seem to work if the window is on another desktop, not sure why.
        if event.window in list_mapped_windows():
            self.queue_window(event.window, "new_window")
        else:
            logging.info("Window %s is not visible, ignoring...", event.window)

    def _handle_property_change(self, event):
        """Handle a property change on a watched window."""
        atom_name = get_atom_name(event.atom)
        if atom_name == "_NET_ACTIVE_WINDOW":
            focused_window = get_active_window().reply()
            logging.info("Focus shifted to %s", focused_window)
            self.queue_window(focused_window, "focus_shift")
        elif atom_name == "WM_NAME" and event.window == self.message_window:
            # Received kill signal from server -> terminate the thread
            self.keep_going = False


class ClientMonitor(Producer):
    """Queue flash requests from clients."""

    def __init__(self, queue):
        super(ClientMonitor, self).__init__(queue)
        self.type = "client_request"
        self.sock = init_server_socket()

    def run(self):
        """Queue client request flashes."""
        while self.keep_going:
            try:
                self.sock.recv(1)
            except socket.timeout:
                pass
            else:
                logging.info("Received a flash request from client...")
                focused = xpybutil.ewmh.get_active_window().reply()
                self.queue_window(focused, "client_request")

    def stop(self):
        super(ClientMonitor, self).stop()
        logging.info("Disconnecting socket...")
        self.sock.close()
