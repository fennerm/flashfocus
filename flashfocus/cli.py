"""Command line interface."""
import logging
from logging import info as log
import os

import click

from flashfocus.monitor import FocusMonitor

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))


def validate_opacity(ctx, param, value):
    """Validate the opacity command line argument."""
    if not 0 <= value <= 1:
        raise ValueError(
            "Opacity not in valid range, should be between 0 and 1")
    return value


def format_time(ctx, param, value):
    """Validate the time command line argument and convert to seconds."""
    if value < 0:
        raise ValueError("Time parameter cannot be negative")
    return value / 1000


@click.command()
@click.option('--opacity', '-o', default=0.9, callback=validate_opacity,
              help='Opacity of the window during a flash')
@click.option('--time', '-t', default=200, callback=format_time,
              help='Flash time interval (in ms)')
def cli(opacity, time):
    """Click command line interface group."""
    log('Arguments are valid')
    log('Initializing the daemon...')
    FocusMonitor(opacity, time).monitor_focus()
