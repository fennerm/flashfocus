"""Test suite for the main flashfocus.server module.

Most of the functionality in flashfocus.router is also tested here.
"""
from time import sleep
from typing import List
from unittest.mock import MagicMock, call

import pytest
from pytest_lazyfixture import lazy_fixture

from flashfocus.client import client_request_flash
from flashfocus.compat import Window
from flashfocus.display import WMEvent, WMEventType
from flashfocus.server import FlashServer
from tests.compat import change_focus, set_fullscreen, switch_workspace
from tests.helpers import (
    new_watched_window,
    new_window_session,
    server_running,
    watching_windows,
)


@pytest.mark.parametrize(
    "focus_indices,flash_indices",
    [
        # Test normal usage
        ([1, 0, 1], [1, 0, 1])
    ],
)
def test_event_loop(
    flash_server: FlashServer,
    windows: List[Window],
    focus_indices: List[int],
    flash_indices: List[int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    focus_shifts = [windows[i] for i in focus_indices]
    windows = sorted(windows, key=lambda window: window.id)
    expected_calls = (
        [call(WMEvent(window=window, event_type=WMEventType.WINDOW_INIT)) for window in windows]
        + [
            call(WMEvent(window=windows[i], event_type=WMEventType.FOCUS_SHIFT))
            for i in flash_indices
        ]
        + [call(WMEvent(window=focus_shifts[-1], event_type=WMEventType.CLIENT_REQUEST))]
    )
    flash_server.router.route_request = MagicMock()  # type: ignore[assignment]
    with server_running(flash_server):
        for window in focus_shifts:
            change_focus(window)
        client_request_flash()
        sleep(0.2)
    actual_calls = flash_server.router.route_request.call_args_list
    assert actual_calls == expected_calls


def test_second_consecutive_focus_requests_ignored(
    flash_server: FlashServer, windows: List[Window]
) -> None:
    expected_calls = [call(WMEvent(window=windows[1], event_type=WMEventType.FOCUS_SHIFT))] * 2
    flash_server.router.route_request = MagicMock()  # type: ignore[assignment]
    with watching_windows(windows) as watchers:
        with server_running(flash_server):
            change_focus(windows[1])
            change_focus(windows[1])

    actual_calls = flash_server.router.route_request.call_args_list
    # The first three route_request calls will be window_inits
    assert actual_calls[3:] == expected_calls

    # Window will only be flashed once though
    watchers[0].count_flashes() == 1


def test_window_opacity_set_to_default_on_startup(
    mult_opacity_server: FlashServer, list_only_test_windows: None, windows: List[Window]
) -> None:
    with server_running(mult_opacity_server):
        assert windows[0].opacity == pytest.approx(0.2)
        assert windows[1].opacity == pytest.approx(0.5)


def test_window_opacity_unset_on_shutdown(
    mult_opacity_server: FlashServer, list_only_test_windows: None, windows: List[Window]
) -> None:
    with server_running(mult_opacity_server):
        pass
    assert windows[0].opacity == pytest.approx(1)
    assert windows[1].opacity == pytest.approx(1)


def test_new_window_opacity_set_to_default(
    transparent_flash_server: FlashServer, list_only_test_windows: None
) -> None:
    with server_running(transparent_flash_server):
        with new_watched_window() as (window, _):
            sleep(0.2)
            assert window.opacity == pytest.approx(0.4)


def test_server_handles_nonexistant_window(flash_server: FlashServer) -> None:
    with server_running(flash_server):
        flash_server.events.put(WMEvent(Window(0), WMEventType.CLIENT_REQUEST))
        sleep(0.01)


def test_per_window_opacity_settings_handled_correctly_by_server(
    mult_flash_opacity_server: FlashServer, windows: List[Window]
) -> None:
    with watching_windows(windows) as watchers:
        with server_running(mult_flash_opacity_server):
            assert windows[0].opacity == pytest.approx(1)
            assert windows[1].opacity == pytest.approx(1)
            change_focus(windows[1])
            change_focus(windows[0])

    # expected: [None, 1.0, 0.2, ...]
    assert watchers[0].opacity_events[2] == pytest.approx(0.2)
    # expected: [None, 1.0, 0.5, ...]
    assert watchers[1].opacity_events[2] == pytest.approx(0.5)


def test_flash_lone_windows_set_to_never_with_existing_window(
    no_lone_server: FlashServer, window: Window
) -> None:
    with watching_windows([window]) as watchers:
        with server_running(no_lone_server):
            assert window.opacity == pytest.approx(0.2)
            change_focus(window)
            assert window.opacity == pytest.approx(0.2)

    # Window has opacity=1 before server starts, then set to 0.2, then set back to 1 when server
    # quits
    assert watchers[0].opacity_events == [1, 0.2, 1]


def test_flash_lone_windows_set_to_never_for_new_window(no_lone_server: FlashServer) -> None:
    with server_running(no_lone_server):
        with new_watched_window() as (window, watcher):
            change_focus(window)

    # The report might contain None or 0.2 depending on whether server or watcher initialized first
    assert watcher.count_flashes() == 0


@pytest.mark.parametrize(
    "server,expected_num_flashes",
    [
        (lazy_fixture("no_lone_server"), 0),
        (lazy_fixture("lone_on_switch_server"), 1),
        (lazy_fixture("lone_on_open_close_server"), 0),
    ],
)
def test_workspace_switching_behavior(server: FlashServer, expected_num_flashes: int) -> None:
    """Test behavior of switching to a workspace with a single mapped window."""
    with new_window_session({0: 1, 1: 1}) as window_session:
        with server_running(server):
            change_focus(window_session.windows[1][0])
            with watching_windows([window_session.get_first_window()]) as watchers:
                change_focus(window_session.get_first_window())
                while not server.events.empty() or server.processing_event:
                    sleep(0.01)

    assert watchers[0].count_flashes() == expected_num_flashes


def test_flash_fullscreen_server_flashes_fullscreen_windows(flash_server: FlashServer) -> None:
    with new_watched_window() as (window, watcher):
        set_fullscreen(window)
        with server_running(flash_server):
            switch_workspace(1)
            change_focus(window)

    assert watcher.count_flashes() == 1


def test_no_flash_fullscreen_false_server_doesnt_flash_fullscreen_windows(
    no_flash_fullscreen_server: FlashServer,
) -> None:
    with new_watched_window() as (window, watcher):
        set_fullscreen(window)
        with server_running(no_flash_fullscreen_server):
            switch_workspace(1)
            change_focus(window)

    assert watcher.count_flashes() == 0
