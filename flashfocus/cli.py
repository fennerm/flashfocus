"""flashfocus command line interface."""
import logging
from logging import info as log
import os

import click
from tendo import singleton

from flashfocus.flasher import Flasher

# Set LOGLEVEL environment variable to DEBUG or WARNING to change logging
# verbosity.
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))


def validate_positive_decimal(ctx, param, value):
    """Validate the opacity command line argument."""
    if not 0 <= value <= 1:
        raise ValueError(
            "%s parameter not in valid range, should be between 0 and 1", param)
    return value


def format_time(ctx, param, value):
    """Validate the time command line argument and convert to seconds."""
    validate_positive_int(ctx, param, value)
    return value / 1000


def validate_positive_int(ctx, param, value):
    """Check that a command line argument is a positive integer."""
    if value < 1:
        raise ValueError("%s parameter cannot be < 1", param)
    if int(value) != value:
        raise ValueError("%s parameter must be an int, not a float", param)
    return value


@click.command()
@click.option('--opacity', '-o',
              default=0.8,
              callback=validate_positive_decimal,
              help='Opacity of the window during a flash.')
@click.option('--time', '-t',
              default=500,
              callback=format_time,
              help='Flash time interval (in milliseconds).')
@click.option('--simple', '-s', is_flag=True,
              help='Don\'t animate flashes. Setting this parameter improves '
                   'performance but causes rougher opacity transitions.')
@click.option('--ntimepoints', '-n',
              default=10,
              callback=validate_positive_int,
              help='Number of timepoints in the flash animation. Higher values '
                   'will lead to smoother animations with the cost of '
                   'increased X server requests. Ignored if --simple is set.')
@click.option('--debug', '-d', is_flag=True, help='Run in debug mode.')
def cli(opacity, time, ntimepoints, simple, debug):
    """Simple focus animations for tiling window managers."""
    params = locals()
    single_instance_lock = singleton.SingleInstance()
    log('Initializing with parameters:')
    log('%s', params)
    flasher = Flasher(opacity, time, ntimepoints, simple)
    if debug:
        log('Flasher attributes: %s', flasher.__dict__)
    else:
        flasher.monitor_focus()
