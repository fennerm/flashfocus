"""Testsuite for flashfocus.xutil."""
from __future__ import annotations
import pytest

from flashfocus.compat import DisplayHandler, Window, get_workspace
from flashfocus.display import WMEvent, WMEventType
from flashfocus.errors import WMError
from tests.compat import change_focus, set_fullscreen, unset_fullscreen
from tests.helpers import new_window_session, producer_running, queue_to_list


def test_window_raises_wm_error_if_window_is_none() -> None:
    with pytest.raises(WMError):
        Window(None)  # type: ignore


@pytest.mark.parametrize("opacity", [0.5, 0.0, 1.0])
def test_window_set_opacity(window: Window, opacity: float) -> None:
    window.set_opacity(opacity)
    assert window.opacity == pytest.approx(opacity)


def test_display_handler_handles_focus_shifts(
    display_handler: DisplayHandler, windows: list[Window]
) -> None:
    with producer_running(display_handler):
        change_focus(windows[1])
        change_focus(windows[0])
    queued = queue_to_list(display_handler.queue)
    assert queued == [
        WMEvent(window=windows[1], event_type=WMEventType.FOCUS_SHIFT),
        WMEvent(window=windows[0], event_type=WMEventType.FOCUS_SHIFT),
    ]


@pytest.mark.parametrize(
    "window1,window2,should_be_equal",
    [(Window(123), Window(324), False), (Window(23), Window(23), True)],
)
def test_window_equality(window1: Window, window2: Window, should_be_equal: bool) -> None:
    assert (window1 == window2) == should_be_equal


def test_window_equality_to_none_raises_error() -> None:
    with pytest.raises(TypeError):
        Window(123) == None  # type: ignore


def test_window_nonequality_to_none_raises_error():
    with pytest.raises(TypeError):
        Window(123) != None  # type: ignore


def test_is_fullscreen(window: Window) -> None:
    assert not window.is_fullscreen()
    set_fullscreen(window)
    assert window.is_fullscreen()
    unset_fullscreen(window)


def test_get_workspace() -> None:
    with new_window_session({0: 1, 1: 1}) as window_session:
        assert get_workspace(window_session.windows[1][0]) == 1
