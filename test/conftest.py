'''Unit test fixtures'''
from pytest import fixture

from flashfocus.monitor import FocusMonitor
from flashfocus.xutil import request_focus

from test.helpers import (
    change_focus,
    WindowSession,
)


@fixture
def windows():
    '''A display session with multiple open windows'''
    windows = WindowSession()
    change_focus(windows.ids[0])
    yield windows.ids
    windows.destroy()


@fixture
def window(windows):
    '''A single blank window'''
    return windows[0]


@fixture
def monitor():
    return FocusMonitor(flash_opacity=0.8, time=200)
