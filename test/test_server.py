"""Test suite for the main flashfocus.server module.

Most of the functionality in flashfocus.router is also tested here.
"""
try:
    from unittest.mock import call, MagicMock
except ImportError:
    from mock import call, MagicMock
from time import sleep

from pytest import approx, mark
from xpybutil.ewmh import get_wm_window_opacity

from flashfocus.client import client_request_flash
from flashfocus.xutil import destroy_window

from test.helpers import (
    change_focus,
    new_watched_window,
    server_running,
    switch_desktop,
    watching_windows,
    WindowSession,
)


@mark.parametrize(
    "focus_indices,flash_indices",
    [
        # Test normal usage
        ([1, 0, 1], [1, 0, 1])
    ],
)
def test_event_loop(flash_server, windows, focus_indices, flash_indices, monkeypatch):
    focus_shifts = [windows[i] for i in focus_indices]
    expected_calls = (
        [call(window, "window_init") for window in windows]
        + [call(windows[i], "focus_shift") for i in flash_indices]
        + [call(focus_shifts[-1], "client_request")]
    )
    flash_server.router.route_request = MagicMock()
    with server_running(flash_server):
        for window in focus_shifts:
            change_focus(window)
        client_request_flash()
    assert flash_server.router.route_request.call_args_list == expected_calls


def test_second_consecutive_focus_requests_ignored(flash_server, windows):
    expected_calls = [call(windows[1], "focus_shift")] * 2
    flash_server.router.route_request = MagicMock()
    with watching_windows(windows) as watchers:
        with server_running(flash_server):
            change_focus(windows[1])
            change_focus(windows[1])
    # The first three route_request calls will be window_inits
    assert flash_server.router.route_request.call_args_list[3:] == expected_calls

    # Window will only be flashed once though
    num_completions = sum([x == 1 for x in watchers[1].opacity_events])
    assert num_completions == 1


def test_window_opacity_set_to_default_on_startup(
    mult_opacity_server, list_only_test_windows, windows
):
    with server_running(mult_opacity_server):
        assert get_wm_window_opacity(windows[0]).reply() == approx(0.2)
        assert get_wm_window_opacity(windows[1]).reply() == approx(0.5)


def test_window_opacity_unset_on_shutdown(mult_opacity_server, list_only_test_windows, windows):
    with server_running(mult_opacity_server):
        pass
    assert get_wm_window_opacity(windows[0]).reply() == approx(1)
    assert get_wm_window_opacity(windows[1]).reply() == approx(1)


def test_new_window_opacity_set_to_default(transparent_flash_server, list_only_test_windows):
    with server_running(transparent_flash_server):
        window_session = WindowSession()
        assert get_wm_window_opacity(window_session.windows[0]).reply() == approx(0.4)
    window_session.destroy()


def test_server_handles_nonexistant_window(flash_server):
    with server_running(flash_server):
        flash_server.flash_requests.put((0, "client_request"))
        sleep(0.01)


def test_server_handles_none_window(flash_server):
    with server_running(flash_server):
        flash_server.flash_requests.put((None, "client_request"))
        sleep(0.1)


def test_per_window_opacity_settings_handled_correctly_by_server(
    mult_flash_opacity_server, windows
):
    with watching_windows(windows) as watchers:
        with server_running(mult_flash_opacity_server):
            assert get_wm_window_opacity(windows[0]).reply() == approx(1)
            assert get_wm_window_opacity(windows[1]).reply() == approx(1)
            change_focus(windows[1])
            change_focus(windows[0])
            sleep(0.2)

    # expected: [None, 1.0, 0.2, ...]
    assert watchers[0].opacity_events[2] == approx(0.2)
    # expected: [None, 1.0, 0.5, ...]
    assert watchers[1].opacity_events[2] == approx(0.5)


def test_flash_lone_windows_set_to_never_with_existing_window(no_lone_server, window):
    with watching_windows([window]) as watchers:
        with server_running(no_lone_server):
            assert get_wm_window_opacity(window).reply() == approx(0.2)
            change_focus(window)
            assert get_wm_window_opacity(window).reply() == approx(0.2)

    assert watchers[0].opacity_events == [None, 0.2, 1]


def test_flash_lone_windows_set_to_never_for_new_window(no_lone_server):
    with server_running(no_lone_server):
        with new_watched_window() as (window, watcher):
            change_focus(window)

    # The report might contain None or 0.2 depending on whether server or watcher initialized first
    assert len(watcher.opacity_events) == 1


def test_flash_lone_windows_set_to_never_with_desktop_switching(no_lone_server):
    with server_running(no_lone_server):
        with new_watched_window() as (window, watcher):
            switch_desktop(1)
            switch_desktop(0)

    # The report might contain None or 0.2 depending on whether server or watcher initialized first
    assert len(watcher.opacity_events) == 1


def test_lone_windows_flash_on_switch_if_flash_lone_windows_is_on_switch(
    lone_on_switch_server, window
):
    with watching_windows([window]) as watchers:
        with server_running(lone_on_switch_server):
            switch_desktop(1)
            change_focus(window)

    assert len(watchers[0].opacity_events) > 2


def test_lone_windows_dont_flash_on_switch_if_flash_lone_windows_is_on_open_close(
    lone_on_open_close_server, window
):
    with watching_windows([window]) as watchers:
        with server_running(lone_on_open_close_server):
            switch_desktop(1)
            change_focus(window)

    # The report might contain None or 0.2 depending on whether server or watcher initialized first
    assert len(watchers[0].opacity_events) == 2
