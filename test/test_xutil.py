"""Testsuite for flashfocus.xutil."""
from pytest import approx
import xpybutil.icccm

from flashfocus.xutil import *


def test_get_wm_class(window):
    assert get_wm_class(window) == ('window1', 'Window1')


def test_create_message_window():
    window = create_message_window()
    xpybutil.icccm.set_wm_name_checked(window, 'foo').check()


def test_set_all_window_opacity(windows, list_only_test_windows):
    set_all_window_opacity(0.5)
    for window in windows:
        assert (xpybutil.ewmh.get_wm_window_opacity(window).reply() ==
                approx(0.5))
