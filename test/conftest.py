"""Unit test fixtures."""
from pytest import fixture

from flashfocus.flasher import Flasher

from test.helpers import (
    change_focus,
    WindowSession,
)


@fixture
def windows():
    """A display session with multiple open windows"""
    windows = WindowSession()
    change_focus(windows.ids[0])
    yield windows.ids
    windows.destroy()


@fixture
def window(windows):
    """A single blank window"""
    return windows[0]


@fixture
def flasher():
    """Flasher instance."""
    return Flasher(flash_opacity=0.8, time=0.2, ntimepoints=10, simple=False)
