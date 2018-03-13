'''Test suite for the server module'''
from multiprocessing import Process
from time import sleep

from pytest import mark

from flashfocus.server import *
from flashfocus.Xutil import (
    request_focus,
    request_opacity,
    set_opacity,
)
from test.helpers import (
    change_focus,
    WindowWatcher,
)


def test_init(server):
    assert server.flash_opacity == 0.8
    assert server.time == 0.05


@mark.parametrize('pre_opacity,expected_opacity_over_time', [
    (0.8, [0.8]),
    (1, [1, 0.8, 1]),
    (None, [0.8, None]),
    (0.5, [0.5, 0.8, 0.5])
])
def test_flash_window(server, window, pre_opacity,
                      expected_opacity_over_time):
    if pre_opacity:
        set_opacity(window, pre_opacity)
    watcher = WindowWatcher(window)
    server.flash_window(window)
    assert watcher.report() == expected_opacity_over_time


def test_unset_window_opacity_is_deleted_after_flash(server, window):
    server.flash_window(window)
    assert not request_opacity(window).unpack()

def test_monitor_focus(server, windows, tmpdir):
    p = Process(target=server.monitor_focus)
    p.start()
    watchers = [WindowWatcher(window) for window in windows]

    change_focus(windows[0])
    sleep(0.2)
    change_focus(windows[1])
    sleep(0.2)
    change_focus(windows[0])
    sleep(0.2)

    opacity_over_time = [watcher.report() for watcher in watchers]
    assert opacity_over_time[0] == [0.8, 1, 0.8]
    assert opacity_over_time[1] == [0.8]
    assert opacity_over_time[2] == []
    p.join()
