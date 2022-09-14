"""Testing X11-specific details which don't apply to the sway implementation."""
from collections import namedtuple
from unittest.mock import MagicMock

import pytest
from xcffib.xproto import CreateNotifyEvent

from flashfocus.compat import (
    DisplayHandler,
    DisplayProtocol,
    Window,
    get_display_protocol,
    list_mapped_windows,
)
from flashfocus.display import WMEvent, WMEventType
from tests.helpers import producer_running, queue_to_list

Event = namedtuple("Event", "window,atom")

if get_display_protocol() == DisplayProtocol.WAYLAND:
    pytest.skip("Skipping X11 tests", allow_module_level=True)


def test_that_nonvisible_windows_are_not_queued_by_display_handler(
    display_handler: DisplayHandler, monkeypatch: pytest.MonkeyPatch, windows: list[Window]
) -> None:
    null_fake_event = MagicMock(spec=CreateNotifyEvent)
    null_fake_event.window = 0
    visible_fake_event = MagicMock(spec=CreateNotifyEvent)
    visible_fake_event.window = windows[0].id

    # Initialize a fake xpybutil connection which spits out a mapped window and a non-existant
    # window

    class Counter:
        def __init__(self) -> None:
            self.i = 0

    def wait_for_event(counter: dict = {"i": 0}) -> MagicMock:  # noqa: B006
        counter["i"] += 1
        if counter["i"] == 1:
            return visible_fake_event
        else:
            return null_fake_event

    monkeypatch.setattr("flashfocus.display_protocols.x11.conn.wait_for_event", wait_for_event)
    with producer_running(display_handler):
        pass
    queued = queue_to_list(display_handler.queue)
    # Check that only the mapped window caused the display_handler to queue an event
    assert queued == [WMEvent(window=windows[0], event_type=WMEventType.NEW_WINDOW)]


@pytest.mark.parametrize(
    "rule,should_match",
    [
        # Id matches exactly, no class
        ({"window_id": r"window_0_1"}, True),
        # Id regex matches, no class
        ({"window_id": r"^win.*$"}, True),
        # Class matches exactly, no id
        ({"window_class": r"Window_0_1"}, True),
        # Class regex matches, no id
        ({"window_class": r"^Win.*$"}, True),
        # Both id and class exactly match
        ({"window_id": r"window_0_1", "window_class": r"Window_0_1"}, True),
        # Class matches but id doesn't
        ({"window_id": r"window_0_2", "window_class": r"Window_0_1"}, False),
        # Id matches but class doesn't
        ({"window_id": r"window_0_1", "window_class": r"Window_0_2"}, False),
        # Neither match
        ({"window_id": r"window_0_2", "window_class": r"Window_0_2"}, False),
        # Neither defines (always matches)
        (dict(), True),
    ],
)
def test_rule_matching(window: Window, rule: dict[str, str], should_match: bool) -> None:
    assert window.match(rule) == should_match


def test_properties(window: Window) -> None:
    assert window.properties == {"window_id": "window_0_1", "window_class": "Window_0_1"}


def test_list_mapped_windows(windows: list[Window]) -> None:
    assert list_mapped_windows(0) == windows
    assert list_mapped_windows(2) == list()


def test_display_handler_handle_property_change_ignores_null_windows(
    display_handler: DisplayHandler, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("xpybutil.util.get_atom_name", lambda _: "_NET_ACTIVE_WINDOW")
    monkeypatch.setattr("flashfocus.display_protocols.x11.get_focused_window", lambda: None)
    event = Event(window=None, atom=1)
    display_handler._handle_property_change(event)  # type: ignore[attr-defined]
    assert display_handler.queue.empty()


def test_display_handler_handle_new_window_ignores_null_windows(
    display_handler: DisplayHandler,
) -> None:
    event = Event(window=None, atom=1)
    display_handler._handle_new_mapped_window(event)  # type: ignore[call-arg]
    assert display_handler.queue.empty()


def test_is_fullscreen_handles_none_wm_states(monkeypatch: pytest.MonkeyPatch) -> None:
    class WMStateResponse:
        def reply(self) -> None:
            return None

    monkeypatch.setattr("xpybutil.ewmh.get_wm_state", lambda _: WMStateResponse())
    win = Window(123)
    win.is_fullscreen()
