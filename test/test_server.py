"""Test suite for the main flashfocus module."""
from threading import Thread
from time import sleep

try:
    from unittest.mock import (
        call,
        MagicMock,
    )
except ImportError:
    from mock import (
        call,
        MagicMock,
    )

from pytest import mark

from flashfocus.client import client_request_flash
from test.helpers import (
    change_focus,
    queue_to_list,
)


def test_queue_focus_shift_tasks(flash_server, windows):
    flash_server._flash_queued_window = MagicMock()
    p = Thread(target=flash_server._queue_focus_shift_tasks)
    p.start()
    sleep(0.1)
    # When queue_focus_shift_tasks starts up it already has some focus shift
    # tasks to get through. We have to clear these out first
    while flash_server.target_windows.qsize() != 0:
        flash_server.target_windows.get()
    change_focus(windows[1])
    change_focus(windows[0])
    flash_server.keep_going = False
    assert (queue_to_list(flash_server.target_windows) ==
            [(windows[1], 'focus_shift'), (windows[0], 'focus_shift')])


def test_queue_client_tasks(flash_server, windows):
    p = Thread(target=flash_server._queue_client_tasks)
    p.start()
    sleep(0.05)
    client_request_flash()
    client_request_flash()
    sleep(0.1)
    flash_server.keep_going = False
    expected_queue = [(windows[0], 'client_request'),
                      (windows[0], 'client_request')]
    assert queue_to_list(flash_server.target_windows) == expected_queue


@mark.parametrize('focus_indices,flash_indices', [
    # Test normal usage
    ([0, 1, 0], [0, 1, 0]),
])
def test_event_loop(flash_server, windows, focus_indices, flash_indices,
                    monkeypatch):
    # Shift focus as specified by parameters then throw in a client request for
    # good measure
    focus_shifts = [windows[i] for i in focus_indices]
    expected_calls = ([call(windows[i]) for i in flash_indices] +
                      [call(focus_shifts[-1])])
    flash_server.flasher.flash_window = MagicMock()
    p = Thread(target=flash_server.event_loop)
    p.start()

    for window in focus_shifts:
        change_focus(window)
    client_request_flash()
    sleep(0.5)
    flash_server.keep_going = False
    p.join()
    assert flash_server.flasher.flash_window.call_args_list == expected_calls
