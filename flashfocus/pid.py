import fcntl
import os
import sys


def determine_runtime_dir() -> str:
    """Determine the runtime dir.

    Uses XDG_RUNTIME_DIR if defined, otherwise falls back to /tmp

    """
    xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime_dir is not None:
        runtime_dir = xdg_runtime_dir
    else:
        runtime_dir = "/tmp"
    return runtime_dir


def lock_pid_file():
    """Lock the flashfocus PID file."""
    # The pid file for flashfocus. Used to ensure that only one instance is active.
    runtime_dir = determine_runtime_dir()
    pid = open(os.path.join(runtime_dir, "flashfocus.pid"), "a")
    fcntl.lockf(pid, fcntl.LOCK_EX | fcntl.LOCK_NB)


def ensure_single_instance():
    """Ensure that no other flashfocus instances are running."""
    try:
        lock_pid_file()
    except IOError:
        sys.exit("Another flashfocus instance is running.")
