"""Testsuite for flashfocus.config."""
from __future__ import annotations
from copy import deepcopy

import pytest
from pytest_lazyfixture import lazy_fixture

from flashfocus.config import (
    construct_config_error_msg,
    dehyphen,
    get_default_config_file,
    hierarchical_merge,
    load_config,
    load_merged_config,
    merge_config_sources,
    validate_config,
)
from flashfocus.errors import ConfigLoadError

# WOW these tests are flakey and overengineered :(


@pytest.fixture
def default_config() -> dict:
    return load_config(get_default_config_file())


@pytest.fixture
def invalid_rules() -> list:
    rules = [
        # No window_class or window_id present
        [{"flash_on_focus": True}],
        [{"flash_lone_windows": "always"}],
        [{"flash_fullscreen": True}],
        # Invalid values
        [{"window_class": "foo", "flash_on_focus": 2}],
        [{"window_class": "foo", "flash_on_focus": "bar"}],
        [{"window_class": "foo", "flash_on_focus": "this"}],
        [{"window_class": "foo", "flash_on_focus": "that"}],
        # List value for window class/id
        [{"window_class": ["foo", "bar"]}],
        [{"window_id": ["foo", "bar"]}],
    ]
    return rules


@pytest.mark.parametrize(
    "option,values",
    [
        ("flash_opacity", ["-1", "2", "foo", -1, 2]),
        ("default_opacity", ["-1", "2", "foo", -1, 2]),
        ("time", ["0", "-1", "foo", 0, -1]),
        ("ntimepoints", ["0", "-1", "foo", 0, -1]),
        ("simple", ["foo", "10"]),
        ("flash_lone_windows", ["foo", "true"]),
        ("flash_fullscreen", ["foo", 3]),
        ("rules", lazy_fixture("invalid_rules")),
    ],
)
@pytest.mark.parametrize("input_type", ["cli", "file"])
def test_invalid_param(
    option: str, values: list, input_type: str, blank_cli_options: dict, default_config: dict
) -> None:
    if input_type == "cli" and option == "rules":
        return
    for value in values:
        # Need to refresh these variables as they might be altered during merge
        defaults = deepcopy(default_config)
        blanks = deepcopy(blank_cli_options)
        with pytest.raises(ConfigLoadError):
            if input_type == "cli":
                blanks[option] = value
                merge_config_sources(cli_options=blanks, user_config={}, default_config=defaults)
            else:
                config = {option: value}
                merge_config_sources(
                    cli_options=blanks, user_config=config, default_config=defaults
                )


def check_validated_config(config: dict, expected_types: dict[str, list[type]]) -> None:
    for name, value in config.items():
        try:
            if expected_types[name] == [bool]:
                assert value in [True, False]
            else:
                assert True in [isinstance(value, typ) for typ in expected_types[name]]
        except KeyError:
            pass


@pytest.mark.parametrize(
    "option,values",
    [
        ("flash_opacity", ["0.5", "0", "1", 0.5, 0, 1]),
        ("default_opacity", ["0.5", "0", "1", 0.5, 0, 1]),
        ("time", ["200", "50.5", 200, 50.5]),
        ("ntimepoints", ["10", 10]),
        ("simple", lazy_fixture("valid_bool")),
        ("flash_on_focus", lazy_fixture("valid_bool")),
        ("flash_fullscreen", lazy_fixture("valid_bool")),
        ("flash_lone_windows", ["always", "never", "on_open_close", "on_switch"]),
    ],
)
@pytest.mark.parametrize("input_type", ["cli", "file"])
def test_valid_param(
    option: str,
    values: list,
    input_type: str,
    blank_cli_options: dict,
    default_config: dict,
    valid_config_types: dict[str, list[type]],
) -> None:
    for value in values:
        blanks = deepcopy(blank_cli_options)
        if input_type == "cli":
            blanks[option] = value
            validated_config = merge_config_sources(
                cli_options=blanks, user_config={}, default_config=default_config
            )
        else:
            config = {option: value}
            validated_config = merge_config_sources(
                cli_options=blanks, user_config=config, default_config=default_config
            )
        check_validated_config(validated_config, valid_config_types)


@pytest.mark.parametrize(
    "rules",
    [
        # Match criteria without any action is valid (but useless)
        [{"window_class": "foo"}],
        # Multiple rules can be defined
        [{"window_id": "bar", "flash_opacity": "0.2"}, {"window_class": "foo", "simple": "True"}],
        # Check that global params are accepted
        [{"window_class": "foo", "default_opacity": "0.5"}],
        [{"window_class": "foo", "simple": True}],
        [{"window_class": "foo", "ntimepoints": "10"}],
        [{"window_class": "foo", "time": "100"}],
        [{"window_class": "foo", "flash_opacity": "0.2"}],
        [{"window_class": "foo", "flash_on_focus": True}],
        [{"window_class": "foo", "flash_lone_windows": "always"}],
        [{"window_class": "foo", "flash_fullscreen": False}],
        # Regexes are valid
        [{"window_class": "^indo.*$", "time": "100"}],
    ],
)
def test_rules_validation(
    rules: list[dict],
    blank_cli_options: dict,
    default_config: dict,
    valid_config_types: dict[str, list[type]],
) -> None:
    rules_dict = {"rules": rules}
    validated_config = merge_config_sources(default_config, rules_dict, blank_cli_options)
    for rule in validated_config["rules"]:
        check_validated_config(rule, valid_config_types)


@pytest.mark.parametrize(
    "arg,expected",
    [
        ({"foo-bar": 1, "car": 2}, {"foo_bar": 1, "car": 2}),
        ({"car": 2}, {"car": 2}),
        ({"car": 2, "rules": [{"foo-bar": 3}]}, {"car": 2, "rules": [{"foo_bar": 3}]}),
        (dict(), dict()),
    ],
)
def test_dehyphen(arg: dict, expected: dict) -> None:
    dehyphen(arg)
    assert arg == expected


@pytest.mark.parametrize(
    "dicts,expected",
    [
        ([{"a": 1, "b": 2}, {"a": 2, "c": 3}], {"a": 2, "b": 2, "c": 3}),
        ([None, {"a": 2, "c": 3}], {"a": 2, "c": 3}),
        ([{"a": 2, "c": 3}, None], {"a": 2, "c": 3}),
        ([dict(), {"a": 2, "c": 3}], {"a": 2, "c": 3}),
        ([{"a": 2, "c": 3}, dict()], {"a": 2, "c": 3}),
        ([{"a": 2}, {"a": 3}, {"a": 4}], {"a": 4}),
    ],
)
def test_hierarchical_merge(dicts: list[dict], expected: dict) -> None:
    assert hierarchical_merge(dicts) == expected


def test_hierarchical_merge_returns_a_new_dict() -> None:
    a = {"a": 1, "b": 2}
    a_copy = a.copy()
    b = {"a": 2, "b": 2, "c": 3}
    hierarchical_merge([a, b])
    assert a == a_copy


def test_rule_defaults_inherited_from_global_param(
    default_config: dict, blank_cli_options: dict
) -> None:
    user_config = {"rules": [{"window_class": "foo"}]}
    validated = merge_config_sources(
        default_config=default_config, user_config=user_config, cli_options=blank_cli_options
    )
    assert validated["rules"][0]["flash_opacity"] == default_config["flash_opacity"]


def test_rules_added_to_config_dict_if_not_present_in_config(
    default_config: dict, blank_cli_options: dict
) -> None:
    validated = merge_config_sources(
        default_config=default_config, user_config=default_config, cli_options=blank_cli_options
    )
    assert "rules" in validated


def test_load_config(configfile) -> None:  # type: ignore[no-untyped-def]
    assert load_config(configfile) == {"default_opacity": 1, "flash_opacity": 0.5}


def test_if_x11_wayland_rules_are_dropped_during_validation(default_config: dict) -> None:
    default_config["rules"] = [{"app_id": "foo", "default_opacity": 0.8}]
    config = validate_config(default_config)
    assert config["rules"] is None


def test_construct_rules_config_error_message() -> None:
    errors = {"rules": {0: ["msg"]}}
    expected = "Failed to parse config\n"
    expected += "  - rules:\n"
    expected += "    - rule 1:\n"
    expected += "      - msg\n"
    assert construct_config_error_msg(errors) == expected


def test_construct_non_rules_config_error_message() -> None:
    errors = {"flash_opacity": ["msg"]}
    expected = "Failed to parse config\n"
    expected += "  - flash-opacity:\n"
    expected += "    - msg\n"
    assert construct_config_error_msg(errors) == expected


@pytest.fixture
def invalid_yaml(tmpdir):  # type: ignore[no-untyped-def]
    yml = tmpdir.join("invalid.yml")
    yml.write("1 :::1: 1:")
    return yml


def test_invalid_yaml_passed_to_load_config(invalid_yaml) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ConfigLoadError):
        load_config(invalid_yaml)


def test_load_merged_config_with_no_custom_config(  # type: ignore[no-untyped-def]
    monkeypatch: pytest.MonkeyPatch, blank_cli_options: dict, configfile
) -> None:
    conf = load_merged_config(config_file_path=configfile, cli_options=blank_cli_options)
    assert conf.get("flash_opacity") == 0.5


def test_load_merged_config_with_custom_config(  # type: ignore[no-untyped-def]
    monkeypatch: pytest.MonkeyPatch, blank_cli_options: dict, configfile_with_02_flash_opacity
) -> None:
    conf = load_merged_config(
        config_file_path=configfile_with_02_flash_opacity, cli_options=blank_cli_options
    )
    assert conf.get("flash_opacity") == 0.2
