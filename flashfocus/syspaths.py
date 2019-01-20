"""Determine where flashfocus files should be placed."""
import os


def determine_runtime_dir():
    """Determine the runtime dir.

    Uses XDG_RUNTIME_DIR if defined, otherwise falls back to /tmp

    """
    xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime_dir is not None:
        runtime_dir = xdg_runtime_dir
    else:
        runtime_dir = "/tmp"
    return runtime_dir


def build_config_search_path():
    """Return a list of user config locations in order of search priority."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    home_dir = os.path.expanduser("~")
    search_path = []
    if xdg_config_home is not None:
        search_path.append(
            os.path.join(xdg_config_home, "flashfocus", "flashfocus.yml")
        )

    search_path += [
        os.path.join(home_dir, ".config", "flashfocus", "flashfocus.yml"),
        os.path.join(home_dir, ".flashfocus.yml"),
    ]
    return search_path


def find_config_file():
    """Find the flashfocus config file if it exists."""
    for location in build_config_search_path():
        if os.path.exists(location):
            return location

    return None


def get_default_config_file():
    """Get the location of the default flashfocus config file."""
    return os.path.join(os.path.dirname(__file__), "default_config.yml")


RUNTIME_DIR = determine_runtime_dir()
