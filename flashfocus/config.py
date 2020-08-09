"""Parsing the user config file.

Marshmallow is used to parse and validate the config/CLI schemas. All of this validation code might
seem overly complex (and perhaps it is!) but it was motivated by a couple of concerns:
1. The 'rules' field in the config allows users to nest all of the primary config options in
   addition to some unique options. This is complicated to parse without a schema.
2. I want to make sure that the user gets helpful feedback when their config file is invalid.
"""
import logging
import os
from pathlib import Path
import re
import shutil
from typing import Any, Dict, List, Optional, Pattern, Union

from marshmallow import fields, post_load, Schema, validates_schema, ValidationError
import yaml
from yaml.parser import ParserError
from yaml.scanner import ScannerError

from flashfocus.compat import DisplayProtocol, get_display_protocol
from flashfocus.errors import ConfigInitError, ConfigLoadError
from flashfocus.types import Number
from flashfocus.util import indent

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

FLASH_LONE_WINDOWS_OPTS = ["never", "on_open_close", "on_switch", "always"]
X11_MATCH_PROPERTIES = {"window_class", "window_id"}
WAYLAND_MATCH_PROPERTIES = {"window_name", "app_id"}
WINDOW_MATCH_PROPERTIES = X11_MATCH_PROPERTIES | WAYLAND_MATCH_PROPERTIES
WINDOW_MATCH_NAMES = {x.replace("_", "-") for x in WINDOW_MATCH_PROPERTIES}
CLI_ONLY_OPTS = ["config", "verbosity"]


def validate_positive_number(data: Number) -> None:
    """Check that a value is a positive number."""
    if not data > 0:
        raise ValidationError("Not a positive number", data)


def validate_decimal(data: Number) -> None:
    """Check that a value is a float between 0 and 1 inclusive."""
    if not 0 <= data <= 1:
        raise ValidationError("Not in valid range, expected a float between 0 and 1")


def validate_flash_lone_windows(data: str) -> None:
    if data not in FLASH_LONE_WINDOWS_OPTS:
        raise ValidationError(
            "Invalid 'flash-lone-windows' value, expected one of "
            f"{', '.join(FLASH_LONE_WINDOWS_OPTS)}",
            data,
        )


class Regex(fields.Field):
    """Schema field for validating a regex."""

    def _deserialize(self, value: str, attr: str, obj: Dict, **kwargs) -> Pattern[str]:
        try:
            return re.compile(value)
        except Exception:
            raise ValidationError("Invalid regex")


class BaseSchema(Schema):
    """Base class for `RulesSchema` and `ConfigSchema`.

    Contains validation criteria for options which can be present both in the global config and in
    flash rules.
    """

    flash_opacity: fields.Number = fields.Number(validate=validate_decimal)
    default_opacity: fields.Number = fields.Number(validate=validate_decimal)  # noqa: E704
    simple: fields.Boolean = fields.Boolean()
    time: fields.Number = fields.Number(validate=validate_positive_number)
    ntimepoints: fields.Integer = fields.Integer(validate=validate_positive_number)
    flash_on_focus: fields.Boolean = fields.Boolean()
    flash_lone_windows: fields.String = fields.String(validate=validate_flash_lone_windows)
    flash_fullscreen: fields.Boolean = fields.Boolean()

    @validates_schema(pass_original=True)
    def check_unknown_fields(self, data: Dict, original_data: Dict, **kwargs) -> None:
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
    app_id = Regex()
    window_name = Regex()

    @validates_schema()
    def check_for_matching_criteria(self, data: Dict, **kwargs) -> None:
        """Check that rule contains at least one method for matching a window."""
        if not any([prop in data for prop in WINDOW_MATCH_PROPERTIES]):
            raise ValidationError(
                "No criteria for matching rule to window. Must set one of "
                f"({', '.join(WINDOW_MATCH_NAMES)})"
            )


class ConfigSchema(BaseSchema):
    """Schema for options which are present in global config but not rules.

    Contains a nested `RulesSchema` used to validate rules.

    """

    rules: fields.Nested = fields.Nested(RulesSchema, many=True)

    @post_load()
    def set_rule_defaults(self, config: Dict, **kwargs) -> Dict:
        """Set default values for the nested `RulesSchema`."""
        if "rules" not in config:
            config["rules"] = None
        else:
            for rule in config["rules"]:
                for prop in BASE_PROPERTIES:
                    if prop not in rule:
                        rule[prop] = config[prop]
        return config


def load_config(config_file: Path) -> Dict:
    """Load the config yaml file into a dictionary."""
    try:
        with config_file.open("r") as f:
            config: Dict = yaml.load(f, Loader=yaml.FullLoader)
    except FileNotFoundError:
        raise ConfigLoadError(f"Config file does not exist: {config_file}")
    except (ScannerError, ParserError) as e:
        logging.error(str(e))
        raise ConfigLoadError(
            "Error encountered in config file. Check that your config file is formatted correctly."
        )
    else:
        dehyphen(config)
    return config


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


def unset_invalid_x11_options(config: Dict) -> None:
    if config["rules"] is not None:
        rules = list()
        for rule in config["rules"]:
            if not WAYLAND_MATCH_PROPERTIES & rule.keys():
                rules.append(rule)
            else:
                logging.warning(
                    f"Detected a rule using wayland-only display properties, dropping it:\n{rule}"
                )
        if len(rules) == 0:
            rules = None
        config["rules"] = rules


def unset_invalid_sway_options(config: Dict) -> None:
    if config["flash_fullscreen"] is True:
        logging.warning(
            "Fullscreen windows cannot be flashed in sway. Setting flash-fullscreen=false. "
            "https://github.com/fennerm/flashfocus/issues/55"
        )
        config["flash_fullscreen"] = False


def unset_invalid_options_for_wm(config: Dict) -> None:
    """Clear any config options which don't work with the user's WM."""
    display_protocol = get_display_protocol()
    if display_protocol == DisplayProtocol.X11:
        unset_invalid_x11_options(config)
    elif display_protocol == DisplayProtocol.SWAY:
        unset_invalid_sway_options(config)


def validate_config(config: Dict) -> Dict:
    """Validate the config file and command line parameters."""
    try:
        schema: ConfigSchema = ConfigSchema(strict=True)
    except TypeError:
        # Strict parameter removed in the latest versions of marshmallow
        schema = ConfigSchema()

    try:
        loaded: Dict = schema.load(config)
    except ValidationError as err:
        raise ConfigLoadError(construct_config_error_msg(err.messages))

    try:
        # In marshmallow v2 the validated data needed to be accessed from the tuple after load
        validated_config = loaded.data
    except AttributeError:
        # In marshmallow v3 the validated data is returned directly from load
        validated_config = loaded

    unset_invalid_options_for_wm(validated_config)

    return validated_config


def dehyphen(config: Dict) -> None:
    """Replace hyphens in config dictionary with underscores."""
    # The conversion to list is necessary so that we're not modifying the keys while looping through
    # them
    for option in list(config.keys()):
        if option == "rules":
            for rule in config["rules"]:
                dehyphen(rule)
        else:
            new_key = option.replace("-", "_")
            config[new_key] = config.pop(option)


def hierarchical_merge(dicts: List[Dict]) -> Dict:
    """Merge a list of dictionaries.

    Parameters
    ----------
    dicts
        Dicts are given in order of precedence from lowest to highest. I.e if
        dicts[0] and dicts[1] have a shared key, the output dict
        will contain the value from dicts[1].

    """
    outdict = dict()
    for dct in dicts:
        try:
            for key, value in dct.items():
                if value is not None:
                    outdict[key] = value
        except (TypeError, AttributeError):
            # dict was probably None
            pass
    return outdict


def init_user_configfile() -> Path:
    """Create the initial user config file if it doesn't exist, otherwise return it."""
    config_file_path = find_config_file()
    if config_file_path is None:
        config_file_path = build_config_search_path()[0]
        try:
            config_file_path.parent.mkdir()
        except (AttributeError, FileNotFoundError):
            raise ConfigInitError(f"Failed to create the user config file in {config_file_path}.")
        default_config_path = get_default_config_file()
        shutil.copy(default_config_path, config_file_path)

    return config_file_path


def build_config_search_path() -> List[Path]:
    """Return a list of user config locations in order of search priority."""
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    search_path = list()
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


def merge_config_sources(user_config: Dict, default_config: Dict, cli_options: Dict) -> Dict:
    """Merge the user, default configs and CLI options into a single dict."""
    for opt in CLI_ONLY_OPTS:
        del cli_options[opt]
    config = hierarchical_merge([default_config, user_config, cli_options])
    validated_config = validate_config(config)
    return validated_config


def load_merged_config(config_file_path: Path, cli_options: Dict) -> Dict:
    """Merge the config options from the config file and the CLI into a dict."""
    default_config_path = get_default_config_file()
    default_config = load_config(default_config_path)
    user_config = load_config(config_file_path)
    if user_config:
        logging.info(f"Loading configuration from {config_file_path}")
    config = merge_config_sources(
        user_config=user_config, default_config=default_config, cli_options=cli_options
    )
    return config
