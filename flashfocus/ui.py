#!/usr/bin/env python
"""flashfocus command line interface."""
import fcntl
import logging
from logging import info, warn
import os
import sys

import click

from flashfocus.color import green, red
from flashfocus.config import create_user_configfile, merge_config_sources
from flashfocus.server import FlashServer
from flashfocus.syspaths import RUNTIME_DIR, USER_CONFIG_FILE

# Set LOGLEVEL environment variable to DEBUG or WARNING to change logging
# verbosity.
logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO"),
    format="%(levelname)s: %(message)s",
)

if sys.stderr.isatty():
    # Colored logging categories
    logging.addLevelName(
        logging.WARNING, red(logging.getLevelName(logging.WARNING))
    )
    logging.addLevelName(
        logging.ERROR, red(logging.getLevelName(logging.ERROR))
    )
    logging.addLevelName(
        logging.INFO, green(logging.getLevelName(logging.INFO))
    )


# The pid file for flashfocus. Used to ensure that only one instance is active.
PID = open(os.path.join(RUNTIME_DIR, "flashfocus.pid"), "a")


def ensure_single_instance():
    """Ensure that no other flashfocus instances are running."""
    try:
        fcntl.lockf(PID, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        sys.exit("Another flashfocus instance is running.")


@click.command()
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
    "--time",
    "-t",
    type=int,
    required=False,
    help="Flash time interval (in milliseconds).",
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
    "--opacity",
    required=False,
    type=float,
    help="DEPRECATED: use --flash-opacity/-o instead",
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
def cli(*args, **kwargs):
    """Simple focus animations for tiling window managers."""
    init_server(kwargs)


def init_server(cli_options):
    """Initialize the flashfocus server with given command line options."""
    ensure_single_instance()

    if cli_options["opacity"]:
        warn("--opacity is deprecated, please use --flash-opacity/-o instead")
        if "flash_opacity" not in cli_options:
            cli_options["flash_opacity"] = cli_options["opacity"]
    del cli_options["opacity"]

    if not USER_CONFIG_FILE:
        create_user_configfile()

    config = merge_config_sources(cli_options)

    info("Initializing with parameters:")
    info("%s", config)
    server = FlashServer(**config)
    return server.event_loop()


if __name__ == "__main__":
    cli()
