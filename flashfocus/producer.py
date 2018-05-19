"""Produce work for the flashfocus server."""
from logging import info
import socket
from threading import Thread

from xcffib.xproto import MapNotifyEvent, PropertyNotifyEvent
import xpybutil
from xpybutil.ewmh import get_active_window
from xpybutil.icccm import set_wm_name_checked
from xpybutil.util import get_atom_name

from flashfocus.xutil import create_message_window, destroy_window
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
        xpybutil.window.listen(
            xpybutil.root, "PropertyChange", "SubstructureNotify"
        )
        xpybutil.window.listen(self.message_window, "PropertyChange")
        while self.keep_going:
            event = xpybutil.conn.wait_for_event()
            if isinstance(event, PropertyNotifyEvent):
                self._handle_property_change(event)
            elif isinstance(event, MapNotifyEvent):
                self._handle_new_mapped_window(event)

    def stop(self):
        set_wm_name_checked(self.message_window, "KILL").check()
        super(XHandler, self).stop()
        destroy_window(self.message_window)

    def _handle_new_mapped_window(self, event):
        """Handle a new mapped window event."""
        info("New window mapped...")
        self.queue_window(event.window, "new_window")

    def _handle_property_change(self, event):
        """Handle a property change on a watched window."""
        atom = get_atom_name(event.atom)
        if atom == "_NET_ACTIVE_WINDOW":
            info("Focus shifted...")
            focused = get_active_window().reply()
            self.queue_window(focused, "focus_shift")
        elif atom == "WM_NAME" and event.window == self.message_window:
            # Kill signal from server
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
                info("Received a flash request from client...")
                focused = xpybutil.ewmh.get_active_window().reply()
                self.queue_window(focused, "client_request")

    def stop(self):
        super(ClientMonitor, self).stop()
        info("Disconnecting socket...")
        self.sock.close()
