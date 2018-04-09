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

from flashfocus.flashfocus import Flasher
import flashfocus.xutil as xutil
from test.helpers import (
    change_focus,
    SelfDestructingFocusWait,
    WindowWatcher,
)


def test_flash_window(flasher, window):
    expected_opacity = [None] + flasher.flash_series
    watcher = WindowWatcher(window)
    watcher.start()
    flasher.flash_window(window)
    assert watcher.report() == approx(expected_opacity, 0.01)


def test_flash_window_stress_test(flasher, window):
    for _ in range(10):
        flasher.flash_window(window)


def test_flash_nonexistant_window_ignored(flash_server):
    flash_server.flash_window(0)


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


def test_event_loop(flash_server):


@mark.parametrize('focus_indices,flash_indices', [
    # Test normal usage
    ([1, 0, 1], [1, 0, 1]),
    # Test that focusing on same window twice only flashes once
    ([0, 0], [0])
])
def test_monitor_focus(flash_server, windows, focus_indices, flash_indices,
                       monkeypatch):
    focus_shifts = [windows[i] for i in focus_indices]
    expected_calls = [call(windows[i]) for i in flash_indices]
    flash_server.flash_window = MagicMock()
    monkeypatch.setattr(
        xutil, 'wait_for_focus_shift',
        SelfDestructingFocusWait(len(focus_indices) + 2))
    p = Thread(target=flash_server.monitor_focus)
    p.start()

    for window in focus_shifts:
        change_focus(window)
        sleep(0.2)
        # This would normally be done by the flash_window method
        flash_server.locked_windows.discard(window)

    p.join()
    assert flash_server.flash_window.call_args_list == expected_calls
