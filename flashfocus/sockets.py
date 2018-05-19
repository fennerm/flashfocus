"""Unix socket initialization.

The flashfocus client and server communicate using a simple datagram unix
socket.
"""
import os
import socket
import sys

from flashfocus.syspaths import RUNTIME_DIR

SOCKET_ADDRESS = os.path.join(RUNTIME_DIR, "flashfocus_socket")


def init_client_socket():
    """Initialize and connect the client unix socket."""
    sock = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_DGRAM)
    try:
        sock.connect(SOCKET_ADDRESS)
    except socket.error:
        sys.exit(
            "Error: Couldn't connect to the flashfocus daemon!\n"
            "=> Please check that the flashfocus daemon is running."
        )
    return sock


def init_server_socket():
    """Initialize and bind the server unix socket."""
    try:
        os.unlink(SOCKET_ADDRESS)
    except (OSError, EnvironmentError):
        pass
    sock = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_DGRAM)
    sock.bind(SOCKET_ADDRESS)
    sock.settimeout(1)
    return sock
