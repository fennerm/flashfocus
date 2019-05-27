"""Communicating with the flashfocus server via unix socket."""
import logging

from flashfocus.sockets import init_client_socket


def client_request_flash():
    """Request that the server flashes the current window."""
    logging.info("Connecting to the flashfocus daemon...")
    sock = init_client_socket()
    logging.info("Connection established, sending flash request...")
    # Just send a single byte to the server. Contents are unimportant.
    sock.sendall(bytearray("1", encoding="UTF-8"))
