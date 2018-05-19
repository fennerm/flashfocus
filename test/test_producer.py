"""Testsuite for flashfocus.producer."""
import socket

from pytest import raises

from flashfocus.client import client_request_flash
from test.helpers import change_focus, producer_running, queue_to_list


def test_client_monitor_handles_client_requests(client_monitor, windows):
    with producer_running(client_monitor):
        client_request_flash()
        client_request_flash()
    queued = queue_to_list(client_monitor.queue)
    assert queued == [
        (windows[0], "client_request"),
        (windows[0], "client_request"),
    ]


def test_client_monitor_stop_disconnects_socket(client_monitor):
    client_monitor.start()
    client_monitor.stop()
    with raises(socket.error):
        client_monitor.sock.getsockname()


def test_xhandler_handles_focus_shifts(xhandler, windows):
    with producer_running(xhandler):
        change_focus(windows[1])
        change_focus(windows[0])
    change_focus(windows[1])
    queued = queue_to_list(xhandler.queue)
    assert queued == [(windows[1], "focus_shift"), (windows[0], "focus_shift")]
