"""Unix socket initialization.

The flashfocus client and server communicate using a simple datagram unix
socket.
"""
import os
import socket
import sys


SOCKET_NAME = 'flashfocus_socket'
NON_XDG_SOCKET_DIR = '/tmp'


def choose_socket_address():
    """Choose the socket address for the server/client to bind to.

    Tries to use XDG_RUNTIME_DIR if it is defined, otherwise uses /tmp.
    """
    xdg_runtime_dir = os.environ.get('XDG_RUNTIME_DIR')
    if xdg_runtime_dir:
        socket_dir = xdg_runtime_dir
    else:
        socket_dir = NON_XDG_SOCKET_DIR
    socket_address = os.path.join(socket_dir, SOCKET_NAME)
    return socket_address


def init_client_socket():
    """Initialize and connect the client unix socket."""
    socket_address = choose_socket_address()
    sock = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_DGRAM)
    try:
        sock.connect(socket_address)
    except socket.error:
        sys.exit('Error: Couldn\'t connect to the flashfocus daemon!\n'
                 '=> Please check that the flashfocus daemon is running.')
    return sock


def init_server_socket():
    """Initialize and bind the server unix socket."""
    socket_address = choose_socket_address()
    try:
        os.unlink(socket_address)
    except (OSError, EnvironmentError):
        if os.path.exists(socket_address):
            raise
    sock = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_DGRAM)
    sock.bind(socket_address)
    return sock
