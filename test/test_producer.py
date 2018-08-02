"""Testsuite for flashfocus.producer."""
import socket

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from pytest import raises
from xcffib.xproto import CreateNotifyEvent

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
    queued = queue_to_list(xhandler.queue)
    assert queued == [(windows[1], "focus_shift"), (windows[0], "focus_shift")]


def test_that_nonvisible_windows_are_not_queued_by_xhandler(
    xhandler, monkeypatch, windows
):
    null_fake_event = MagicMock(spec=CreateNotifyEvent)
    null_fake_event.window = 0
    visible_fake_event = MagicMock(spec=CreateNotifyEvent)
    visible_fake_event.window = windows[0]

    class FakeConnection:
        def __init__(self, windows):
            self.i = 0
            self.windows = windows

        def wait_for_event(self):
            self.i += 1
            if self.i == 2:
                return visible_fake_event
            else:
                return null_fake_event

    monkeypatch.setattr("xpybutil.conn", FakeConnection(windows))
    with producer_running(xhandler):
        pass
    queued = queue_to_list(xhandler.queue)
    assert queued == [(windows[0], "new_window")]
