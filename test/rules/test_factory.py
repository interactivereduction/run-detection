"""
Rule factory unit tests
"""
# pylint: disable=protected-access
import unittest
from typing import Type, Any
from unittest.mock import patch

import pytest

from rundetection.rules.common_rules import EnabledRule
from rundetection.rules.factory import rule_factory
from rundetection.rules.inter_rules import InterStitchRule
from rundetection.rules.mari_rules import MariStitchRule, MariMaskFileRule, MariWBVANRule
from rundetection.rules.osiris_rules import (
    OsirisStitchRule,
    OsirisPanadiumRule,
    OsirisReductionModeRule,
    OsirisAnalyserRule,
)
from rundetection.rules.rule import MissingRuleError, Rule
from rundetection.rules.tosca_rules import ToscaStitchRule


def assert_correct_rule(name: str, value: Any, rule_type: Type[Rule]):
    """
    Assert when given name and value is passed to factory, the given Rule Type is returned
    :param name: the rule name
    :param value: the rule value
    :param rule_type: the rule type
    :return: None
    """
    rule = rule_factory(name, value)
    assert isinstance(rule, rule_type)
    assert rule._value is value


@pytest.mark.parametrize(
    "rule_key,rule_value,expected_rule",
    [
        ("enabled", True, EnabledRule),
        ("interstitch", True, InterStitchRule),
        ("toscastitch", True, ToscaStitchRule),
        ("maristitch", True, MariStitchRule),
        ("marimaskfile", "foo", MariMaskFileRule),
        ("mariwbvan", 12345, MariWBVANRule),
        ("osirisstitch", True, OsirisStitchRule),
        ("osirispanadium", 12345, OsirisPanadiumRule),
        ("osirisreductionmode", True, OsirisReductionModeRule),
        ("osirisanalyser", True, OsirisAnalyserRule),
    ],
)
@patch("rundetection.rules.mari_rules.MariStitchRule._load_mari_spec")
def test_rule_factory_returns_correct_rule(_, rule_key, rule_value, expected_rule):
    """
    Test that the rule factory will return the correct rule
    :param rule_key: The key to identify the rule
    :param rule_value: The value associated with the rule
    :param expected_rule: The expected rule class
    :return: None
    """
    assert_correct_rule(rule_key, rule_value, expected_rule)


def test_raises_exception_for_missing_rule_class() -> None:
    """
    Test exception raised when non-existent rule name is given
    :return: None
    """
    with pytest.raises(MissingRuleError):
        rule_factory("foo", "bar")


def test_raises_exception_for_incorrect_rule_value_type() -> None:
    """
    Test exception raised when incorrect value type
    :return: None
    """
    with pytest.raises(ValueError):
        rule_factory("enabled", "string")
    with pytest.raises(ValueError):
        rule_factory("enabled", 1)
    with pytest.raises(ValueError):
        rule_factory("maristitch", 4)
    with pytest.raises(ValueError):
        rule_factory("marimaskfile", 5)
    with pytest.raises(ValueError):
        rule_factory("mariwbvan", 3.3)


if __name__ == "__main__":
    unittest.main()
