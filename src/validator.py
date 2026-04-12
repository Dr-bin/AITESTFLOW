# AITestFlow Skill: Validator

"""Validator module for running test validation"""

import gc
import json
import logging
import os
import re
import subprocess
import tempfile
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models import CoverageState, TestCase


logger = logging.getLogger(__name__)


class TestResult:
    """Test result container"""

    def __init__(self, passed: int, failed: int, failed_tests: List[Dict[str, Any]]):
        self.passed = passed
        self.failed = failed
        self.failed_tests = failed_tests
    
    def __repr__(self) -> str:
        return f"TestResult(passed={self.passed}, failed={self.failed})"


def run_mock_validation(
    endpoint: str,
    test_code: str,
    state: CoverageState,
    test_case_index: Optional[Dict[str, List[str]]] = None,
) -> CoverageState:
    """
    Run validation for generated test code.

    Args:
        endpoint: API endpoint path being tested
        test_code: Python test code to validate
        state: Current CoverageState
        test_case_index: Map test_id -> covered_condition_ids for accurate failure attribution

    Returns:
        Updated CoverageState with test results
    """
    temp_file = None
    temp_path = None
    
    try:
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", 
            suffix="_test.py", 
            delete=False, 
            encoding="utf-8"
        )
        
        wrapped_code = _wrap_test_code(test_code, endpoint)
        temp_file.write(wrapped_code)
        temp_file.flush()
        temp_path = temp_file.name
        
        logger.debug(f"Running pytest on temporary file: {temp_path}")

        result = _run_pytest(temp_path)
        
        logger.info(f"Test results: {result.passed} passed, {result.failed} failed")

        failed_condition_ids = _map_failures_to_conditions(
            result.failed_tests,
            state.covered_condition_ids,
            test_case_index=test_case_index or {},
        )

        all_covered = set(state.covered_condition_ids)
        
        for fc in failed_condition_ids:
            all_covered.discard(fc)

        new_failed = state.failed_test_cases + result.failed_tests

        coverage_rate = len(all_covered) / state.total_conditions if state.total_conditions > 0 else 0.0
        
        coverage_rate = min(1.0, coverage_rate)
        
        state.iteration += 1

        return CoverageState(
            total_conditions=state.total_conditions,
            covered_condition_ids=list(all_covered),
            failed_test_cases=new_failed,
            iteration=state.iteration,
            coverage_rate=coverage_rate,
        )

    except subprocess.TimeoutExpired:
        logger.error(f"Pytest execution timed out for endpoint {endpoint}")
        return CoverageState(
            total_conditions=state.total_conditions,
            covered_condition_ids=state.covered_condition_ids,
            failed_test_cases=state.failed_test_cases + [{"error": "Execution timeout"}],
            iteration=state.iteration,
            coverage_rate=state.coverage_rate,
        )
        
    except Exception as e:
        logger.error(f"Validation error for endpoint {endpoint}: {e}", exc_info=True)
        return state
        
    finally:
        if temp_file and temp_path:
            time.sleep(0.5)
            gc.collect()
            
            for attempt in range(3):
                try:
                    os.unlink(temp_path)
                    logger.debug(f"Cleaned up temporary file: {temp_path}")
                    break
                except OSError as e:
                    if attempt < 2:
                        time.sleep(1)
                        gc.collect()
                    else:
                        logger.warning(f"Failed to delete temp file after 3 attempts: {temp_path}")


def _strip_make_request_definitions(code: str) -> str:
    """Remove top-level make_request definitions so the validator stub takes effect."""
    lines = code.splitlines(keepends=True)
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("def make_request"):
            i += 1
            while i < len(lines):
                n = lines[i]
                if n.strip() == "":
                    i += 1
                    continue
                if not (n.startswith(" ") or n.startswith("\t")):
                    break
                i += 1
            continue
        out.append(line)
        i += 1
    return "".join(out)


def _wrap_test_code(test_code: str, endpoint: str) -> str:
    """Prepend a make_request stub that honors expected_status (no real HTTP)."""
    body = _strip_make_request_definitions(test_code)
    header = f'''"""AITestFlow mock validation (endpoint: {endpoint})"""
import pytest
from typing import Any, Dict, Optional
from unittest.mock import MagicMock


def make_request(
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    expected_status: int = 200,
) -> Any:
    m = MagicMock()
    m.status_code = int(expected_status)
    m.text = ""
    m.json.return_value = {{}}
    m.headers = {{"Content-Type": "application/json"}}
    return m


'''
    return header + body


def _run_pytest(test_path: str) -> TestResult:
    """Run pytest and capture results"""
    import sys
    import shutil
    
    pytest_cmd = shutil.which('pytest')
    if not pytest_cmd:
        pytest_cmd = sys.executable.replace('python.exe', 'Scripts\\pytest.exe')
        if not os.path.exists(pytest_cmd):
            pytest_cmd = 'pytest'
    
    logger.debug(f"Using pytest at: {pytest_cmd}")
    
    try:
        result = subprocess.run(
            [pytest_cmd, test_path, "--tb=short", "-v", "--no-header"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = result.stdout + "\n" + result.stderr
        logger.debug(f"Pytest output length: {len(output)} chars")
        
        return _parse_pytest_output(output)
        
    except subprocess.TimeoutExpired:
        logger.error("Pytest execution timed out")
        raise
    except FileNotFoundError:
        logger.error(f"pytest not found at {pytest_cmd}")
        return TestResult(passed=0, failed=0, failed_tests=[])
    except Exception as e:
        logger.error(f"Error running pytest: {e}")
        return TestResult(passed=0, failed=0, failed_tests=[])


def _parse_pytest_output(output: str) -> TestResult:
    """Parse pytest output to extract pass/fail statistics"""
    passed = 0
    failed = 0
    failed_tests: List[Dict[str, Any]] = []

    passed_match = re.search(r"(\d+)\s+passed", output)
    if passed_match:
        passed = int(passed_match.group(1))

    failed_match = re.search(r"(\d+)\s+failed", output)
    if failed_match:
        failed = int(failed_match.group(1))

    error_match = re.search(r"(\d+)\s+error", output)
    if error_match:
        failed += int(error_match.group(1))

    failed_test_pattern = re.compile(
        r"FAILED\s+([a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*)",
        re.MULTILINE
    )
    for match in failed_test_pattern.finditer(output):
        test_name = match.group(1).strip()
        
        skip_patterns = ['collecting', 'test session', '::::', 'Documents', 'Settings']
        if any(skip in test_name for skip in skip_patterns):
            logger.debug(f"Skipping pytest system message: {test_name}")
            continue
        
        failed_tests.append({
            "test_name": test_name,
            "error": "Test failed",
            "timestamp": datetime.now().isoformat()
        })
    
    error_test_pattern = re.compile(
        r"ERROR\s+([a-zA-Z_][a-zA-Z0-9_]*(?:::[a-zA-Z_][a-zA-Z0-9_]*)*)",
        re.MULTILINE
    )
    for match in error_test_pattern.finditer(output):
        test_name = match.group(1).strip()
        
        skip_patterns = ['collecting', 'test session', '::::', 'Documents', 'Settings']
        if any(skip in test_name for skip in skip_patterns):
            logger.debug(f"Skipping pytest system message: {test_name}")
            continue
        
        failed_tests.append({
            "test_name": test_name,
            "error": "Test error",
            "timestamp": datetime.now().isoformat()
        })

    logger.debug(f"Parsed results: {passed} passed, {failed} failed, {len(failed_tests)} failed test details")
    
    return TestResult(passed=passed, failed=failed, failed_tests=failed_tests)


def _map_failures_to_conditions(
    failed_tests: List[Dict[str, Any]],
    covered_ids: List[str],
    test_case_index: Optional[Dict[str, List[str]]] = None,
) -> List[str]:
    """Map failed tests to condition IDs using parametrize ids (test_id) when possible."""
    condition_ids: List[str] = []
    index = test_case_index or {}

    for ft in failed_tests:
        test_name = ft.get("test_name", "")
        logger.warning(f"Test failed: {test_name} - {ft.get('error', 'Unknown error')}")

        bracket = re.search(r"\[([^\]]+)\]", test_name)
        if bracket:
            tid = bracket.group(1).strip()
            if tid in index:
                condition_ids.extend(index[tid])
                logger.debug("Mapped failure %s to conditions via test_id %s", test_name, tid)
                continue

        for cond_id in covered_ids:
            if cond_id in test_name or test_name in cond_id:
                condition_ids.append(cond_id)
                logger.debug(f"Mapped failed test '{test_name}' to condition '{cond_id}'")
                break

    return list(dict.fromkeys(condition_ids))


def log_validation(
    endpoint: str, 
    iteration: int, 
    coverage_rate: float, 
    action: str
) -> str:
    """Generate validation log entry"""
    timestamp = datetime.now().isoformat()
    log_entry = (
        f"[{timestamp}] Endpoint={endpoint} Iter={iteration} "
        f"Coverage={coverage_rate:.2%} Action={action}\n"
    )
    return log_entry


def validate_syntax(code: str) -> tuple[bool, Optional[str]]:
    """
    Validate Python syntax of generated code.
    
    Args:
        code: Python code string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        compile(code, '<string>', 'exec')
        return True, None
    except SyntaxError as e:
        error_msg = f"Syntax error at line {e.lineno}: {e.msg}"
        logger.warning(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Code validation error: {e}"
        logger.warning(error_msg)
        return False, error_msg
