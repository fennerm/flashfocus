"""Unit test fixtures."""
from __future__ import annotations

import socket
from queue import Queue
from collections.abc import Generator

import pytest
from factory import Factory
from pytest_factoryboy import register

from flashfocus.client import ClientMonitor
from flashfocus.compat import DisplayHandler, Window
from flashfocus.flasher import Flasher
from flashfocus.server import FlashServer
from flashfocus.sockets import init_client_socket, init_server_socket
from tests.helpers import (
    StubServer,
    WindowSession,
    default_flash_param,
    fill_in_rule,
    quick_conf,
    rekey,
)


@pytest.fixture
def windows() -> Generator[list[Window], None, None]:
    """Display session with multiple open windows."""
    window_session = WindowSession({0: 3})
    window_session.setup()
    yield window_session.windows[0]
    window_session.destroy()


@pytest.fixture
def window() -> Generator[Window, None, None]:
    """Single blank window."""
    window_session = WindowSession({0: 1})
    window_session.setup()
    yield window_session.windows[0][0]
    window_session.destroy()


class ServerFactory(Factory):
    """Factory for producing FlashServer fixture instances."""

    class Meta:
        model = FlashServer

    config = quick_conf()


register(ServerFactory, "flash_server")

register(
    ServerFactory, "transparent_flash_server", config=rekey(quick_conf(), {"default_opacity": 0.4})
)


# See issue #25
register(
    ServerFactory,
    "no_lone_server",
    config=rekey(
        quick_conf(),
        {
            "default_opacity": 1,
            "flash_opacity": 0.8,
            "flash_lone_windows": "never",
            "rules": [
                fill_in_rule(
                    {
                        "window_class": "Window_0_1",
                        "default_opacity": 0.2,
                        "flash_lone_windows": "never",
                    }
                )
            ],
        },
    ),
)

register(
    ServerFactory,
    "lone_on_switch_server",
    config=rekey(
        quick_conf(),
        {"default_opacity": 1, "flash_opacity": 0.8, "flash_lone_windows": "on_switch"},
    ),
)

register(
    ServerFactory,
    "lone_on_open_close_server",
    config=rekey(
        quick_conf(),
        {"default_opacity": 1, "flash_opacity": 0.8, "flash_lone_windows": "on_open_close"},
    ),
)

register(
    ServerFactory,
    "mult_opacity_server",
    config=rekey(
        quick_conf(),
        {
            "rules": [
                fill_in_rule(rule)
                for rule in [
                    {"window_class": "Window_0_1", "default_opacity": 0.2},
                    {"window_id": "window_0_2", "default_opacity": 0.5},
                ]
            ]
        },
    ),
)

register(
    ServerFactory,
    "mult_flash_opacity_server",
    config=rekey(
        quick_conf(),
        {
            "rules": [
                fill_in_rule(rule)
                for rule in [
                    {"window_class": "Window_0_1", "flash_opacity": 0.2},
                    {"window_id": "window_0_2", "flash_opacity": 0.5},
                ]
            ]
        },
    ),
)

register(
    ServerFactory,
    "no_flash_fullscreen_server",
    config=rekey(
        quick_conf(), {"default_opacity": 1, "flash_opacity": 0.8, "flash_fullscreen": False}
    ),
)


class FlasherFactory(Factory):
    """Factory for producing Flasher fixture instances."""

    class Meta:
        model = Flasher

    default_opacity = 1
    flash_opacity = 0.8
    time = 100
    ntimepoints = 4
    simple = False


register(FlasherFactory, "flasher")

register(FlasherFactory, "pointless_flasher", flash_opacity=1)


@pytest.fixture
def server_socket() -> Generator[socket.socket, None, None]:
    """Server socket instance."""
    socket = init_server_socket()
    yield socket
    socket.close()


@pytest.fixture
def client_socket(server_socket: socket.socket) -> socket.socket:
    """Client socket instance."""
    return init_client_socket()


@pytest.fixture
def stub_server(server_socket: socket.socket) -> StubServer:
    """StubServer instance."""
    return StubServer(server_socket)


@pytest.fixture
def list_only_test_windows(monkeypatch: pytest.MonkeyPatch, windows: list[Window]) -> None:
    """Only list test window ids."""
    monkeypatch.setattr("flashfocus.compat.list_mapped_windows", lambda: windows)


@pytest.fixture
def valid_config_types() -> dict[str, list[type]]:
    return {key: val["type"] for key, val in default_flash_param().items()}


@pytest.fixture
def blank_cli_options() -> dict:
    cli_options: dict = dict()
    for key, val in default_flash_param().items():
        if val["location"] == "any":
            cli_options[key] = None
        elif val["location"] == "cli":
            cli_options[key] = val["default"]
    return cli_options


@pytest.fixture
def valid_bool() -> tuple[str, str, str, str, str, str, bool, bool]:
    return "false", "False", "FALSE", "True", "true", "TRUE", True, False


@pytest.fixture
def client_monitor() -> ClientMonitor:
    return ClientMonitor(Queue())


@pytest.fixture
def display_handler() -> DisplayHandler:
    return DisplayHandler(Queue())


@pytest.fixture
def configfile(tmpdir):  # type: ignore
    # tmpdir is a py._path.local.LocalPath object
    tmp = tmpdir.join("conf.yml")
    tmp.write("default-opacity: 1\nflash-opacity: 0.5")
    return tmp


@pytest.fixture
def configfile_with_02_flash_opacity(tmpdir):  # type: ignore
    tmp = tmpdir.join("conf.yml")
    tmp.write("default-opacity: 1\nflash-opacity: 0.2")
    return tmp
