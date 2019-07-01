"""Testing X11-specific details which don't apply to the sway implementation."""
from unittest.mock import MagicMock

import pytest
from xcffib.xproto import CreateNotifyEvent

from flashfocus.compat import DisplayProtocol, get_display_protocol
from flashfocus.display import WMMessage, WMMessageType
from test.helpers import producer_running, queue_to_list


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

    def wait_for_event(counter={"i": 0}):
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
    assert queued == [WMMessage(window=windows[0], type=WMMessageType.NEW_WINDOW)]
