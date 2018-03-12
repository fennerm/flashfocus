'''Test suite for the server module'''
from time import sleep
from uuid import uuid4

from plumbum import local
from pytest import (
    fixture,
    mark,
)

from flashfocus.server import *
from flashfocus.Xutil import (
    get_focused_window,
    MAX_OPACITY,
    set_opacity,
)
from test.helpers import watch_window


def test_init(server):
    assert server.flash_opacity == 0.8
    assert server.time == 0.05
    assert server.focused_window == get_focused_window()


@mark.parametrize('pre_opacity,expected_opacity_over_time', [
    (0.8, [0.8]),
    (1, [1, 0.8, 1]),
    (None, [0.8, 1]),
    (0.5, [0.5, 0.8, 0.5])
])
def test_flash_window(server, window, tmpdir, pre_opacity,
                      expected_opacity_over_time):
    tmp_logfile = local.path(tmpdir) / (uuid4().hex + '.log')
    if pre_opacity:
        set_opacity(window, pre_opacity)
    watch_window(window, tmp_logfile)
    # Give xorg time to actually update the property
    sleep(0.05)
    server.flash_window(window)
    opacity_over_time = []

    with tmp_logfile.open('r') as f:
        for line in f:
            if line.startswith('_NET_WM_WINDOW_OPACITY'):
                opacity = int(line.split(' ')[-1]) / MAX_OPACITY
                opacity_over_time.append(opacity)

    opacity_over_time = [round(value, 1) for value in opacity_over_time]
    assert opacity_over_time == expected_opacity_over_time
