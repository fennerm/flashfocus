"""Testsuite for flashfocus.xutil."""
from flashfocus.xutil import *


def test_get_wm_class(window):
    assert get_wm_class(window) == ('window1', 'Window1')
