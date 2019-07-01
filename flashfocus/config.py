"""Parsing the user config file."""
import logging
import os
from pathlib import Path
import re
from shutil import copy
import sys
from typing import Any, Dict, Iterator, List, Optional, Pattern, Union

from marshmallow import fields, post_load, Schema, validates_schema, ValidationError
from parser import ParserError
import yaml
from yaml.scanner import ScannerError

from flashfocus.types import Number

# Properties which may be contained both in global config and in flash rules.
BASE_PROPERTIES = [
    "flash_opacity",
    "default_opacity",
    "simple",
    "flash_on_focus",
    "ntimepoints",
    "time",
    "flash_lone_windows",
]


def validate_positive_number(data: Number) -> None:
    """Check that a value is a positive number."""
    if not data > 0:
        raise ValidationError("Not a positive number", data)


def validate_decimal(data: Number) -> None:
    """Check that a value is a float between 0 and 1 inclusive."""
    if not 0 <= data <= 1:
        raise ValidationError("Not in valid range, expected a float between 0 and 1")


def validate_flash_lone_windows(data: str) -> None:
    accepted_values = ["never", "on_open_close", "on_switch", "always"]
    if data not in accepted_values:
        raise ValidationError(
            f"Invalid 'flash-lone-windows' value, expected one of {', '.join(accepted_values)}",
            data,
        )


class Regex(fields.Field):
    """Schema field for validating a regex."""

    def deserialize(self, value: str, attr, obj) -> Pattern[str]:
        try:
            return re.compile(value)
        except Exception:
            raise ValidationError("Invalid regex")


class BaseSchema(Schema):
    """Base class for `RulesSchema` and `ConfigSchema`.

    Contains validation criteria for options which can be present both in the
    global config and in flash rules.

    """

    flash_opacity = fields.Number(validate=validate_decimal)
    default_opacity = fields.Number(validate=validate_decimal)
    simple = fields.Boolean()
    time = fields.Number(validate=validate_positive_number)
    ntimepoints = fields.Integer(validate=validate_positive_number)
    flash_on_focus = fields.Boolean()
    flash_lone_windows = fields.String(validate=validate_flash_lone_windows)

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data, original_data):
        """Check that unknown options were not passed by the user."""
        try:
            unknown = set(original_data) - set(self.fields)
        except TypeError:
            unknown = set(original_data[0]) - set(self.fields)
        if unknown:
            raise ValidationError("Unknown parameter", unknown)


class RulesSchema(BaseSchema):
    """Schema for options which are present in rules but not global config."""

    window_class = Regex()
    window_id = Regex()

    @validates_schema()
    def check_for_matching_criteria(self, data):
        """Check that rule contains at least one method for matching a window."""
        if not any([param in data for param in ["window_class", "window_id"]]):
            raise ValidationError("No criteria for matching rule to window")


class ConfigSchema(BaseSchema):
    """Schema for options which are present in global config but not rules.

    Contains a nested `RulesSchema` used to validate rules.

    """

    preset_opacity = fields.Boolean()
    rules = fields.Nested(RulesSchema, many=True)

    @post_load()
    def set_rule_defaults(self, config: Dict) -> None:
        """Set default values for the nested `RulesSchema`."""
        if "rules" not in config:
            config["rules"] = None
        else:
            for rule in config["rules"]:
                for property in BASE_PROPERTIES:
                    if property not in rule:
                        rule[property] = config[property]


def load_config(config_file: Path) -> Dict[str, str]:
    """Load the config file into a dictionary.

    Returns
    -------
    Dict[str, str]

    """
    if config_file:
        try:
            with open(str(config_file), "r") as f:
                config = yaml.load(f)
                dehyphen(config)
        except (ScannerError, ParserError) as e:
            sys.exit("Error in config file:\n" + str(e))
    else:
        config = None
    return config


def indent(n: int) -> str:
    """Return `n` indents."""
    return "  " * n


def parse_config_error(option: Union[int, str], err: Union[List, Dict], ntabs: int = 1) -> str:
    """Parse Marshmallow schema error."""
    if isinstance(option, int):
        option = "rule " + str(option + 1)
    option = option.replace("_", "-")
    error_msg = "".join([indent(ntabs), "- ", option, ":\n"])
    if isinstance(err, list):
        # Base case
        output = error_msg + "".join([indent(ntabs + 1), "- ", err[0], "\n"])
    else:
        # Recursively parse error
        output = error_msg + parse_config_error(*err.popitem(), ntabs=ntabs + 1)
    return output


def construct_config_error_msg(errors: Dict[str, Any]) -> str:
    """Construct an error message for an invalid configuration setup.

    Parameters
    ----------
    config
        Merged dictionary of configuration options from CLI, user configfile and
        default configfile
    errors
        Dictionary of schema validation errors passed by Marshmallow

    Returns
    -------
    str

    """
    error_msg = "Failed to parse config\n"
    for error_param, exception_msg in errors.items():
        error_msg += parse_config_error(error_param, exception_msg)
    return error_msg


def validate_config(config: Dict) -> Dict:
    """Validate the config file and command line parameters."""
    try:
        validated = ConfigSchema(strict=True).load(config)
    except TypeError:
        # Strict parameter removed in the latest versions of marshmallow
        validated = ConfigSchema().load(config)
    except ValidationError as err:
        logging.error(construct_config_error_msg(err.messages))
        sys.exit(1)
    return validated.data


def dehyphen(config: Dict) -> None:
    """Replace hyphens in config dictionary with underscores."""
    for option in list(config.keys()):
        if option == "rules":
            for rule in config["rules"]:
                dehyphen(rule)
        else:
            new_key = option.replace("-", "_")
            config[new_key] = config.pop(option)


def merge_config_sources(cli_options: Dict, user_config: Dict, default_config: Dict) -> Dict:
    """
    Parameters
    ----------
    cli_options
        Dictionary of command line options
    default_config
        Dictionary of options from the default configfile
    user_config
        Dictionary of options from the user configfile

    Returns
    -------
    Dict[str, str]

    """
    if user_config:
        logging.info("Loading configuration from %s", user_config)
    config = hierarchical_merge([default_config, user_config, cli_options])
    validated_config = validate_config(config)
    return validated_config


def hierarchical_merge(dicts: List[Dict]) -> Dict:
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
    for d in dicts:
        try:
            for key, value in d.items():
                if value is not None:
                    outdict[key] = value
        except (TypeError, AttributeError):
            # d was probably None
            pass
    return outdict


def init_user_configfile() -> Path:
    """Create the initial user config file if it doesn't exist."""
    config_file_path = find_config_file()
    if config_file_path is None:
        try:
            config_file_path = build_config_search_path()[0]
            os.makedirs(os.path.dirname(config_file_path))
        except OSError:
            pass
        assert config_file_path is not None
        default_config_path = get_default_config_file()
        copy(default_config_path, config_file_path)

    return config_file_path


def build_config_search_path() -> List[Path]:
    """Return a list of user config locations in order of search priority."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    search_path = []
    if xdg_config_home is not None:
        search_path.append(Path(xdg_config_home) / "flashfocus" / "flashfocus.yml")

    search_path += [
        Path.home() / ".config" / "flashfocus" / "flashfocus.yml",
        Path.home() / ".flashfocus.yml",
    ]
    return search_path


def find_config_file() -> Optional[Path]:
    """Find the flashfocus config file if it exists."""
    for location in build_config_search_path():
        if location.exists():
            return location

    return None


def get_default_config_file() -> Path:
    """Get the location of the default flashfocus config file."""
    return Path(__file__).parent / "default_config.yml"


class Config:
    def __init__(self) -> None:
        self._config: Dict[str, str] = dict()

    def __getitem__(self, key: str) -> str:
        return self._config[key]

    def __contains__(self, item: str) -> bool:
        return item in self._config

    def __iter__(self) -> Iterator[str]:
        return iter(self._config)

    def __repr__(self) -> str:
        return repr(self._config)

    def get(self, key: str, default_value: Any = None) -> Any:
        return self._config.get(key, default_value)

    def load(self, config_file_path: Path, cli_options: Dict) -> None:
        """Merge the CLI options with the user and default config files and return as a dict."""
        default_config_path = get_default_config_file()

        if not os.path.exists(config_file_path):
            logging.error(f"{config_file_path} does not exist")
            sys.exit("Could not load config file, exiting...")
        default_config = load_config(default_config_path)
        user_config = load_config(config_file_path)
        self._config = merge_config_sources(
            cli_options=cli_options, user_config=user_config, default_config=default_config
        )
