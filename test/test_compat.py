"""Testsuite for flashfocus.xutil."""
from pytest import approx, raises

from flashfocus.compat import Window
from flashfocus.display import WMError, WMMessage, WMMessageType
from test.helpers import change_focus, producer_running, queue_to_list


def test_get_wm_class(window):
    assert window.wm_class == ("window1", "Window1")


def test_window_raises_wm_error_if_window_is_none():
    with raises(WMError):
        Window(None)


def test_window_set_opacity(window):
    window.set_opacity(0.5)
    assert window.opacity == approx(0.5)


def test_display_handler_handles_focus_shifts(display_handler, windows):
    with producer_running(display_handler):
        change_focus(windows[1])
        change_focus(windows[0])
    queued = queue_to_list(display_handler.queue)
    assert queued == [
        WMMessage(window=windows[1], type=WMMessageType.FOCUS_SHIFT),
        WMMessage(window=windows[0], type=WMMessageType.FOCUS_SHIFT),
    ]
