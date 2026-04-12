# AITestFlow Skill: Scenario Generator

"""Scenario generation module using LLM for test case composition"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
            if "query" not in item:
                item["query"] = item.get("params") or {}
            if "payload" not in item:
                item["payload"] = {}
            try:
                result.append(TestCase.model_validate(item))
            except ValidationError as e:
                logger.warning(f"Failed to parse test case: {e}")
                continue
    return result


def _validate_test_case(tc: TestCase, expected_endpoint: str, expected_method: str) -> bool:
    """Validate that test case matches expected endpoint and method"""
    actual_endpoint = tc.endpoint

    if actual_endpoint == expected_endpoint:
        if tc.method.upper() != expected_method.upper():
            logger.warning(
                f"Test case {tc.test_id} has wrong method: "
                f"expected {expected_method}, got {tc.method}"
            )
            return False
        return True

    pattern = re.sub(r"\{[^}]+\}", r"[^/]+", expected_endpoint)
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


def _normalize_testcase(tc: TestCase, method: str) -> TestCase:
    """Move misplaced GET/HEAD/DELETE fields from payload into query."""
    m = (method or "GET").upper()
    q = dict(tc.query or {})
    p = dict(tc.payload or {})
    if m in ("GET", "HEAD", "DELETE"):
        if p and not q:
            q, p = p, {}
    return TestCase(
        test_id=tc.test_id,
        endpoint=tc.endpoint,
        method=tc.method,
        query=q,
        payload=p,
        expected_status=tc.expected_status,
        covered_condition_ids=tc.covered_condition_ids,
    )


def _param_location(endpoint_meta: dict, param_name: str) -> str:
    """Return path|query|header|body|unknown for a parameter name."""
    path = endpoint_meta.get("path", "")
    if re.search(r"\{" + re.escape(param_name) + r"\}", path):
        return "path"

    for p in endpoint_meta.get("parameters", []):
        if not isinstance(p, dict):
            continue
        if p.get("name") != param_name:
            continue
        loc = (p.get("in") or "query").lower()
        if loc == "path":
            return "path"
        if loc == "header":
            return "header"
        if loc == "cookie":
            return "cookie"
        return "query"
    rb = endpoint_meta.get("requestBody") or {}
    props = rb.get("properties") or {}
    if param_name in props:
        return "body"
    method = (endpoint_meta.get("method") or "GET").upper()
    return "query" if method in ("GET", "HEAD", "DELETE") else "body"


def _fill_path_placeholders(path: str, primary: str, value: Any) -> str:
    p = path.replace(f"{{{primary}}}", str(value))
    p = re.sub(r"\{(\w+)\}", "1", p)
    return p


def _infer_expected_status(c: EPCondition) -> int:
    pt = (c.partition_type or "").lower()
    if "invalid" in pt:
        return 400
    return 200


def _synthetic_testcase_for_condition(
    c: EPCondition,
    endpoint: str,
    method: str,
    endpoint_meta: dict,
) -> Optional[TestCase]:
    """Build a minimal test case for one condition when the LLM omitted coverage."""
    if not c.id or not c.parameter:
        return None
    if "," in c.parameter:
        logger.debug(f"Skip auto case for compound parameter condition {c.id}")
        return None
    if not c.values:
        return None

    loc = _param_location(endpoint_meta, c.parameter)
    if loc in ("header", "cookie", "unknown"):
        logger.debug(f"Skip auto case for header/cookie/unknown location: {c.parameter}")
        return None

    val = c.values[0]
    m = method.upper()
    query: Dict[str, Any] = {}
    payload: Dict[str, Any] = {}
    ep = endpoint

    if loc == "path":
        ep = _fill_path_placeholders(endpoint, c.parameter, val)
    elif loc == "query":
        query[c.parameter] = val
    else:
        payload[c.parameter] = val

    return TestCase(
        test_id=f"TC_GAP_{c.id}",
        endpoint=ep,
        method=m,
        query=query,
        payload=payload,
        expected_status=_infer_expected_status(c),
        covered_condition_ids=[c.id],
    )


def ensure_all_conditions_covered(
    conditions: List[EPCondition],
    test_cases: List[TestCase],
    endpoint: str,
    method: str,
    endpoint_meta: Optional[dict] = None,
) -> List[TestCase]:
    """Append deterministic tests for any condition id not referenced in covered_condition_ids."""
    meta = endpoint_meta or {"path": endpoint, "method": method, "parameters": [], "requestBody": None}
    covered: set[str] = set()
    for tc in test_cases:
        covered.update(tc.covered_condition_ids)
    missing = [c for c in conditions if c.id and c.id not in covered]
    if not missing:
        return test_cases

    out = list(test_cases)
    for c in missing:
        try:
            auto = _synthetic_testcase_for_condition(c, endpoint, method, meta)
            if auto:
                out.append(auto)
                logger.info("Gap-fill test %s for condition %s", auto.test_id, c.id)
        except Exception as e:
            logger.warning("Could not auto-fill condition %s: %s", c.id, e)
    return out


def compose_scenarios(
    conditions: List[EPCondition],
    endpoint: str = "/api",
    method: str = "GET",
    validate_endpoint: bool = True,
    endpoint_meta: Optional[dict] = None,
) -> List[TestCase]:
    """
    Compose test scenarios from conditions using LLM.

    Args:
        conditions: List of EPCondition objects
        endpoint: API endpoint path
        method: HTTP method
        validate_endpoint: Whether to validate endpoint matching
        endpoint_meta: Full endpoint dict from api_parser (for gap-filling and normalization)

    Returns:
        List of TestCase objects with covered_condition_ids mapping
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

    valid_test_cases: List[TestCase] = []
    for tc in test_cases:
        if not tc.test_id:
            logger.warning("Test case missing test_id, skipping")
            continue

        if not tc.endpoint:
            logger.warning(f"Test case {tc.test_id} missing endpoint, skipping")
            continue

        if validate_endpoint:
            if _validate_test_case(tc, endpoint, method):
                valid_test_cases.append(_normalize_testcase(tc, method))
            else:
                corrected_tc = TestCase(
                    test_id=tc.test_id,
                    endpoint=endpoint,
                    method=method.upper(),
                    query=tc.query,
                    payload=tc.payload,
                    expected_status=tc.expected_status,
                    covered_condition_ids=tc.covered_condition_ids,
                )
                valid_test_cases.append(_normalize_testcase(corrected_tc, method))
                logger.info(f"Auto-corrected endpoint for test case {tc.test_id}")
        else:
            valid_test_cases.append(_normalize_testcase(tc, method))

    if not valid_test_cases:
        raise ValueError("No valid test cases after validation")

    meta = endpoint_meta
    if meta is None:
        meta = {"path": endpoint, "method": method, "parameters": [], "requestBody": None}

    valid_test_cases = ensure_all_conditions_covered(
        conditions, valid_test_cases, endpoint, method, meta
    )

    logger.info(f"Generated {len(valid_test_cases)} test cases for {method} {endpoint}")

    return valid_test_cases


def _load_prompt(prompt_name: str) -> str:
    """Load prompt template from file"""
    prompt_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompt_dir / f"{prompt_name}.txt"
    return prompt_file.read_text(encoding="utf-8")
