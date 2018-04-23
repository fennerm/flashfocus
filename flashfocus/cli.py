#!/usr/bin/env python
"""flashfocus command line interface."""
import fcntl
import logging
from logging import info
import os
from shutil import copy
import sys
from warnings import warn

import click
from schema import (
    And,
    Schema,
    SchemaError,
    Use,
)
import yaml

from flashfocus.server import FlashServer
from flashfocus.syspaths import (
    CONFIG_SEARCH_PATH,
    DEFAULT_CONFIG_FILE,
    RUNTIME_DIR,
    USER_CONFIG_FILE,
)

# Set LOGLEVEL environment variable to DEBUG or WARNING to change logging
# verbosity.
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

# The pid file for flashfocus. Used to ensure that only one instance is active.
PID = open(os.path.join(RUNTIME_DIR, 'flashfocus.pid'), 'a')


def to_bool(x):
    """Convert 'true'/'false' to bool."""
    if isinstance(x, bool):
        return x
    x = x.lower()
    if x == 'true':
        return True
    elif x == 'false':
        return False
    else:
        return None


# Schema used to validate cli options and config file
CONFIG_SCHEMA = Schema({
    'flash_opacity': And(Use(float), lambda n: 0 <= n <= 1),
    'default_opacity': And(Use(float), lambda n: 0 <= n <= 1),
    'time': And(Use(float), lambda n: 0 < n),
    'ntimepoints': And(Use(int), lambda n: 0 < n),
    'simple': And(Use(to_bool), bool)
})


def ensure_single_instance():
    """Ensure that no other flashfocus instances are running."""
    try:
        fcntl.lockf(PID, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        sys.exit('Another flashfocus instance is running.')


def load_config(config_file):
    """Load the config file into a dictionary.

    Returns
    -------
    Dict[str, str]

    """
    if config_file:
        try:
            with open(config_file, 'r') as f:
                config = replace_hyphens(yaml.load(f))
        except yaml.scanner.ScannerError as e:
            sys.exit('Error in config file:\n' + str(e))
    else:
        config = None
    return config


def validate_config(config):
    """Validate the config file and command line parameters."""
    try:
        validated = CONFIG_SCHEMA.validate(config)
    except SchemaError as e:
        error_parts = str(e).split()
        option = error_parts[1]
        message = ' '.join(error_parts[3:])
        sys.exit('Error in {} parameter:\n {}'.format(option, message))
    return validated


def overwrite(original, new):
    """Overwrite shared keys in `original` with `new`.

    Parameters
    ----------
    original: Dict
    new: Dict

    Returns
    -------
    Dict

    """
    if not original:
        return new

    if new:
        for key, value in new.items():
            if value:
                original[key] = value
    return original


def replace_hyphens(dic):
    """Replace hyphens in dictionary keys with underscores."""
    if dic:
        new_dic = dict()
        for key in dic:
            new_key = key.replace('-', '_')
            new_dic[new_key] = dic[key]
    else:
        new_dic = dic
    return new_dic


def merge_config_sources(cli_options,
                         default_config=load_config(DEFAULT_CONFIG_FILE),
                         user_config=load_config(USER_CONFIG_FILE)):
    """Parse configuration by merging the default and user config files

    Returns
    -------
    Dict[str, str]

    """
    if USER_CONFIG_FILE:
        info('Loading configuration from %s...', USER_CONFIG_FILE)
    file_config = overwrite(default_config, user_config)
    config = overwrite(file_config, cli_options)
    validated_config = validate_config(config)
    return validated_config


@click.command()
@click.option('--flash-opacity', '-o', required=False,
              help='Opacity of the window during a flash.')
@click.option('--default-opacity', '-e', required=False,
              help='Default window opacity. flashfocus will reset the window '
                   'opacity to this value post-flash. (default: 1.0)')
@click.option('--time', '-t', required=False,
              help='Flash time interval (in milliseconds).')
@click.option('--simple', '-s', required=False, is_flag=True,
              help='Don\'t animate flashes. Setting this parameter improves '
                   'performance but causes rougher opacity transitions. '
                   '(default: false)')
@click.option('--ntimepoints', '-n', required=False,
              help='Number of timepoints in the flash animation. Higher values '
                   'will lead to smoother animations with the cost of '
                   'increased X server requests. Ignored if --simple is set. '
                   '(default: 10)')
@click.option('--opacity', required=False,
              help='DEPRECATED: use --flash-opacity/-o instead')
def cli(*args, **kwargs):
    """Simple focus animations for tiling window managers."""
    init_server(kwargs)


def init_server(cli_options):
    """Initialize the flashfocus server with given command line options."""
    ensure_single_instance()

    if cli_options['opacity']:
        warn('--opacity is deprecated, please used --flash-opacity/-o instead')
        if 'flash_opacity' not in cli_options:
            cli_options['flash_opacity'] = cli_options['opacity']
    del cli_options['opacity']

    if not USER_CONFIG_FILE:
        try:
            os.makedirs(os.path.dirname(CONFIG_SEARCH_PATH[0]))
        except OSError:
            pass
        copy(DEFAULT_CONFIG_FILE, CONFIG_SEARCH_PATH[0])

    config = merge_config_sources(cli_options)

    info('Initializing with parameters:')
    info('%s', config)
    server = FlashServer(**config)
    server.event_loop()

if __name__ == '__main__':
    cli()
