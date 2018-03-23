'''Testsuite for flashfocus.Xutil'''
from pytest import approx

import flashfocus.xutil as xutil
from test.helpers import change_focus


def test_get_set_opacity(window):
    assert not xutil.request_opacity(window).unpack()
    xutil.set_opacity(window, 0.5)
    assert xutil.request_opacity(window).unpack() == approx(0.5, 0.00001)


def test_focus_request(window):
    change_focus(window)
    assert xutil.request_focus().unpack() == window


def test_delete_opacity(window):
    xutil.set_opacity(window, 0.5)
    assert xutil.request_opacity(window).unpack()
    xutil.delete_opacity(window)
    assert not xutil.request_opacity(window).unpack()
