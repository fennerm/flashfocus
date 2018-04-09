"""Testsuite for flashfocus.sockets."""
import os
from socket import (
    AF_UNIX,
    SOCK_STREAM,
    socket,
)


SOCKET_NAME = '.flashfocus_socket'
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
    sock = socket(family=AF_UNIX, type=SOCK_STREAM)
    sock.connect(socket_address)
    return sock


def init_server_socket():
    """Initialize and bind the server unix socket."""
    socket_address = choose_socket_address()
    try:
        os.unlink(socket_address)
    except (OSError, EnvironmentError):
        if os.path.exists(socket_address):
            raise
    sock = socket(family=AF_UNIX, type=SOCK_STREAM)
    sock.bind(socket_address)
    sock.listen(1)
    return sock
