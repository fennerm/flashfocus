"""Testsuite for flashfocus.xutil."""
from pytest import approx, mark, raises

from flashfocus.compat import Window
from flashfocus.display import WMEvent, WMEventType
from flashfocus.errors import WMError
from test.compat import change_focus, set_fullscreen, unset_fullscreen
from test.helpers import producer_running, queue_to_list


def test_window_raises_wm_error_if_window_is_none():
    with raises(WMError):
        Window(None)


@mark.parametrize("opacity", [0.5, 0, 1])
def test_window_set_opacity(window, opacity):
    window.set_opacity(opacity)
    assert window.opacity == approx(opacity)


def test_display_handler_handles_focus_shifts(display_handler, windows):
    with producer_running(display_handler):
        change_focus(windows[1])
        change_focus(windows[0])
    queued = queue_to_list(display_handler.queue)
    assert queued == [
        WMEvent(window=windows[1], event_type=WMEventType.FOCUS_SHIFT),
        WMEvent(window=windows[0], event_type=WMEventType.FOCUS_SHIFT),
    ]


@mark.parametrize(
    "window1,window2,should_be_equal",
    [(Window(123), Window(324), False), (Window(23), Window(23), True)],
)
def test_window_equality(window1, window2, should_be_equal):
    assert (window1 == window2) == should_be_equal


def test_window_equality_to_none_raises_error():
    with raises(TypeError):
        Window(123) == None


def test_window_nonequality_to_none_raises_error():
    with raises(TypeError):
        Window(123) != None


def test_none_windows_raise_error():
    with raises(WMError):
        Window(None)


def test_is_fullscreen(window):
    assert not window.is_fullscreen()
    set_fullscreen(window)
    assert window.is_fullscreen()
    unset_fullscreen(window)
