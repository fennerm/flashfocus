"""Unit test fixtures."""
try:
    from queue import (
        Empty,
        Queue,
    )
except ImportError:
    from Queue import (
        Empty,
        Queue,
    )
import re
import sys

from factory import Factory
from pytest import fixture
from pytest_factoryboy import register
import xpybutil
import xpybutil.window


from flashfocus.flasher import Flasher
from flashfocus.producer import (
    ClientMonitor,
    FocusMonitor,
)
from flashfocus.rule import RuleMatcher
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


class ServerFactory(Factory):
    """Factory for producing FlashServer fixture instances."""

    class Meta:
        model = FlashServer

    default_opacity = 1
    flash_opacity = 0.8
    time = 100
    ntimepoints = 4
    simple = False
    preset_opacity = True
    rules = None


register(ServerFactory, 'flash_server')

register(ServerFactory, 'transparent_flash_server', default_opacity=0.4)

register(ServerFactory, 'flash_server_with_classrule',
         rules=[{'window_class': 'Window2', 'flash-opacity': 0}])

register(ServerFactory, 'flash_server_with_idrule',
         rules=[{'window_id': 'window2', 'flash-opacity': 0}])

register(ServerFactory, 'flash_server_with_matched_rules',
         rules=[{
             'window_class': 'Window2',
             'window_id': 'window2',
             'flash-opacity': 0}])

register(ServerFactory, 'flash_server_with_unmatched_classrule',
         rules=[{
             'window_class': 'foo',
             'window_id': 'window2',
             'flash-opacity': 0}])

register(ServerFactory, 'flash_server_with_unmatched_idrule',
         rules=[{
             'window_class': 'Window2',
             'window_id': 'foo',
             'flash-opacity': 0}])


register(ServerFactory, 'mult_rule_server',
         rules=[
             {
                 'window_class': 'Window2',
                 'window_id': 'window2',
                 'flash-opacity': 0
             },
             {
                 'window_class': 'Window1',
                 'flash-opacity': 0.2
             }])

register(ServerFactory, 'flash_server_with_matched_idregex',
         rules=[{
             'window_id': '^.*ndow.*$',
             'flash-opacity': 0}])

register(ServerFactory, 'flash_server_with_matched_classregex',
         rules=[{
             'window_class': '^.*ndow.*$',
             'flash-opacity': 0}])


class FlasherFactory(Factory):
    """Factory for producing Flasher fixture instances."""
    class Meta:
        model = Flasher

    default_opacity = 1
    flash_opacity = 0.8
    time = 100
    ntimepoints = 4
    simple = False


register(FlasherFactory, 'flasher')

register(FlasherFactory, 'pointless_flasher', flash_opacity=1)


class RuleMatcherFactory(Factory):
    """Factory for producing RuleMatcher fixture instances."""
    class Meta:
        model = RuleMatcher

    defaults = {
        'default_opacity': 1,
        'flash_opacity': 0.8,
        'time': 100,
        'ntimepoints': 4,
        'simple': False,
        'flash_on_focus': True
    }
    rules = [
        # Matches window1 but not 2
        {
            'window_id': re.compile('^.*1$'),
            'flash_opacity': 0,
            'default_opacity': 0.8,
            'time': 100,
            'ntimepoints': 4,
            'simple': False,
            'flash_on_focus': False
        }
    ]

register(RuleMatcherFactory, 'rule_matcher')


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


@fixture
def list_only_test_windows(windows):
    """Generate a function which lists the test window ids."""
    def lister():
        return windows

    return lister


@fixture
def valid_config_types():
    types = {
        'time': float,
        'ntimepoints': int,
        'flash_opacity': float,
        'default_opacity': float,
        'simple': bool,
        'preset_opacity': bool,
        'window_class': re._pattern_type,
        'window_id': re._pattern_type,
        'flash_on_focus': bool
    }
    return types


@fixture
def blank_cli_options():
    cli_options = {
        'flash-opacity': None,
        'default-opacity': None,
        'time': None,
        'ntimepoints': None,
        'simple': None,
        'preset_opacity': None,
        'flash_on_focus': None
    }
    return cli_options


@fixture
def valid_bool():
    return ['false', 'False', 'FALSE', 'True', 'true', 'TRUE', True, False]


@fixture
def client_monitor():
    return ClientMonitor(Queue())


@fixture
def focus_monitor():
    return FocusMonitor(Queue())
