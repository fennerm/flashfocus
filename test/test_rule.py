"""Testsuite for flashfocus.rule."""
from pytest import mark

from flashfocus.rule import *
from test.helpers import to_regex


@mark.parametrize('id_regex,class_regex,should_match', [
    (r'window1', None, True),
    (r'^win.*$', None, True),
    (None, r'Window1', True),
    (None, r'^Win.*$', True),
    (r'window1', r'Window1', True),
    (r'window2', r'Window1', False),
    (r'window1', r'Window2', False),
    (r'window2', r'Window2', False),
])
@mark.parametrize('default_rule', [True, False])
def test_rule_matching(id_regex, class_regex, should_match, default_rule):
    if default_rule:
        rule = DefaultRule(to_regex(id_regex), to_regex(class_regex))
        assert rule.match('window1', 'Window1')
    else:
        rule = Rule(to_regex(id_regex), to_regex(class_regex))
        assert rule.match('window1', 'Window1') == should_match


def test_rule_matcher_match(rule_matcher, window):
    rule, flasher = rule_matcher.match(window)
    assert rule == rule_matcher.rules[0]
    assert flasher == rule_matcher.flashers[0]
    assert flasher.flash_opacity == 0


def test_rule_matcher_no_match_returns_default(rule_matcher, windows):
    rule, flasher = rule_matcher.match(windows[1])
    assert rule == rule_matcher.rules[1]
    assert flasher == rule_matcher.flashers[1]
    assert isinstance(rule, DefaultRule)
    assert flasher.flash_opacity != 0


def test_rule_matcher_returns_none_if_not_flash_on_focus(rule_matcher, window):
    assert rule_matcher.match(window, 'focus_shift') is None
