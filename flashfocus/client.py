"""Communicating with the flashfocus server via unix socket."""
import logging
import socket

import xpybutil

from flashfocus.producer import Producer
from flashfocus.sockets import init_client_socket, init_server_socket


def client_request_flash():
    """Request that the server flashes the current window."""
    logging.info("Connecting to the flashfocus daemon...")
    sock = init_client_socket()
    logging.info("Connection established, sending flash request...")
    # Just send a single byte to the server. Contents are unimportant.
    sock.sendall(bytearray("1", encoding="UTF-8"))


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
