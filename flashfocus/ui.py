#!/usr/bin/env python
"""flashfocus command line interface."""
import fcntl
import logging
from logging import (
    info,
    warn,
)
import os
import re
from shutil import copy
import sys

import click
from marshmallow import (
    fields,
    Schema,
    validates_schema,
    ValidationError,
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
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'),
                    format='%(levelname)s: %(message)s')

# Colored logging categories
logging.addLevelName(logging.WARNING, "\033[1;31m%s\033[1;0m" %
                     logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" %
                     logging.getLevelName(logging.ERROR))
logging.addLevelName(logging.INFO, "\033[92m%s\033[1;0m" %
                     logging.getLevelName(logging.INFO))

# The pid file for flashfocus. Used to ensure that only one instance is active.
PID = open(os.path.join(RUNTIME_DIR, 'flashfocus.pid'), 'a')


def validate_positive_number(data):
    """Check that a value is a positive number."""
    if not data > 0:
        raise ValidationError('Not a positive number'.format(data))


def validate_decimal(data):
    """Check that a value is a decimal between 0 and 1."""
    if not 0 <= data <= 1:
        raise ValidationError(
            'Not in valid range, expected a float between 0 and 1'.format(data))


class Regex(fields.Field):
    def _deserialize(self, value, attr, obj):
        try:
            return re.compile(value)
        except:
            raise ValidationError('Invalid regex')


class BaseSchema(Schema):
    flash_opacity = fields.Number(validate=validate_decimal)
    default_opacity = fields.Number(validate=validate_decimal)
    simple = fields.Boolean()
    time = fields.Number(validate=validate_positive_number)
    ntimepoints = fields.Integer(validate=validate_positive_number)

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        try:
            unknown = set(original_data) - set(self.fields)
        except TypeError:
            unknown = set(original_data[0]) - set(self.fields)
        if unknown:
            raise ValidationError('Unknown parameter', unknown)


class RulesSchema(BaseSchema):
    flash = fields.Boolean()
    window_class = Regex()
    window_id = Regex()
    tab = fields.Boolean()
    new_window = fields.Boolean()

    @validates_schema()
    def check_required_fields(self, data):
        minimal_req = ['tab', 'new_window', 'window_class', 'window_id']
        if not any(param in data for param in minimal_req):
            raise ValidationError('No criteria for matching rule to window')


class ConfigSchema(BaseSchema):
    preset_opacity = fields.Boolean()
    rules = fields.Nested(RulesSchema, many=True)


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
                config = replace_key_chars(yaml.load(f), '-', '_')
        except yaml.scanner.ScannerError as e:
            sys.exit('Error in config file:\n' + str(e))
    else:
        config = None
    return config


def validate_config(config):
    """Validate the config file and command line parameters."""
    schema = ConfigSchema()
    validated = schema.load(config)
    errors = validated[1]
    if not errors:
        if hasattr(validated[0]['rules'][0], 'window_class'):
            import pytest
            pytest.set_trace()

    if errors:
        error_msg = 'CONFIG ERROR(S):\n'
        for error_param, exception_msg in errors.items():
            error_msg += '\t{} ({}) -> {}\n'.format(
                error_param.replace('_', '-'), config[error_param],
                exception_msg[0])
        sys.exit(error_msg)
    return validated[0]


def replace_key_chars(a_dict, old, new):
    """Replace a substring in dict keys with another substring."""
    if a_dict:
        new_dict = dict()
        for key in a_dict:
            new_key = key.replace(old, new)
            new_dict[new_key] = a_dict[key]
    else:
        new_dict = a_dict
    return new_dict


def merge_config_sources(cli_options,
                         default_config=load_config(DEFAULT_CONFIG_FILE),
                         user_config=load_config(USER_CONFIG_FILE)):
    """Parse configuration by merging the default and user config files

    Returns
    -------
    Dict[str, str]

    """
    if USER_CONFIG_FILE:
        info('Loading configuration from %s', USER_CONFIG_FILE)
    config = hierarchical_merge([default_config, user_config, cli_options])
    validated_config = validate_config(config)
    return validated_config


def hierarchical_merge(dicts):
    """Merge a list of dictionaries.

    Parameters
    ----------
    dicts: List[Dict]
        Dicts are given in order of precedence from lowest to highest. I.e if
        dicts[0] and dicts[1] have a shared key, the output dict
        will contain the value from dicts[1].

    Returns
    -------
    Dict

    """
    outdict = dict()
    for x in dicts:
        if x:
            for key, value in x.items():
                if value is not None:
                    outdict[key] = value
    return outdict


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
@click.option('--preset-opacity/--no-preset-opacity', required=False,
              is_flag=True,
              help=('If True, flashfocus will set windows to their default'
                    'opacity on startup'))
def cli(*args, **kwargs):
    """Simple focus animations for tiling window managers."""
    init_server(kwargs)


def init_server(cli_options):
    """Initialize the flashfocus server with given command line options."""
    ensure_single_instance()

    if cli_options['opacity']:
        warn('--opacity is deprecated, please use --flash-opacity/-o instead')
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
    return server.event_loop()


if __name__ == '__main__':
    cli()
