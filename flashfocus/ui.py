#!/usr/bin/env python
"""flashfocus command line interface."""
import logging
import os
import sys
from typing import Dict

import click

from flashfocus.color import green, red
from flashfocus.config import config
from flashfocus.pid import ensure_single_instance
from flashfocus.server import FlashServer

# Set LOGLEVEL environment variable to DEBUG or WARNING to change logging
# verbosity.
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"), format="%(levelname)s: %(message)s")

if sys.stderr.isatty():
    # Colored logging categories
    logging.addLevelName(logging.WARNING, red(logging.getLevelName(logging.WARNING)))
    logging.addLevelName(logging.ERROR, red(logging.getLevelName(logging.ERROR)))
    logging.addLevelName(logging.INFO, green(logging.getLevelName(logging.INFO)))


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
def cli(*args, **kwargs) -> None:
    """Simple focus animations for tiling window managers."""
    init_server(kwargs)


def init_server(cli_options: Dict) -> None:
    """Initialize the flashfocus server with given command line options."""
    ensure_single_instance()
    config.load_merged_config(cli_options)
    logging.info("Initializing with parameters:")
    logging.info(f"{config}")
    server = FlashServer()
    return server.event_loop()


if __name__ == "__main__":
    cli()
