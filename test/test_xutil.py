"""Testsuite for flashfocus.xutil."""
from pytest import approx

from flashfocus.xutil import *
from test.helpers import get_opacity


def test_get_wm_class(window):
    assert get_wm_class(window) == ('window1', 'Window1')


def test_create_message_window():
    window = create_message_window()
    set_opacity(window, 0.8)


def test_set_all_window_opacity(windows, list_only_test_windows):
    set_all_window_opacity(0.5)
    for window in windows:
        assert get_opacity(window) == approx(0.5)


def test_set_opacity(window):
    set_opacity(window, 0.5)
    assert get_opacity(window) == approx(0.5)
