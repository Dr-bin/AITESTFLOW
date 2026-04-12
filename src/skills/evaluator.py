# AITestFlow Skill: Evaluator

"""Coverage evaluation module for test scenario analysis"""

from typing import List, Tuple

from src.models import TestCase


def evaluate_coverage(
    scenarios: List[TestCase], total_conditions: int
) -> Tuple[float, List[str]]:
    """
    Evaluate test coverage based on scenarios.

    Args:
        scenarios: List of TestCase objects
        total_conditions: Total number of conditions to cover

    Returns:
        Tuple of (coverage_rate float, covered_condition_ids list)

    Raises:
        ValueError: If total_conditions is non-positive
    """
    if total_conditions <= 0:
        raise ValueError("total_conditions must be positive")

    covered_ids: set[str] = set()

    for scenario in scenarios:
        covered_ids.update(scenario.covered_condition_ids)

    coverage_rate = len(covered_ids) / total_conditions

    return coverage_rate, list(covered_ids)
