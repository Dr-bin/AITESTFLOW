# AITestFlow Skill: Coordinator

"""Workflow Coordinator - the brain of AITestFlow with feedback engine"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.llm_client import LLMClient
from src.models import (
    CodeResponseModel,
    CoverageState,
    EPCondition,
    TestCase,
)
from src.skills import (
    api_parser,
    code_gen,
    condition_gen,
    scenario_gen,
)
from src.validator import run_mock_validation


logger = logging.getLogger(__name__)


class WorkflowCoordinator:
    """Main coordinator for test generation workflow with feedback loop"""

    def __init__(
        self,
        coverage_threshold: float = 0.85,
        max_iter: int = 3,
        output_dir: str = "output",
    ) -> None:
        """
        Initialize workflow coordinator.

        Args:
            coverage_threshold: Target coverage rate (0.0-1.0)
            max_iter: Maximum iterations per endpoint
            output_dir: Directory for output files
        """
        self._threshold = coverage_threshold
        self._max_iter = max_iter
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(exist_ok=True)
        
        self._llm = LLMClient()
        self._workflow_log: List[str] = []
        self._global_coverage: Optional[CoverageState] = None
        self._all_conditions: Dict[str, List[EPCondition]] = {}

    def run_full_pipeline(self, openapi_spec: dict) -> Tuple[str, CoverageState]:
        """
        Execute full test generation pipeline with feedback loop.

        Args:
            openapi_spec: OpenAPI specification dictionary

        Returns:
            Tuple of (final_test_code, final_coverage_state)
        """
        self._log("=" * 60)
        self._log("Starting full pipeline")
        
        endpoints = api_parser.parse_openapi(openapi_spec)
        self._log(f"Parsed {len(endpoints)} endpoints")

        all_test_code_parts: List[str] = []
        all_covered_ids: List[str] = []
        total_conditions = 0

        for idx, endpoint_meta in enumerate(endpoints, 1):
            self._log("-" * 40)
            self._log(f"[{idx}/{len(endpoints)}] Processing: {endpoint_meta['method']} {endpoint_meta['path']}")
            
            try:
                test_code, coverage, conditions = self._process_endpoint(endpoint_meta)
                
                self._all_conditions[endpoint_meta['path']] = conditions
                all_test_code_parts.append(test_code)
                
                condition_ids = [c.id for c in conditions]
                all_covered_ids.extend(condition_ids)
                total_conditions += len(conditions)
                
                self._log(f"✓ Endpoint processed successfully")
                
            except Exception as e:
                self._log(f"✗ ERROR processing endpoint: {e}")
                logger.error(f"Failed to process endpoint {endpoint_meta['path']}: {e}", exc_info=True)

        final_test_code = self._merge_test_code(all_test_code_parts)
        
        self._write_output(final_test_code, "test_api.py")
        
        valid_covered_ids = self._filter_valid_condition_ids(all_covered_ids)
        unique_covered_ids = list(set(valid_covered_ids))
        coverage_rate = len(unique_covered_ids) / total_conditions if total_conditions > 0 else 0.0
        
        self._global_coverage = CoverageState(
            total_conditions=total_conditions,
            covered_condition_ids=unique_covered_ids,
            failed_test_cases=[],
            iteration=self._max_iter,
            coverage_rate=min(1.0, coverage_rate),
        )

        self._write_coverage_report()
        self._write_workflow_log()

        self._log("=" * 60)
        self._log(f"Pipeline complete. Final coverage: {self._global_coverage.coverage_rate:.2%}")
        self._log(f"Total conditions: {total_conditions}, Covered: {len(unique_covered_ids)}")

        return final_test_code, self._global_coverage

    def _process_endpoint(
        self, endpoint_meta: dict
    ) -> Tuple[str, CoverageState, List[EPCondition]]:
        """Process a single endpoint with feedback loop"""
        
        conditions = condition_gen.generate_conditions(endpoint_meta)
        self._log(f"Generated {len(conditions)} conditions")

        test_cases = scenario_gen.compose_scenarios(
            conditions,
            endpoint=endpoint_meta.get("path", "/api"),
            method=endpoint_meta.get("method", "GET"),
        )
        self._log(f"Generated {len(test_cases)} test cases")

        initial_code = code_gen.render_test_code(test_cases)
        
        condition_ids = [c.id for c in conditions]
        
        state = CoverageState(
            total_conditions=len(conditions),
            covered_condition_ids=condition_ids,
            failed_test_cases=[],
            iteration=0,
            coverage_rate=1.0 if condition_ids else 0.0,
        )

        current_code = initial_code
        best_code = initial_code
        best_coverage = state.coverage_rate

        for iteration in range(1, self._max_iter + 1):
            self._log(f"--- Iteration {iteration}/{self._max_iter} ---")
            
            try:
                state = run_mock_validation(
                    endpoint_meta["path"],
                    current_code,
                    state,
                )
            except Exception as e:
                self._log(f"Validation error: {e}")
                logger.warning(f"Mock validation failed: {e}")
                state.iteration = iteration

            self._log(f"Coverage: {state.coverage_rate:.2%}")
            
            if state.coverage_rate > best_coverage:
                best_coverage = state.coverage_rate
                best_code = current_code

            uncovered = self._get_uncovered_conditions(conditions, state)
            failed = state.failed_test_cases

            self._log(f"Uncovered conditions: {len(uncovered)}")
            self._log(f"Failed tests: {len(failed)}")

            if uncovered or failed:
                gap_prompt = self._build_gap_prompt(uncovered, failed, conditions)
                current_code = self._generate_supplementary_code(
                    gap_prompt, current_code
                )
                self._log(f"Regenerating tests for gaps...")
            else:
                self._log("All conditions covered, continuing to next iteration to maximize coverage")
        
        if best_coverage > state.coverage_rate:
            state.coverage_rate = best_coverage
            current_code = best_code
            self._log(f"Restored best coverage: {best_coverage:.2%}")

        return current_code, state, conditions

    def _generate_supplementary_code(
        self, gap_prompt: str, existing_code: str
    ) -> str:
        """Generate supplementary test code for gaps"""
        prompt = (
            f"Existing test code:\n{existing_code}\n\n"
            f"{gap_prompt}\n\n"
            f"Return JSON with 'python_code' field containing the complete updated test code."
        )
        
        try:
            response = self._llm.call(prompt, CodeResponseModel)
            return response.python_code
        except Exception as e:
            self._log(f"Error generating supplementary code: {e}")
            logger.error(f"Failed to generate supplementary code: {e}")
            return existing_code

    def _build_gap_prompt(
        self,
        uncovered: List[str],
        failed: List[Dict[str, Any]],
        conditions: List[EPCondition],
    ) -> str:
        """Build prompt for gap filling"""
        uncovered_details = []
        for cond_id in uncovered:
            for cond in conditions:
                if cond.id == cond_id:
                    uncovered_details.append(f"- {cond_id}: {cond.description}")
                    break
        
        return (
            f"The following test conditions are not covered:\n"
            f"{chr(10).join(uncovered_details)}\n\n"
            f"Failed test cases: {json.dumps(failed, indent=2)}\n\n"
            f"Please generate additional test cases to cover these gaps. "
            f"Return the complete updated test code."
        )

    def _get_uncovered_conditions(
        self,
        conditions: List[EPCondition],
        state: CoverageState,
    ) -> List[str]:
        """Get list of uncovered condition IDs"""
        covered = set(state.covered_condition_ids)
        all_ids = {c.id for c in conditions}
        return list(all_ids - covered)

    def _merge_test_code(self, code_parts: List[str]) -> str:
        """Merge multiple test code parts into single cohesive file"""
        if not code_parts:
            return "# No tests generated\n"

        header = '''"""Auto-generated API Test Suite
Generated by AITestFlow - AI-Driven Black-Box Testing Platform
Timestamp: ''' + datetime.now().isoformat() + '''
"""

import pytest
import requests
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"


def make_request(
    method: str,
    endpoint: str,
    params: Optional[Dict] = None,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None
) -> requests.Response:
    """Helper function to make HTTP requests with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            return requests.get(url, params=params, headers=headers, timeout=10)
        elif method == "POST":
            return requests.post(url, json=data, params=params, headers=headers, timeout=10)
        elif method == "PUT":
            return requests.put(url, json=data, params=params, headers=headers, timeout=10)
        elif method == "DELETE":
            return requests.delete(url, params=params, headers=headers, timeout=10)
        elif method == "PATCH":
            return requests.patch(url, json=data, params=params, headers=headers, timeout=10)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Request failed: {str(e)}")


'''

        merged_functions = []
        seen_imports = set()
        seen_consts = set()
        
        for code in code_parts:
            code = self._clean_code_section(code)
            
            code = re.sub(r'^import pytest\s*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'^import requests\s*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'^from typing import.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'^BASE_URL\s*=.*$', '', code, flags=re.MULTILINE)
            code = re.sub(r'^def make_request.*?(?=\n(?:def |class |@pytest))', '', code, flags=re.DOTALL)
            
            code = code.strip()
            
            if code:
                merged_functions.append(code)

        final_code = header + "\n\n".join(merged_functions)
        
        final_code = re.sub(r'\n{3,}', '\n\n', final_code)
        
        return final_code.strip() + "\n"

    def _clean_code_section(self, code: str) -> str:
        """Clean a code section by removing duplicates and normalizing"""
        code = re.sub(r'^"""[\s\S]*?"""', '', code, count=1)
        code = re.sub(r"^'''[\s\S]*?'''", '', code, count=1)
        
        lines = code.split('\n')
        seen_lines = set()
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            if stripped and stripped not in seen_lines:
                seen_lines.add(stripped)
                cleaned_lines.append(line)
            elif not stripped:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def _write_output(self, content: str, filename: str) -> None:
        """Write content to output file"""
        output_path = self._output_dir / filename
        output_path.write_text(content, encoding="utf-8")
        self._log(f"Written: {output_path}")

    def _write_coverage_report(self) -> None:
        """Write coverage report JSON"""
        if not self._global_coverage:
            return

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_conditions": self._global_coverage.total_conditions,
            "covered_condition_ids": self._global_coverage.covered_condition_ids,
            "coverage_rate": self._global_coverage.coverage_rate,
            "failed_test_cases": self._global_coverage.failed_test_cases,
            "iteration": self._global_coverage.iteration,
            "endpoints_processed": len(self._all_conditions),
        }

        self._write_output(json.dumps(report, indent=2), "coverage_report.json")

    def _write_workflow_log(self) -> None:
        """Write workflow log file"""
        self._write_output("".join(self._workflow_log), "workflow_log.txt")

    def _filter_valid_condition_ids(self, condition_ids: List[str]) -> List[str]:
        """Filter out invalid condition IDs that contain error messages or invalid patterns"""
        invalid_patterns = [
            "FAILED_",
            "ERROR",
            "test session",
            "Documents and Settings",
            "collecting",
            "::_",
        ]
        
        valid_ids = []
        for cond_id in condition_ids:
            is_valid = True
            for pattern in invalid_patterns:
                if pattern in cond_id:
                    is_valid = False
                    logger.debug(f"Filtered out invalid condition ID: {cond_id}")
                    break
            
            if is_valid and cond_id:
                valid_ids.append(cond_id)
        
        return valid_ids

    def _log(self, message: str) -> None:
        """Add timestamped log entry"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        self._workflow_log.append(entry)
        print(entry.strip())


class Coordinator:
    """Legacy coordinator for backward compatibility"""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self._llm = llm_client or LLMClient()
        self._coverage_state: Optional[CoverageState] = None
        self._conditions: List[EPCondition] = []
        self._test_cases: List[TestCase] = []

    def _load_prompt(self, prompt_name: str) -> str:
        from pathlib import Path
        prompt_dir = Path(__file__).parent / "prompts"
        return (prompt_dir / f"{prompt_name}.txt").read_text(encoding="utf-8")

    def parse_api_spec(self, api_spec: str) -> List[Dict[str, Any]]:
        endpoints = api_parser.parse_openapi(api_spec)
        return endpoints

    def generate_conditions(
        self,
        parameter_name: str,
        parameter_type: str,
        constraints: str,
        description: str,
    ) -> List[EPCondition]:
        endpoint_meta = {
            "method": "GET",
            "path": "/api",
            "parameters": [
                {
                    "name": parameter_name,
                    "type": parameter_type,
                    "constraints": constraints,
                    "description": description,
                }
            ],
            "requestBody": None,
            "responses": {},
            "constraints": {},
        }
        return condition_gen.generate_conditions(endpoint_meta)

    def generate_scenarios(
        self,
        conditions: List[EPCondition],
        endpoint: str,
        method: str,
    ) -> List[TestCase]:
        return scenario_gen.compose_scenarios(conditions, endpoint=endpoint, method=method)

    def generate_code(
        self, scenarios: List[TestCase], base_url: str
    ) -> CodeResponseModel:
        code = code_gen.render_test_code(scenarios)
        return CodeResponseModel(python_code=code)

    def update_coverage(
        self,
        total_conditions: int,
        covered_ids: List[str],
        failed_tests: List[Dict[str, Any]],
        iteration: int,
    ) -> CoverageState:
        coverage_rate = len(covered_ids) / total_conditions if total_conditions > 0 else 0.0
        self._coverage_state = CoverageState(
            total_conditions=total_conditions,
            covered_condition_ids=covered_ids,
            failed_test_cases=failed_tests,
            iteration=iteration,
            coverage_rate=coverage_rate,
        )
        return self._coverage_state

    @property
    def coverage_state(self) -> Optional[CoverageState]:
        return self._coverage_state

    @property
    def conditions(self) -> List[EPCondition]:
        return self._conditions

    @property
    def test_cases(self) -> List[TestCase]:
        return self._test_cases
