"""Test suite for the server module."""
from threading import Thread
from time import sleep

from mock import (
    call,
    MagicMock,
    Mock,
    patch,
)
from pytest import (
    mark,
    raises,
)

from flashfocus.xutil import CONN, set_opacity
from test.helpers import (
    change_focus,
    ExitAfter,
    WindowWatcher,
)


@mark.parametrize('pre_opacity,expected_opacity_over_time', [
    (0.8, [0.8]),
    (1, [1, 0.8, 1]),
    (None, [None, 0.8, None]),
    (0.5, [0.5, 0.8, 0.5])
])
def test_flash_window(monitor, window, pre_opacity,
                      expected_opacity_over_time):
    if pre_opacity:
        set_opacity(window, pre_opacity)
    watcher = WindowWatcher(window)
    watcher.start()
    monitor.flash_window(window)
    assert watcher.report() == expected_opacity_over_time


def test_two_quick_calls_just_flashes_once(monitor, window):
    watcher = WindowWatcher(window)
    watcher.start()
    p = Thread(target=monitor.flash_window, args=window)
    p.start()
    monitor.flash_window(window)
    p.join()
    assert watcher.report() == [None, 0.8, None]


def test_monitor_focus(monitor, windows):
    focus_shifts = [windows[1], windows[0], windows[1]]
    expected_calls = [call(window) for window in focus_shifts]
    monitor.flash_window = MagicMock()
    # Kill the monitor after it calls flash_window three times
    monitor.flash_window.side_effect = ExitAfter(2)
    p = Thread(target=monitor.monitor_focus)
    p.start()

    for window in focus_shifts:
        change_focus(window)
        sleep(0.2)

    p.join()
    monitor.flash_window.assert_has_calls(expected_calls)
