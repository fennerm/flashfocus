"""Determine where flashfocus files should be placed."""
import os


def determine_runtime_dir():
    """Determine the runtime dir.

    Uses XDG_RUNTIME_DIR if defined, otherwise falls back to /tmp

    """
    xdg_runtime_dir = os.environ.get('XDG_RUNTIME_DIR')
    if xdg_runtime_dir:
        runtime_dir = xdg_runtime_dir
    else:
        runtime_dir = '/tmp'
    return runtime_dir

RUNTIME_DIR = determine_runtime_dir()
