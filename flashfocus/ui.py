#!/usr/bin/env python
"""flashfocus command line interface."""
import fcntl
import logging
import os
import sys

import click

from flashfocus.color import green, red
from flashfocus.config import load_merged_config
from flashfocus.server import FlashServer
from flashfocus.syspaths import RUNTIME_DIR

# Set LOGLEVEL environment variable to DEBUG or WARNING to change logging
# verbosity.
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"), format="%(levelname)s: %(message)s")

if sys.stderr.isatty():
    # Colored logging categories
    logging.addLevelName(logging.WARNING, red(logging.getLevelName(logging.WARNING)))
    logging.addLevelName(logging.ERROR, red(logging.getLevelName(logging.ERROR)))
    logging.addLevelName(logging.INFO, green(logging.getLevelName(logging.INFO)))


# The pid file for flashfocus. Used to ensure that only one instance is active.
PID = open(os.path.join(RUNTIME_DIR, "flashfocus.pid"), "a")


def lock_pid_file():
    """Lock the flashfocus PID file."""
    fcntl.lockf(PID, fcntl.LOCK_EX | fcntl.LOCK_NB)


def ensure_single_instance():
    """Ensure that no other flashfocus instances are running."""
    try:
        lock_pid_file()
    except IOError:
        sys.exit("Another flashfocus instance is running.")


@click.command()
@click.option("--config", "-c", required=False, default=None, help="Config file location")
@click.option(
    "--flash-opacity",
    "-o",
    type=float,
    required=False,
    help="Opacity of the window during a flash.",
)
@click.option(
    "--default-opacity",
    "-e",
    type=float,
    required=False,
    help="Default window opacity. flashfocus will reset the window "
    "opacity to this value post-flash. (default: 1.0)",
)
@click.option(
    "--time", "-t", type=int, required=False, help="Flash time interval (in milliseconds)."
)
@click.option(
    "--simple",
    "-s",
    required=False,
    is_flag=True,
    default=None,
    help="Don't animate flashes. Setting this parameter improves "
    "performance but causes rougher opacity transitions. "
    "(default: false)",
)
@click.option(
    "--ntimepoints",
    "-n",
    required=False,
    type=int,
    help="Number of timepoints in the flash animation. Higher values "
    "will lead to smoother animations with the cost of "
    "increased X server requests. Ignored if --simple is set. "
    "(default: 10)",
)
@click.option(
    "--opacity", required=False, type=float, help="DEPRECATED: use --flash-opacity/-o instead"
)
@click.option(
    "--flash-on-focus/--no-flash-on-focus",
    required=False,
    is_flag=True,
    default=None,
    help=(
        "If True, windows will be flashed on focus. Otherwise, "
        "windows will only be flashed on request. (default: True)"
    ),
)
@click.option(
    "--flash-lone-windows",
    "-l",
    required=False,
    default=None,
    help=(
        "Should windows be flashed when they are the only one on the desktop?. "
        "One of [never, always, on_open_close, on_switch]."
    ),
)
def cli(*args, **kwargs):
    """Simple focus animations for tiling window managers."""
    init_server(kwargs)


def init_server(cli_options):
    """Initialize the flashfocus server with given command line options."""
    ensure_single_instance()

    if "opacity" in cli_options:
        if cli_options["opacity"] is not None:
            logging.warn("--opacity is deprecated, please use --flash-opacity/-o instead")
            if cli_options["flash_opacity"] is None:
                cli_options["flash_opacity"] = cli_options["opacity"]
        del cli_options["opacity"]

    config = load_merged_config(cli_options)

    logging.info("Initializing with parameters:")
    logging.info("%s", config)
    server = FlashServer(**config)
    return server.event_loop()


if __name__ == "__main__":
    cli()
