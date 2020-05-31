"""Unit test fixtures."""
from queue import Queue

from factory import Factory
from pytest import fixture
from pytest_factoryboy import register

from flashfocus.flasher import Flasher
from flashfocus.client import ClientMonitor
from flashfocus.compat import DisplayHandler
from flashfocus.server import FlashServer
from flashfocus.sockets import init_client_socket, init_server_socket

from test.helpers import (
    default_flash_param,
    fill_in_rule,
    quick_conf,
    rekey,
    StubServer,
    WindowSession,
)


@fixture
def windows():
    """Display session with multiple open windows."""
    window_session = WindowSession(3)
    yield window_session.windows
    window_session.destroy()


@fixture
def window():
    """Single blank window."""
    window_session = WindowSession(1)
    yield window_session.windows[0]
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
                        "window_class": "Window1",
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
                    {"window_class": "Window1", "default_opacity": 0.2},
                    {"window_id": "window2", "default_opacity": 0.5},
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
                    {"window_class": "Window1", "flash_opacity": 0.2},
                    {"window_id": "window2", "flash_opacity": 0.5},
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


@fixture
def server_socket():
    """Server socket instance."""
    socket = init_server_socket()
    yield socket
    socket.close()


@fixture
def client_socket(server_socket):
    """Client socket instance."""
    return init_client_socket()


@fixture
def stub_server(server_socket):
    """StubServer instance."""
    return StubServer(server_socket)


@fixture
def list_only_test_windows(monkeypatch, windows):
    """Only list test window ids."""
    monkeypatch.setattr("flashfocus.compat.list_mapped_windows", lambda: windows)


@fixture
def valid_config_types():
    return {key: val["type"] for key, val in default_flash_param().items()}


@fixture
def blank_cli_options():
    cli_options = dict()
    for key, val in default_flash_param().items():
        if val["location"] == "any":
            cli_options[key] = None
        elif val["location"] == "cli":
            cli_options[key] = val["default"]
    return cli_options


@fixture
def valid_bool():
    return ["false", "False", "FALSE", "True", "true", "TRUE", True, False]


@fixture
def client_monitor():
    return ClientMonitor(Queue())


@fixture
def display_handler():
    return DisplayHandler(Queue())


@fixture
def configfile(tmpdir):
    tmp = tmpdir.join("conf.yml")
    tmp.write("default-opacity: 1\nflash-opacity: 0.5")
    return tmp


@fixture
def configfile_with_02_flash_opacity(tmpdir):
    tmp = tmpdir.join("conf.yml")
    tmp.write("default-opacity: 1\nflash-opacity: 0.2")
    return tmp
