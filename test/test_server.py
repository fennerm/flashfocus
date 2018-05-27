"""Test suite for the main flashfocus module."""
try:
    from unittest.mock import call, MagicMock
except ImportError:
    from mock import call, MagicMock
from time import sleep

from pytest import approx, mark
from xpybutil.ewmh import get_wm_window_opacity

from flashfocus.client import client_request_flash
from test.helpers import change_focus, server_running, WindowSession


@mark.parametrize(
    "focus_indices,flash_indices",
    [
        # Test normal usage
        ([1, 0, 1], [1, 0, 1])
    ],
)
def test_event_loop(
    flash_server, windows, focus_indices, flash_indices, monkeypatch
):
    focus_shifts = [windows[i] for i in focus_indices]
    expected_calls = [
        call(windows[i], "focus_shift") for i in flash_indices
    ] + [call(focus_shifts[-1], "client_request")]
    flash_server.matcher.route_request = MagicMock()
    with server_running(flash_server):
        for window in focus_shifts:
            change_focus(window)
        client_request_flash()
    assert flash_server.matcher.route_request.call_args_list == expected_calls


def test_second_consecutive_focus_requests_ignored(flash_server, windows):
    flash_server.matcher.route_request = MagicMock()
    with server_running(flash_server):
        change_focus(windows[1])
        change_focus(windows[1])
    assert flash_server.matcher.route_request.call_args_list == [
        call(windows[1], "focus_shift")
    ]


def test_window_opacity_set_to_default_on_startup(
    mult_opacity_server, list_only_test_windows, windows
):
    with server_running(mult_opacity_server):
        assert get_wm_window_opacity(windows[0]).reply() == approx(0.2)
        assert get_wm_window_opacity(windows[1]).reply() == approx(0.5)


def test_window_opacity_unset_on_shutdown(
    mult_opacity_server, list_only_test_windows, windows
):
    with server_running(mult_opacity_server):
        pass
    assert get_wm_window_opacity(windows[0]).reply() == approx(1)
    assert get_wm_window_opacity(windows[1]).reply() == approx(1)


def test_new_window_opacity_set_to_default(
    transparent_flash_server, list_only_test_windows
):
    with server_running(transparent_flash_server):
        windows = WindowSession()
        sleep(0.2)
        assert get_wm_window_opacity(windows.ids[0]).reply() == approx(0.4)
    windows.destroy()


def test_server_handles_nonexistant_window(flash_server):
    with server_running(flash_server):
        flash_server.flash_requests.put((0, "client_request"))
        sleep(0.1)


def test_server_handles_none_window(flash_server):
    with server_running(flash_server):
        flash_server.flash_requests.put((None, "client_request"))
        sleep(0.1)
