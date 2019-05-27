"""Unit test fixtures."""
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
import re
import sys

from factory import Factory
from pytest import fixture
from pytest_factoryboy import register

from flashfocus.flasher import Flasher
from flashfocus.producer import ClientMonitor, XHandler
from flashfocus.server import FlashServer
from flashfocus.sockets import init_client_socket, init_server_socket

from test.helpers import (
    clear_desktop,
    default_flash_param,
    fill_in_rule,
    rekey,
    StubServer,
    switch_desktop,
    WindowSession,
)


@fixture
def windows():
    """Display session with multiple open windows."""
    clear_desktop(0)
    switch_desktop(0)
    window_session = WindowSession(3)
    yield window_session.windows
    window_session.destroy()


@fixture
def window(windows):
    """Single blank window."""
    clear_desktop(0)
    switch_desktop(0)
    window_session = WindowSession(1)
    yield window_session.windows[0]
    window_session.destroy()


class ServerFactory(Factory):
    """Factory for producing FlashServer fixture instances."""

    class Meta:
        model = FlashServer

    default_opacity = 1
    flash_opacity = 0.8
    time = 100
    ntimepoints = 4
    simple = False
    rules = None
    flash_on_focus = True
    flash_lone_windows = "always"


register(ServerFactory, "flash_server")

register(ServerFactory, "transparent_flash_server", default_opacity=0.4)


# See issue #25
register(
    ServerFactory,
    "no_lone_server",
    default_opacity=1,
    flash_opacity=0.8,
    flash_lone_windows="never",
    rules=[
        fill_in_rule(
            {"window_class": "Window1", "default_opacity": 0.2, "flash_lone_windows": "never"}
        )
    ],
)

register(
    ServerFactory,
    "lone_on_switch_server",
    default_opacity=1,
    flash_opacity=0.8,
    flash_lone_windows="on_switch",
)

register(
    ServerFactory,
    "lone_on_open_close_server",
    default_opacity=1,
    flash_opacity=0.8,
    flash_lone_windows="on_open_close",
)

register(
    ServerFactory,
    "mult_opacity_server",
    rules=[
        fill_in_rule(rule)
        for rule in [
            {"window_class": "Window1", "default_opacity": 0.2},
            {"window_id": "window2", "default_opacity": 0.5},
        ]
    ],
)

register(
    ServerFactory,
    "mult_flash_opacity_server",
    rules=[
        fill_in_rule(rule)
        for rule in [
            {"window_class": "Window1", "flash_opacity": 0.2},
            {"window_id": "window2", "flash_opacity": 0.5},
        ]
    ],
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
def string_type():
    if sys.version_info[0] < 3:
        return basestring
    else:
        return str


@fixture
def list_only_test_windows(monkeypatch, windows):
    """Only list test window ids."""
    monkeypatch.setattr("flashfocus.xutil.list_mapped_windows", lambda: windows)


@fixture
def valid_config_types():
    return {key: val["type"] for key, val in default_flash_param().items()}


@fixture
def blank_cli_options():
    return {
        key: None
        for key, val in default_flash_param().items()
        if val["location"] == "any" or val["location"] == "cli"
    }


@fixture
def valid_bool():
    return ["false", "False", "FALSE", "True", "true", "TRUE", True, False]


@fixture
def client_monitor():
    return ClientMonitor(Queue())


@fixture
def xhandler():
    return XHandler(Queue())


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
