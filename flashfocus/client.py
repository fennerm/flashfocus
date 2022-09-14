"""Communicating with the flashfocus server via unix socket."""
import logging
import socket
from queue import Queue

from flashfocus.compat import get_focused_window
from flashfocus.display import WMEventType
from flashfocus.producer import ProducerThread
from flashfocus.sockets import init_client_socket, init_server_socket


def client_request_flash() -> None:
    """Request that the server flashes the current window."""
    logging.debug("Connecting to the flashfocus daemon...")
    sock = init_client_socket()
    logging.debug("Connection established, sending flash request...")
    # Just send a single byte to the server. Contents are unimportant.
    sock.sendall(bytearray("1", encoding="UTF-8"))


class ClientMonitor(ProducerThread):
    """Queue flash requests from clients."""

    def __init__(self, queue: Queue) -> None:
        super().__init__(queue)
        self.sock = init_server_socket()
        self.ready = True

    def run(self) -> None:
        """Queue client request flashes."""
        while self.keep_going:
            try:
                self.sock.recv(1)
            except socket.timeout:
                continue
            logging.debug("Received a flash request from client...")
            focused = get_focused_window()
            if focused is not None:
                self.queue_window(focused, WMEventType.CLIENT_REQUEST)
            else:
                logging.debug("Focused window is undefined, ignoring request...")

    def stop(self) -> None:
        super().stop()
        logging.debug("Disconnecting socket...")
        self.sock.close()
