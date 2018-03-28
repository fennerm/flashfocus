"""Test suite for the server module."""
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

import flashfocus.xutil as xutil
from test.helpers import (
    change_focus,
    SelfDestructingFocusWait,
    WindowWatcher,
)


@mark.parametrize('pre_opacity', [
    (0.8), (1), (None), (0.5)
])
def test_flash_window(flasher, window, pre_opacity):
    if pre_opacity:
        xutil.set_opacity(window, pre_opacity)
    expected_opacity = (
        [pre_opacity] +
        flasher.compute_flash_series(pre_opacity) +
        [pre_opacity])
    # WindowWatcher collapses runs of the same value
    if all(x == expected_opacity[0] for x in expected_opacity):
        expected_opacity = [expected_opacity[0]]
    watcher = WindowWatcher(window)
    watcher.start()
    flasher.flash_window(window)
    assert watcher.report() == approx(expected_opacity, 0.01)


def test_flash_nonexistant_window_ignored(flasher):
    flasher.flash_window(0)


@mark.parametrize('focus_indices,flash_indices', [
    # Test normal usage
    ([1, 0, 1], [1, 0, 1]),
    # Test that focusing on same window twice only flashes once
    ([0, 0], [0])
])
def test_monitor_focus(flasher, windows, focus_indices, flash_indices,
                       monkeypatch):
    focus_shifts = [windows[i] for i in focus_indices]
    expected_calls = [call(windows[i]) for i in flash_indices]
    flasher.flash_window = MagicMock()
    monkeypatch.setattr(
        xutil, 'wait_for_focus_shift',
        SelfDestructingFocusWait(len(focus_indices) + 2))
    p = Thread(target=flasher.monitor_focus)
    p.start()

    for window in focus_shifts:
        change_focus(window)
        sleep(0.2)
        # This would normally be done by the flash_window method
        flasher.locked_windows.discard(window)

    p.join()
    assert flasher.flash_window.call_args_list == expected_calls


@mark.parametrize(
    'flash_opacity,preflash_opacity,ntimepoints,expected_result', [
        # test typical usecase
        (0.8, None, 4, [0.8, 0.85, 0.9, 0.95]),
        # test that it still works when flash opacity > preflash opacity
        (1, 0.8, 4, [1, 0.95, 0.9, 0.85]),
        # test that opacity=1 gives same result as opacity=none
        (0.8, 1, 4, [0.8, 0.85, 0.9, 0.95]),
        # test for single chunk
        (0.8, 1, 1, [0.8])
    ]
)
def test_compute_flash_series(flash_opacity, preflash_opacity, ntimepoints,
                              expected_result, flasher):
    flasher.flash_opacity = flash_opacity
    flasher.ntimepoints = ntimepoints
    assert (flasher.compute_flash_series(preflash_opacity) ==
            approx(expected_result, 0.0001))
    if preflash_opacity:
        assert (flasher.flash_series_hash[preflash_opacity] ==
                approx(expected_result, 0.0001))
