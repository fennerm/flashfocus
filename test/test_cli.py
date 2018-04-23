"""Testsuite for the flashfocus CLI."""
from pytest import (
    fixture,
    mark,
    raises,
    warns,
)

from flashfocus.cli import *
from flashfocus.server import FlashServer
from flashfocus.syspaths import DEFAULT_CONFIG_FILE


@fixture
def blank_cli_options():
    cli_options = {
        'flash-opacity': None,
        'default-opacity': None,
        'time': None,
        'ntimepoints': None,
        'simple': False
    }
    return cli_options


@fixture
def default_config():
    return load_config(DEFAULT_CONFIG_FILE)


@mark.parametrize('option,values', [
    ('flash_opacity', ['-1', '2', 'foo', -1, 2]),
    ('default_opacity', ['-1', '2', 'foo', -1, 2]),
    ('time', ['0', '-1', 'foo', 0, -1]),
    ('ntimepoints', ['0', '-1', 'foo', 0, -1]),
    ('simple', ['foo', '10'])
])
@mark.parametrize('input_type', ['cli', 'file'])
def test_invalid_param(option, values, input_type, blank_cli_options,
                       default_config):
    for value in values:
        config = {option: value}
        with raises(SystemExit):
            if input_type == 'cli':
                merge_config_sources(config, default_config, None)
            else:
                merge_config_sources(blank_cli_options, default_config, config)


@mark.parametrize('option,values', [
    ('flash_opacity', ['0.5', '0', '1', 0.5, 0, 1]),
    ('default_opacity', ['0.5', '0', '1', 0.5, 0, 1]),
    ('time', ['200', '50.5', 200, 50.5]),
    ('ntimepoints', ['10', 10]),
    ('simple', ['false', 'False', 'FALSE', 'True', 'true', 'TRUE', True, False])
])
@mark.parametrize('input_type', ['cli', 'file'])
def test_valid_param(option, values, input_type, blank_cli_options,
                     string_type, default_config):
    for value in values:
        config = {option: value}
        if input_type == 'cli':
            validated_config = merge_config_sources(config, default_config,
                                                    None)
        else:
            validated_config = merge_config_sources(
                blank_cli_options, default_config, config)
        assert isinstance(validated_config['time'], float)
        assert isinstance(validated_config['ntimepoints'], int)
        assert isinstance(validated_config['flash_opacity'], float)
        assert isinstance(validated_config['default_opacity'], float)
        assert validated_config['simple'] in [True, False]
        assert len(validated_config) == len(blank_cli_options)


@mark.parametrize('input,expected', [
    ({'foo-bar': 1, 'car': 2}, {'foo_bar': 1, 'car': 2}),
    ({'car': 2}, {'car': 2}),
    (dict(), dict()),
    (None, None)
])
def test_replace_hyphens(input, expected):
    assert replace_hyphens(input) == expected


@mark.parametrize('old,new,expected', [
    ({'a': 1, 'b': 2}, {'a': 2, 'c': 3}, {'a': 2, 'b': 2, 'c': 3}),
    (None, {'a': 2, 'c': 3}, {'a': 2, 'c': 3}),
    ({'a': 2, 'c': 3}, None, {'a': 2, 'c': 3}),
    (dict(), {'a': 2, 'c': 3}, {'a': 2, 'c': 3}),
    ({'a': 2, 'c': 3}, dict(), {'a': 2, 'c': 3}),
])
def test_overwrite(old, new, expected):
    assert overwrite(old, new) == expected


def test_opacity_deprecation(monkeypatch):
    def return_true(*args, **kwargs):
        return True

    monkeypatch.setattr(FlashServer, 'event_loop', return_true)
    with warns(UserWarning):
        init_server({'opacity': '0.8'})
