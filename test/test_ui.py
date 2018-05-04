"""Testsuite for the flashfocus CLI."""
from flashfocus.server import FlashServer
from flashfocus.ui import *


def test_opacity_deprecation(monkeypatch):
    def return_opacity(self, *args, **kwargs):
        return self.default_flasher.flash_opacity

    monkeypatch.setattr(FlashServer, 'event_loop', return_opacity)
    assert init_server({'opacity': '0.5'}) == 0.5
