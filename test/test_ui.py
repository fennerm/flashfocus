"""Testsuite for the flashfocus CLI."""
import logging
import re
try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from pytest import (
    fixture,
    mark,
    raises,
)
from pytest_lazyfixture import lazy_fixture

from flashfocus.ui import *
from flashfocus.server import FlashServer
from flashfocus.syspaths import DEFAULT_CONFIG_FILE


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
        'tab': bool,
        'new_window': bool
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
    }
    return cli_options


@fixture
def default_config():
    return load_config(DEFAULT_CONFIG_FILE)


@fixture
def invalid_rules():
    rules = [
        # No window_class or window_id present
        [{'flash': 'True'}],
        # Invalid flash values
        [{'window-class': 'foo', 'flash': 2}],
        [{'window-class': 'foo', 'flash': 'bar'}],
        # List value for window class/id
        [{'window-class': ['foo', 'bar']}],
        [{'window_id': ['foo', 'bar']}],
        # preset-opacity parameter cannot be used inside rule
        [{'window_id': 'foo', 'preset_opacity': 'False'}],
    ]
    return rules


@mark.parametrize('option,values', [
    ('flash_opacity', ['-1', '2', 'foo', -1, 2]),
    ('default_opacity', ['-1', '2', 'foo', -1, 2]),
    ('time', ['0', '-1', 'foo', 0, -1]),
    ('ntimepoints', ['0', '-1', 'foo', 0, -1]),
    ('simple', ['foo', '10']),
    ('preset_opacity', ['foo', '10']),
    ('rules', lazy_fixture('invalid_rules'))
])
@mark.parametrize('input_type', ['cli', 'file'])
def test_invalid_param(option, values, input_type, blank_cli_options,
                       default_config):
    if input_type == 'cli' and option == 'rules':
        return
    for value in values:
        # Need to refresh these variables as they might be altered during merge
        defaults = default_config
        blanks = blank_cli_options
        config = {option: value}
        with raises(SystemExit):
            if input_type == 'cli':
                merge_config_sources(config, defaults, None)
            else:
                merge_config_sources(blanks, defaults, config)


def check_validated_config(config, expected_types):
    for name, value in config.items():
        try:
            if expected_types[name] == bool:
                assert value in [True, False]
            else:
                assert isinstance(value, expected_types[name])
        except KeyError:
            pass


@fixture
def valid_bool():
    return ['false', 'False', 'FALSE', 'True', 'true', 'TRUE', True, False]


@mark.parametrize('option,values', [
    ('flash_opacity', ['0.5', '0', '1', 0.5, 0, 1]),
    ('default_opacity', ['0.5', '0', '1', 0.5, 0, 1]),
    ('time', ['200', '50.5', 200, 50.5]),
    ('ntimepoints', ['10', 10]),
    ('simple', lazy_fixture('valid_bool')),
    ('preset_opacity', lazy_fixture('valid_bool')),
])
@mark.parametrize('input_type', ['cli', 'file'])
def test_valid_param(option, values, input_type, blank_cli_options,
                     string_type, default_config, valid_config_types):
    for value in values:
        config = {option: value}
        if input_type == 'cli':
            validated_config = merge_config_sources(config, default_config,
                                                    None)
        else:
            validated_config = merge_config_sources(
                blank_cli_options, default_config, config)
        check_validated_config(validated_config, valid_config_types)
        assert len(validated_config) == len(blank_cli_options) + 1


@mark.parametrize('rules', [
    # Match criteria without any action is valid (but useless)
    [{'window-class': 'foo'}],
    # Check flash parameter accepted
    [{'window-class': 'foo', 'flash': 'False'}],
    # Special TAB and NEW_WINDOW rules don't require match criteria
    [{'tab': 'True', 'flash_opacity': '0.2'}],
    [{'new-window': 'True', 'flash_opacity': '0.2'}],
    # Multiple rules can be defined
    [{'tab': 'True', 'flash_opacity': '0.2'},
     {'window-class': 'foo', 'simple': 'True'}],
    # Check that global params are accepted
    [{'window-class': 'foo', 'default_opacity': '0.5'}],
    [{'window-class': 'foo', 'simple': 'True'}],
    [{'window-class': 'foo', 'ntimepoints': '10'}],
    [{'window-class': 'foo', 'time': '100'}],
    [{'window-class': 'foo', 'flash_opacity': '0.2'}],
])
def test_rules_validation(rules, blank_cli_options, default_config,
                          valid_config_types):
    rules_dict = {'rules': rules}
    validated_config = merge_config_sources(
        blank_cli_options, default_config, rules_dict)
    for rule in validated_config['rules']:
        check_validated_config(rule, valid_config_types)


@mark.parametrize('input,expected', [
    ({'foo-bar': 1, 'car': 2}, {'foo_bar': 1, 'car': 2}),
    ({'car': 2}, {'car': 2}),
    (dict(), dict()),
    (None, None)
])
def test_replace_key_chars(input, expected):
    assert replace_key_chars(input, '-', '_') == expected


def test_opacity_deprecation(monkeypatch):
    def return_opacity(self, *args, **kwargs):
        return self.flasher.flash_opacity

    monkeypatch.setattr(FlashServer, 'event_loop', return_opacity)
    assert init_server({'opacity': '0.5'}) == 0.5


@mark.parametrize('old,new,expected', [
    ([{'a': 1, 'b': 2}, {'a': 2, 'c': 3}], {'a': 2, 'b': 2, 'c': 3}),
    ([None, {'a': 2, 'c': 3}], {'a': 2, 'c': 3}),
    ([{'a': 2, 'c': 3}, None], {'a': 2, 'c': 3}),
    ([dict(), {'a': 2, 'c': 3}], {'a': 2, 'c': 3}),
    ([{'a': 2, 'c': 3}, dict()], {'a': 2, 'c': 3}),
    ([{'a': 2}, {'a': 3}, {'a': 4}], {'a': 4})
])
def test_hierarchical_merge(dicts, expected):
    assert hierarchical_merge(dicts) == expected


def test_overwrite_returns_a_new_dict():
    a = {'a': 1, 'b': 2}, {'a': 2, 'c': 3}
    a_copy = a.copy()
    b = {'a': 2, 'b': 2, 'c': 3}
    overwrite(a, b)
    assert a == a_copy


def test_issues_warning_for_unrecognized_config_option(
        monkeypatch, default_config, blank_cli_options):
    monkeypatch.setattr(logging, 'warn', MagicMock())
    unrecognized_option = {'foo': 'bar'}
    merge_config_sources(blank_cli_options, default_config, unrecognized_option)
    assert 'unrecognized' in logging.warn.call_args()
