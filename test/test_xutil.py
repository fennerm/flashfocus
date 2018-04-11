"""Testsuite for flashfocus.xutil."""
from threading import Thread

from pytest import approx

from test.helpers import change_focus


def test_get_set_opacity(xconnection, window):
    assert not xconnection.request_opacity(window).unpack()
    xconnection.set_opacity(window, 0.5)
    assert xconnection.request_opacity(window).unpack() == approx(0.5, 0.00001)


def test_focus_request(xconnection, window):
    change_focus(window)
    assert xconnection.request_focus().unpack() == window


def test_delete_opacity(xconnection, window):
    xconnection.set_opacity(window, 0.5)
    assert xconnection.request_opacity(window).unpack()
    xconnection.delete_opacity(window)
    assert not xconnection.request_opacity(window).unpack()


def test_start_watching_properties(xconnection):
    xconnection.start_watching_properties(xconnection.root_window)
    xconnection.conn.flush()
    xconnection.conn.poll_for_event()
