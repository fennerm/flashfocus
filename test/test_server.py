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

from pytest import (
    approx,
    mark,
)

from flashfocus.client import client_request_flash
from flashfocus.server import Flasher
from test.helpers import (
    change_focus,
    queue_to_list,
    WindowWatcher,
)


def test_flash_window(flasher, window):
    change_focus(window)
    expected_opacity = [None] + flasher.flash_series + [None]
    watcher = WindowWatcher(window)
    watcher.start()
    flasher.flash_window(window)
    sleep(0.3)
    assert watcher.report() == approx(expected_opacity, 0.01)


def test_flash_window_stress_test(flasher, window):
    for _ in range(10):
        flasher.flash_window(window)


def test_flash_nonexistant_window_ignored(flasher):
    flasher.flash_window(0)


def test_flash_window_conflicts_are_restarted(flasher, window):
    watcher = WindowWatcher(window)
    watcher.start()
    flasher.flash_window(window)
    sleep(0.05)
    flasher.flash_window(window)
    sleep(0.2)
    num_none = sum([x is None for x in watcher.report()])
    # If the flasher restarts a flash, we should expect the default opacity to
    # only be present at the start and the end of the watcher report.
    assert num_none == 2


@mark.parametrize(
    'flash_opacity,default_opacity,ntimepoints,expected_result', [
        # test typical usecase
        (0.8, 1, 4, [0.8, 0.85, 0.9, 0.95, None]),
        # test that it still works when flash opacity > preflash opacity
        (1, 0.8, 4, [1, 0.95, 0.9, 0.85, 0.8]),
        # test that opacity=1 gives same result as opacity=none
        (0.8, 1, 4, [0.8, 0.85, 0.9, 0.95, None]),
        # test for single chunk
        (0.8, 1, 1, [0.8, None])
    ]
)
def test_compute_flash_series(flash_opacity, default_opacity, ntimepoints,
                              expected_result, flash_server):
    flasher = Flasher(
        flash_opacity=flash_opacity,
        default_opacity=default_opacity,
        ntimepoints=ntimepoints,
        simple=False,
        time=0.2
    )
    for actual, expected in zip(flasher.flash_series, expected_result):
        if actual:
            assert actual == approx(expected)
        else:
            assert not expected


def test_queue_focus_shift_tasks(flash_server, windows):
    p = Thread(target=flash_server._queue_focus_shift_tasks)
    p.start()
    sleep(0.1)
    # When queue_focus_shift_tasks starts up it already has some focus shift
    # tasks to get through. We have to clear these out first
    while flash_server.target_windows.qsize() != 0:
        flash_server.target_windows.get()
    change_focus(windows[1])
    sleep(0.1)
    flash_server.keep_going = False
    change_focus(windows[0])
    sleep(0.1)
    assert (queue_to_list(flash_server.target_windows) ==
            [(windows[1], 'focus_shift'), (windows[0], 'focus_shift')])


def test_queue_client_tasks(flash_server, windows):
    p = Thread(target=flash_server._queue_client_tasks)
    p.start()
    sleep(0.2)
    client_request_flash()
    sleep(0.2)
    client_request_flash()
    sleep(0.2)
    flash_server.keep_going = False
    expected_queue = [(windows[0], 'client_request'),
                      (windows[0], 'client_request')]
    assert queue_to_list(flash_server.target_windows) == expected_queue


@mark.parametrize('focus_indices,flash_indices', [
    # Test normal usage
    ([1, 0, 1], [1, 0, 1]),
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
    sleep(0.1)

    for window in focus_shifts:
        change_focus(window)
    client_request_flash()
    sleep(0.1)
    flash_server.keep_going = False
    p.join()
    assert flash_server.flasher.flash_window.call_args_list == expected_calls
