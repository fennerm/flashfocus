"""Unix socket initialization.

The flashfocus client and server communicate using a simple datagram unix
socket.
"""
import os
import socket
import sys


def determine_runtime_dir() -> str:
    """Determine the runtime dir.

    Uses XDG_RUNTIME_DIR if defined, otherwise falls back to /tmp

    """
    xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime_dir is not None:
        runtime_dir = xdg_runtime_dir
    else:
        runtime_dir = "/tmp"

    return runtime_dir


def get_socket_address() -> str:
    runtime_dir = determine_runtime_dir()
    return os.path.join(runtime_dir, "flashfocus_socket")


def init_client_socket() -> socket.socket:
    """Initialize and connect the client unix socket."""
    sock = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_DGRAM)
    socket_address = get_socket_address()
    try:
        sock.connect(socket_address)
    except socket.error:
        sys.exit(
            "Error: Couldn't connect to the flashfocus daemon!\n"
            "=> Please check that the flashfocus daemon is running."
        )
    return sock


def init_server_socket() -> socket.socket:
    """Initialize and bind the server unix socket."""
    socket_address = get_socket_address()
    try:
        os.unlink(socket_address)
    except (OSError, EnvironmentError):
        pass
    sock = socket.socket(family=socket.AF_UNIX, type=socket.SOCK_DGRAM)
    sock.bind(socket_address)
    sock.settimeout(1)
    return sock
