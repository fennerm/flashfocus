"""Testsuite for the flashfocus CLI."""
import pytest
from typing import Any

from flashfocus.cli import init_server
from flashfocus.server import FlashServer


def return_opacity(self: FlashServer, *args: Any, **kwargs: Any) -> float:
    return self.router.flashers[-1].flash_opacity


def test_custom_configfile(  # type: ignore[no-untyped-def]
    monkeypatch: pytest.MonkeyPatch,
    blank_cli_options: dict,
    configfile,
) -> None:
    cli_options = blank_cli_options
    cli_options["config"] = str(configfile)
    monkeypatch.setattr(FlashServer, "event_loop", return_opacity)
    opacity = init_server(cli_options)  # type: ignore[func-returns-value]
    assert opacity == 0.5
