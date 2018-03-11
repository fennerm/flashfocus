from pytest import approx

from flashfocus.Xutil import *

def get_opacity(x_window_id):
    cookie = request_opacity(x_window_id)
    opacity = unpack_cookie(cookie)
    return opacity


def test_get_set_opacity(window):
    assert get_opacity(window) == 1
    set_opacity(window, 0.5)
    assert get_opacity(window) == approx(0.5, 0.00001)
