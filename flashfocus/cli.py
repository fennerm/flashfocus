#!/usr/bin/env python
"""Command line interface."""
import logging
from pathlib import Path
import sys
from typing import Dict

import click

from flashfocus.errors import ConfigInitError, ConfigLoadError, UnsupportedWM
from flashfocus.config import init_user_configfile, load_merged_config
from flashfocus.logging import setup_logging
from flashfocus.pid import ensure_single_instance
from flashfocus.server import FlashServer


# Basic logging init - we'll change the log level later
logging.basicConfig(level="WARNING", format="%(levelname)s: %(message)s")


def check_for_supported_wm():
    try:
        import flashfocus.compat  # noqa F401
    except UnsupportedWM as error:
        logging.error(str(error))
        sys.exit("Unrecoverable error, exiting...")


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
    help="Don't animate flashes. Setting this parameter improves performance but causes rougher "
    "opacity transitions. (default: false)",
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
    "--flash-fullscreen/--no-flash-fullscreen",
    required=False,
    is_flag=True,
    default=None,
    help="If True, fullscreen windows are flashed (default: True).",
)
@click.option(
    "--flash-lone-windows",
    "-l",
    required=False,
    default=None,
    type=click.Choice(["never", "always", "on_open_close", "on_switch"]),
    help="Flash windows when they are the only one on the desktop?"
)
@click.option(
    "--verbosity",
    "-v",
    required=False,
    default="INFO",
    type=click.Choice(["INFO", "WARNING", "DEBUG", "ERROR"]),
    help="Set the logging verbosity."
)
def cli(*args, **kwargs) -> None:
    """Simple focus animations for tiling window managers."""
    init_server(kwargs)


def init_server(cli_options: Dict) -> None:
    """Initialize the flashfocus server with given command line options."""
    setup_logging(cli_options["verbosity"])
    check_for_supported_wm()
    ensure_single_instance()

    config_file_path = cli_options["config"]
    if config_file_path is None:
        try:
            config_file_path = init_user_configfile()
        except (ConfigInitError, ConfigLoadError) as error:
            if str(error):
                logging.error(str(error))
            sys.exit("Could not load config file, exiting...")
    config = load_merged_config(config_file_path=Path(config_file_path), cli_options=cli_options)
    logging.info(f"Initializing with parameters:\n{config}")
    server = FlashServer(config)
    # The return statement is a hack for testing purposes. It allows us to mock the return of
    # the function.
    return server.event_loop()


if __name__ == "__main__":
    cli()
