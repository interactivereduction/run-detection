"""
Module containing the factory function for each rule
"""
from rundetection.rules.common_rules import EnabledRule, SpecificNameRule
from rundetection.rules.inter_rules import InterStitchRule
from rundetection.rules.rule import T_co, Rule, MissingRuleError


def rule_factory(key_: str, value: T_co) -> Rule[T_co]:
    """
    Given the rule key, and rule value, return the rule implementation
    :param key_: The key of the rule
    :param value: The value of the rule
    :return: The Rule implementation
    """
    match key_.lower():
        case "enabled":
            if isinstance(value, bool):
                return EnabledRule(value)

            raise ValueError(f"Bad value: {value} in rule: {key_}")
        case "interstitch":
            if isinstance(value, bool):
                return InterStitchRule(value)
            raise ValueError(f"Bad value: {value} in rule {key_}")
        case "specificname":
            if isinstance(value, str):
                return SpecificNameRule(value)
            raise ValueError(f"Bad value: {value} un rule {key_}")
        case _:
            raise MissingRuleError(f"Implementation of Rule: {key_} does not exist.")