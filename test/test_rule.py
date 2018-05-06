"""Testsuite for flashfocus.rule."""
try:
    from unittest.mock import (
        call,
        MagicMock,
    )
except ImportError:
    from mock import (
        call,
        MagicMock,
    )
from pytest import (
    lazy_fixture,
    mark,
    raises,
)
from xcffib.xproto import WindowError

from flashfocus.rule import *
from test.helpers import to_regex


@mark.parametrize('id_regex,class_regex,should_match', [
    # Id matches exactly, no class
    (r'window1', None, True),
    # Id regex matches, no class
    (r'^win.*$', None, True),
    # Class matches exactly, no id
    (None, r'Window1', True),
    # Class regex matches, no id
    (None, r'^Win.*$', True),
    # Both id and class exactly match
    (r'window1', r'Window1', True),
    # Class matches but id doesn't
    (r'window2', r'Window1', False),
    # Id matches but class doesn't
    (r'window1', r'Window2', False),
    # Neither match
    (r'window2', r'Window2', False),
    # Neither defines (always matches)
    (None, None, True)
])
def test_rule_matching(id_regex, class_regex, should_match):
    rule = Rule(to_regex(id_regex), to_regex(class_regex))
    assert rule.match('window1', 'Window1') == should_match


def test_rule_matcher_match_raises_window_error(rule_matcher):
    with raises(WindowError):
        rule_matcher.match(0)


@mark.parametrize('matcher', [
    lazy_fixture('rule_matcher'),
    lazy_fixture('norule_matcher')
])
def test_rule_matcher_match(matcher, window):
    rule, flasher = matcher.match(window)
    assert rule == matcher.rules[0]
    assert flasher == matcher.flashers[0]
    if len(matcher.rules) > 1:
        assert flasher.flash_opacity == 0


def test_rule_matcher_no_match_returns_default(rule_matcher, windows):
    rule, flasher = rule_matcher.match(windows[1])
    assert rule == rule_matcher.rules[1]
    assert flasher == rule_matcher.flashers[1]
    assert flasher.flash_opacity != 0


def test_rule_matcher_returns_none_if_not_flash_on_focus(rule_matcher, window):
    assert rule_matcher.match(window, 'focus_shift') is None


def test_rule_matcher_direct_request_calls_matching_flasher(
        rule_matcher, flasher):
    flasher.flash_window = MagicMock()
    rule_matcher.match = lambda *args, **kwargs: (Rule(), flasher)
    rule_matcher.direct_request(0)
    flasher.flash_window.assert_called()
