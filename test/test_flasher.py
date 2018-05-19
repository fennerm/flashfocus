"""Test suite for flashfocus.flasher."""
from time import sleep

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from pytest import approx, mark

from test.helpers import change_focus, WindowWatcher

from flashfocus.flasher import Flasher


def test_flash(flasher, window):
    change_focus(window)
    expected_opacity = [None] + flasher.flash_series + [1.0]
    watcher = WindowWatcher(window)
    watcher.start()
    flasher.flash(window)
    report = watcher.report()
    assert not report[0]
    assert report[1:] == approx(expected_opacity[1:], 0.01)


def test_flash_stress_test(flasher, window):
    for _ in range(10):
        flasher.flash(window)


def test_flash_nonexistant_window_ignored(flasher):
    flasher.flash(0)


def test_flash_conflicts_are_restarted(flasher, window):
    watcher = WindowWatcher(window)
    watcher.start()
    flasher.flash(window)
    sleep(0.05)
    flasher.flash(window)
    sleep(0.2)
    num_completions = sum([x == 1 for x in watcher.report()])
    # If the flasher restarts a flash, we should expect the default opacity to
    # only be present at the end of the watcher report.
    assert num_completions == 1


@mark.parametrize(
    "flash_opacity,default_opacity,ntimepoints,expected_result",
    [
        # test typical usecase
        (0.8, 1, 4, [0.8, 0.85, 0.9, 0.95, None]),
        # test that it still works when flash opacity > preflash opacity
        (1, 0.8, 4, [1, 0.95, 0.9, 0.85, 0.8]),
        # test that opacity=1 gives same result as opacity=none
        (0.8, 1, 4, [0.8, 0.85, 0.9, 0.95, None]),
        # test for single chunk
        (0.8, 1, 1, [0.8, None]),
    ],
)
def test_compute_flash_series(
    flash_opacity, default_opacity, ntimepoints, expected_result, flash_server
):
    flasher = Flasher(
        flash_opacity=flash_opacity,
        default_opacity=default_opacity,
        ntimepoints=ntimepoints,
        simple=False,
        time=0.2,
    )
    for actual, expected in zip(flasher.flash_series, expected_result):
        assert actual == approx(expected)


def test_flash_requests_ignored_if_no_opacity_change(pointless_flasher, window):
    pointless_flasher._flash = MagicMock()
    pointless_flasher.flash(window)
    pointless_flasher._flash.assert_not_called()
