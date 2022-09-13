"""Test suite for the flashfocus.sockets module."""
import os
import socket

import pytest

from flashfocus.sockets import (
    get_socket_address,
    init_client_socket,
    init_server_socket,
)


def test_init_client_socket(client_socket) -> None:
    client_socket.sendall("test".encode("UTF-8"))


def test_first_init_server_socket() -> None:
    os.unlink(get_socket_address())
    init_server_socket()


def test_init_server_socket(server_socket: socket.socket) -> None:
    assert server_socket.getsockname()


def test_init_client_socket_without_server() -> None:
    with pytest.raises(SystemExit) as error:
        init_client_socket()
    assert "Error:" in str(error.value)
