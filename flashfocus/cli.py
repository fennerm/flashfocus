#!/usr/bin/env python
'''Flash i3 windows on focus'''
import logging
from logging import info as log
import os
import sys

import click

from flashfocus.Xutil import MAX_OPACITY
from i3flash.server import FlashServer

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))


@click.command()
@click.option('--opacity', '-o', default=0.9,
              help='Opacity of the window during a flash')
@click.option('--time', '-t', default=150, help='Flash time interval (in ms)')
@click.option('--current', '-c', help='Flash the currently focused window')
def cli(opacity, time, current):
    '''Click command line interface group'''
    # TODO: set logging parameters based on args
    log('Checking command-line arguments...')
    opacity = format_opacity(opacity)
    time = time / 1000
    log('Arguments are valid')

    if current:
        log('Initializing a client...')
        FlashClient(opacity, time).run()
    else:
        log('Initializing the server...')
        FlashServer(opacity, time).run()


def format_opacity(opacity):
    '''Convert the opacity paramater from decimal to int'''
    if opacity > 1 or opacity < 0:
        sys.exit("Invalid opacity argument, expected a decimal")

    return int(opacity * MAX_OPACITY)
