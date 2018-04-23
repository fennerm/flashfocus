"""Unit test fixtures."""
import sys

from pytest import fixture
import xpybutil
import xpybutil.window


from flashfocus.flasher import Flasher
from flashfocus.server import FlashServer
from flashfocus.sockets import (
    init_client_socket,
    init_server_socket,
)

from test.helpers import (
    change_focus,
    StubServer,
    WindowSession,
)


@fixture
def windows():
    """Display session with multiple open windows."""
    windows = WindowSession()
    change_focus(windows.ids[0])
    yield windows.ids
    windows.destroy()


@fixture
def window(windows):
    """Single blank window."""
    return windows[0]


@fixture
def flash_server():
    """FlashServer instance."""
    return FlashServer(
        default_opacity=1,
        flash_opacity=0.8,
        time=200,
        ntimepoints=10,
        simple=False)


@fixture
def flasher():
    """Flasher instance."""
    return Flasher(
        time=200,
        flash_opacity=0.8,
        default_opacity=1,
        ntimepoints=10,
        simple=False
    )


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
def fresh_xpybutil():
    """Reimport xpybutil to refresh the X connection."""
    try:
        import importlib
        importlib.reload(xpybutil)
        importlib.reload(xpybutil.window)
    except:
        reload(xpybutil)
        reload(xpybutil.window)


@fixture
def string_type():
    if sys.version_info[0] < 3:
        return basestring
    else:
        return str
