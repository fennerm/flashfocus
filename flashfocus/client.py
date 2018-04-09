"""Communicating with the flashfocus server via unix socket."""
from flashfocus.sockets import init_client_socket


def client_request_flash():
    """Request that the server flashes the current window."""
    sock = init_client_socket()
    sock.sendall(bytearray('1', encoding='UTF-8'))
