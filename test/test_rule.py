"""Testsuite for flashfocus.rule."""
from pytest import mark

from flashfocus.rule import Rule
from test.helpers import to_regex


@mark.parametrize(
    "id_regex,class_regex,should_match",
    [
        # Id matches exactly, no class
        (r"window1", None, True),
        # Id regex matches, no class
        (r"^win.*$", None, True),
        # Class matches exactly, no id
        (None, r"Window1", True),
        # Class regex matches, no id
        (None, r"^Win.*$", True),
        # Both id and class exactly match
        (r"window1", r"Window1", True),
        # Class matches but id doesn't
        (r"window2", r"Window1", False),
        # Id matches but class doesn't
        (r"window1", r"Window2", False),
        # Neither match
        (r"window2", r"Window2", False),
        # Neither defines (always matches)
        (None, None, True),
    ],
)
def test_rule_matching(id_regex, class_regex, should_match):
    rule = Rule(to_regex(id_regex), to_regex(class_regex))
    assert rule.match("window1", "Window1") == should_match
