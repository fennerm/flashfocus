"""Testsuite for the flashfocus CLI."""
from click.testing import CliRunner
from pytest import (
    fixture,
    mark,
)

from flashfocus.cli import cli


@fixture
def runner():
    """A click CliRunner instance."""
    return CliRunner()


def test_cli_defaults(runner):
    assert runner.invoke(cli, ['--debug']).exit_code == 0


@mark.parametrize('param', [
    ['-o', 1],
    ['-o', 0.5],
    ['-o', 0],
    ['-e', 1],
    ['-e', 0.5],
    ['-e', 0],
    ['-t', 1],
    ['-t', 100],
    ['-n', 5],
    ['--simple']
])
def test_valid_cli_param(runner, param):
    result = runner.invoke(cli, ['--debug'] + param)
    assert result.exit_code == 0


@mark.parametrize('param', [
    ['-o', -1],
    ['-o', 'foo'],
    ['-e', -1],
    ['-e', 'foo'],
    ['-t', 0],
    ['-t', 'foo'],
    ['-n', 0],
    ['-n', -1],
    ['-n', 'foo']
])
def test_invalid_cli_param(runner, param):
    assert runner.invoke(cli, ['--debug'] + param).exit_code != 0
