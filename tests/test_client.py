"""Test suite for flashfocus.client."""
import socket
from threading import Thread
from time import sleep
from typing import List

from pytest import raises

from flashfocus.client import ClientMonitor, client_request_flash
from flashfocus.compat import Window
from flashfocus.display import WMEvent, WMEventType
from tests.helpers import StubServer, producer_running, queue_to_list


def test_client_request_flash(stub_server: StubServer) -> None:
    p = Thread(target=stub_server.await_data)
    p.start()
    client_request_flash()
    sleep(0.05)
    p.join()
    assert stub_server.data == [b"1"]


def test_client_monitor_handles_client_requests(
    client_monitor: ClientMonitor, windows: List[Window]
) -> None:
    with producer_running(client_monitor):
        client_request_flash()
        client_request_flash()
    queued = queue_to_list(client_monitor.queue)
    assert queued == [
        WMEvent(window=windows[0], event_type=WMEventType.CLIENT_REQUEST),
        WMEvent(window=windows[0], event_type=WMEventType.CLIENT_REQUEST),
    ]


def test_client_monitor_stop_disconnects_socket(client_monitor: ClientMonitor) -> None:
    client_monitor.start()
    client_monitor.stop()
    with raises(socket.error):
        client_monitor.sock.getsockname()
