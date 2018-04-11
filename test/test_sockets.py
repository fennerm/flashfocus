"""Test suite for the flashfocus.sockets module."""
import os

from pytest import raises

from flashfocus.sockets import *


def test_init_client_socket(client_socket):
    client_socket.sendall('test'.encode('UTF-8'))


def test_init_server_socket(server_socket):
    assert server_socket.getsockname()


def test_init_client_socket_without_server():
    with raises(SystemExit) as error:
        init_client_socket()
    assert 'Error:' in str(error.value)
