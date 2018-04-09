"""Unit test fixtures."""
from pytest import fixture

from flashfocus.flashfocus import (
    Flasher,
    FlashServer,
)
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
    return FlashServer(flash_opacity=0.8,
                       time=0.2,
                       ntimepoints=10,
                       simple=False)

@fixture
def flasher():
    """Flasher instance."""
    return Flasher(
        time=0.2,
        flash_opacity=0.8,
        default_opacity=1,
        ntimepoints=10,
        simple=False
    )

@fixture
def server_socket():
    """Bound, listening server socket."""
    socket = init_server_socket()
    yield socket
    socket.close()


@fixture
def client_socket(server_socket):
    """Client socket."""
    return init_client_socket()


@fixture
def stub_server(server_socket):
    """StubServer instance."""
    return StubServer(server_socket)
