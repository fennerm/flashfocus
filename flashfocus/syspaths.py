"""Determine where flashfocus files should be placed."""
import os


def determine_runtime_dir():
    """Determine the runtime dir.

    Uses XDG_RUNTIME_DIR if defined, otherwise falls back to /tmp

    """
    xdg_runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if xdg_runtime_dir:
        runtime_dir = xdg_runtime_dir
    else:
        runtime_dir = "/tmp"
    return runtime_dir


def build_config_search_path():
    """Return a list of user config locations in order of search priority."""
    locations = []
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        config_file = os.path.join(
            xdg_config_home, "flashfocus", "flashfocus.yml"
        )
        locations.append(config_file)

    home = os.path.expanduser("~")
    locations.append(os.path.join(home, ".config/flashfocus/flashfocus.yml"))
    locations.append(os.path.join(home, ".flashfocus.yml"))
    return locations


def find_config_file():
    """Find the flashfocus config file if it exists."""
    for location in CONFIG_SEARCH_PATH:
        if os.path.exists(location):
            return location

    return None


DEFAULT_CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), "default_config.yml"
)
CONFIG_SEARCH_PATH = build_config_search_path()
USER_CONFIG_FILE = find_config_file()
RUNTIME_DIR = determine_runtime_dir()
