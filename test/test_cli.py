"""Testsuite for the flashfocus CLI."""
from flashfocus.server import FlashServer
from flashfocus.cli import init_server


def return_opacity(self, *args, **kwargs):
    return self.router.flashers[-1].flash_opacity


def test_custom_configfile(monkeypatch, blank_cli_options, configfile):
    cli_options = blank_cli_options
    cli_options["config"] = str(configfile)
    monkeypatch.setattr(FlashServer, "event_loop", return_opacity)
    opacity = init_server(cli_options)
    assert opacity == 0.5
