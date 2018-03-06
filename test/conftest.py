import i3ipc
from pytest import fixture


@fixture
def i3():
    return i3ipc.Connection()
