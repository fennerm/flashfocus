"""A pid file is used to ensure only one flashfocus instance is running."""

import fcntl
from pathlib import Path
import os
import sys


def determine_runtime_dir() -> Path:
    """Determine the runtime dir.

    Uses XDG_RUNTIME_DIR if defined, otherwise falls back to /tmp

    """
    xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime_dir is not None:
        runtime_dir = xdg_runtime_dir
    else:
        runtime_dir = "/tmp"
    return Path(runtime_dir)


def get_pid_file() -> Path:
    runtime_dir = determine_runtime_dir()
    return runtime_dir / "flashfocus.pid"


# This must be declared globally or else the file is closed when it goes out of scope
PID = get_pid_file().open("a")


def lock_pid_file() -> None:
    fcntl.lockf(PID, fcntl.LOCK_EX | fcntl.LOCK_NB)


def unlock_pid_file() -> None:
    fcntl.lockf(PID, fcntl.LOCK_UN)


def ensure_single_instance():
    """Ensure that no other flashfocus instances are running."""
    try:
        lock_pid_file()
    except IOError:
        sys.exit("Another flashfocus instance is running.")
