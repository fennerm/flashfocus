'''Testsuite for flashfocus.Xutil'''
from pytest import approx

from flashfocus.Xutil import *
from test.helpers import change_focus


def test_get_set_opacity(window):
    assert not request_opacity(window).unpack()
    set_opacity(window, 0.5)
    assert request_opacity(window).unpack() == approx(0.5, 0.00001)


def test_focus_request(window):
    change_focus(window)
    assert request_focus().unpack() == window
