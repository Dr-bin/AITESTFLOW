# AITestFlow Skill: Scenario Generator

"""Scenario generation module using LLM for test case composition"""

import json
import logging
import re
from pathlib import Path
from typing import List, Union

from pydantic import BaseModel, ValidationError

from src.llm_client import LLMClient
from src.models import EPCondition, TestCase


logger = logging.getLogger(__name__)


class TestCaseList(BaseModel):
    """Wrapper model for list of TestCase"""

    items: List[TestCase] = []


def _parse_testcases_response(data: Union[dict, list]) -> List[TestCase]:
    """Parse test cases from various response formats"""
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if "items" in data:
            items = data["items"]
        elif "test_cases" in data and isinstance(data["test_cases"], list):
            items = data["test_cases"]
        elif "scenarios" in data and isinstance(data["scenarios"], list):
            items = data["scenarios"]
        else:
            items = []
    else:
        items = []

    if not items:
        return []

    result = []
    for item in items:
        if isinstance(item, dict):
            try:
                result.append(TestCase.model_validate(item))
            except ValidationError as e:
                logger.warning(f"Failed to parse test case: {e}")
                continue
    return result


def _validate_test_case(tc: TestCase, expected_endpoint: str, expected_method: str) -> bool:
    """Validate that test case matches expected endpoint and method
    
    Supports path parameter substitution (e.g., /pets/{petId} -> /pets/5)
    """
    actual_endpoint = tc.endpoint
    
    if actual_endpoint == expected_endpoint:
        if tc.method.upper() != expected_method.upper():
            logger.warning(
                f"Test case {tc.test_id} has wrong method: "
                f"expected {expected_method}, got {tc.method}"
            )
            return False
        return True
    
    pattern = re.sub(r'\{[^}]+\}', r'[^/]+', expected_endpoint)
    pattern = f"^{pattern}$"
    
    if re.match(pattern, actual_endpoint):
        logger.debug(
            f"Test case {tc.test_id} has path parameter substitution: "
            f"{expected_endpoint} -> {actual_endpoint}"
        )
        if tc.method.upper() != expected_method.upper():
            logger.warning(
                f"Test case {tc.test_id} has wrong method: "
                f"expected {expected_method}, got {tc.method}"
            )
            return False
        return True
    
    logger.warning(
        f"Test case {tc.test_id} has wrong endpoint: "
        f"expected {expected_endpoint}, got {actual_endpoint}"
    )
    return False


def compose_scenarios(
    conditions: List[EPCondition], 
    endpoint: str = "/api", 
    method: str = "GET",
    validate_endpoint: bool = True
) -> List[TestCase]:
    """
    Compose test scenarios from conditions using LLM.

    Args:
        conditions: List of EPCondition objects
        endpoint: API endpoint path
        method: HTTP method
        validate_endpoint: Whether to validate endpoint matching

    Returns:
        List of TestCase objects with covered_condition_ids mapping

    Raises:
        ValueError: If LLM returns empty or invalid response
    """
    if not conditions:
        raise ValueError("Conditions list cannot be empty")

    prompt_template = _load_prompt("gen_scenarios")
    
    conditions_data = [
        {
            "id": c.id,
            "parameter": c.parameter,
            "partition_type": c.partition_type,
            "description": c.description,
            "values": c.values,
        }
        for c in conditions
    ]

    prompt = prompt_template.replace("CONDITIONS_PLACEHOLDER", json.dumps(conditions_data, indent=2))
    prompt = prompt.replace("ENDPOINT_PLACEHOLDER", endpoint)
    prompt = prompt.replace("METHOD_PLACEHOLDER", method.upper())

    llm_client = LLMClient()
    raw_response = llm_client.call(prompt, dict)

    test_cases = _parse_testcases_response(raw_response)

    if not test_cases:
        raise ValueError("LLM returned empty test cases list")

    valid_test_cases = []
    for tc in test_cases:
        if not tc.test_id:
            logger.warning("Test case missing test_id, skipping")
            continue
        
        if not tc.endpoint:
            logger.warning(f"Test case {tc.test_id} missing endpoint, skipping")
            continue
        
        if validate_endpoint:
            if _validate_test_case(tc, endpoint, method):
                valid_test_cases.append(tc)
            else:
                corrected_tc = TestCase(
                    test_id=tc.test_id,
                    endpoint=endpoint,
                    method=method.upper(),
                    payload=tc.payload,
                    expected_status=tc.expected_status,
                    covered_condition_ids=tc.covered_condition_ids,
                )
                valid_test_cases.append(corrected_tc)
                logger.info(f"Auto-corrected endpoint for test case {tc.test_id}")
        else:
            valid_test_cases.append(tc)

    if not valid_test_cases:
        raise ValueError("No valid test cases after validation")

    logger.info(f"Generated {len(valid_test_cases)} valid test cases for {method} {endpoint}")
    
    return valid_test_cases


def _load_prompt(prompt_name: str) -> str:
    """Load prompt template from file"""
    prompt_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompt_dir / f"{prompt_name}.txt"
    return prompt_file.read_text(encoding="utf-8")
