"""Test suite for flashfocus.syspaths."""
import os

from flashfocus.syspaths import *


def test_determine_runtime_dir_with_xdg():
    os.environ["XDG_RUNTIME_DIR"] = "/run/user/1000"
    assert determine_runtime_dir() == "/run/user/1000"


def test_determine_runtime_dir_without_xdg():
    del os.environ["XDG_RUNTIME_DIR"]
    assert determine_runtime_dir() == "/tmp"
