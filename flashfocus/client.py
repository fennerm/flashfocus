"""Communicating with the flashfocus server via unix socket."""
from logging import info

from flashfocus.sockets import init_client_socket


def client_request_flash():
    """Request that the server flashes the current window."""
    info("Connecting to the flashfocus daemon...")
    sock = init_client_socket()
    info("Connection established, sending flash request...")
    # Just send a single byte to the server. Contents are unimportant.
    sock.sendall(bytearray("1", encoding="UTF-8"))
