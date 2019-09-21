"""Testing X11-specific details which don't apply to the sway implementation."""
from collections import namedtuple
from unittest.mock import MagicMock

import pytest
from pytest import mark
from xcffib.xproto import CreateNotifyEvent

from flashfocus.compat import DisplayProtocol, get_display_protocol, list_mapped_windows, Window
from flashfocus.display import WMEvent, WMEventType
from test.helpers import producer_running, queue_to_list

Event = namedtuple("Event", "window,atom")

if get_display_protocol() == DisplayProtocol.WAYLAND:
    pytest.skip("Skipping X11 tests", allow_module_level=True)


def test_that_nonvisible_windows_are_not_queued_by_display_handler(
    display_handler, monkeypatch, windows
):
    null_fake_event = MagicMock(spec=CreateNotifyEvent)
    null_fake_event.window = 0
    visible_fake_event = MagicMock(spec=CreateNotifyEvent)
    visible_fake_event.window = windows[0].id

    # Initialize a fake xpybutil connection which spits out a mapped window and a non-existant
    # window

    class Counter:
        def __init__(self):
            self.i = 0

    def wait_for_event(counter={"i": 0}):  # noqa: B006
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


@mark.parametrize(
    "rule,should_match",
    [
        # Id matches exactly, no class
        ({"window_id": r"window1"}, True),
        # Id regex matches, no class
        ({"window_id": r"^win.*$"}, True),
        # Class matches exactly, no id
        ({"window_class": r"Window1"}, True),
        # Class regex matches, no id
        ({"window_class": r"^Win.*$"}, True),
        # Both id and class exactly match
        ({"window_id": r"window1", "window_class": r"Window1"}, True),
        # Class matches but id doesn't
        ({"window_id": r"window2", "window_class": r"Window1"}, False),
        # Id matches but class doesn't
        ({"window_id": r"window1", "window_class": r"Window2"}, False),
        # Neither match
        ({"window_id": r"window2", "window_class": r"Window2"}, False),
        # Neither defines (always matches)
        (dict(), True),
    ],
)
def test_rule_matching(window, rule, should_match):
    assert window.match(rule) == should_match


def test_properties(window):
    assert window.properties == {"window_id": "window1", "window_class": "Window1"}


def test_list_mapped_windows(windows):
    assert list_mapped_windows(0) == windows
    assert list_mapped_windows(2) == list()


def test_display_handler_handle_property_change_ignores_null_windows(display_handler, monkeypatch):
    monkeypatch.setattr("xpybutil.util.get_atom_name", lambda _: "_NET_ACTIVE_WINDOW")
    monkeypatch.setattr("flashfocus.display_protocols.x11.get_focused_window", lambda: None)
    event = Event(window=None, atom=1)
    display_handler._handle_property_change(event)
    assert display_handler.queue.empty()


def test_display_handler_handle_new_window_ignores_null_windows(display_handler):
    event = Event(window=None, atom=1)
    display_handler._handle_new_mapped_window(event)
    assert display_handler.queue.empty()


def test_is_fullscreen_handles_none_wm_states(monkeypatch):
    class WMStateResponse:
        def reply(self):
            return None

    monkeypatch.setattr("xpybutil.ewmh.get_wm_state", lambda _: WMStateResponse())
    win = Window(123)
    win.is_fullscreen()
