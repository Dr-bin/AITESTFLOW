# AITestFlow Skill: Code Generator

"""Code generation module using LLM for pytest test generation"""

import json
import re
from pathlib import Path
from typing import List, Union

from pydantic import BaseModel

from src.llm_client import LLMClient
from src.models import TestCase


class CodeResponse(BaseModel):
    """Wrapper model for code response"""

    python_code: str = ""


def _parse_code_response(data: Union[dict, str]) -> str:
    """Parse code from various response formats"""
    if isinstance(data, str):
        return data
    
    if isinstance(data, dict):
        if "python_code" in data:
            return data["python_code"]
        elif "code" in data:
            return data["code"]
        elif "test_code" in data:
            return data["test_code"]
    
    return ""


def _clean_code(code: str) -> str:
    """Clean generated code by removing markdown markers and extra formatting"""
    code = re.sub(r"^```python\s*", "", code, flags=re.MULTILINE)
    code = re.sub(r"^```\s*", "", code, flags=re.MULTILINE)
    code = re.sub(r"^```json\s*", "", code, flags=re.MULTILINE)
    
    lines = code.split('\n')
    cleaned_lines = []
    skip_empty_count = 0
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# Test scenarios placeholder') or stripped.startswith('# Include all scenarios'):
            continue
        if stripped == 'test_scenarios = [' and skip_empty_count == 0:
            skip_empty_count = 1
        cleaned_lines.append(line)
    
    code = '\n'.join(cleaned_lines)
    code = code.strip()
    
    return code


def render_test_code(scenarios: List[TestCase], base_url: str = "http://localhost:8000") -> str:
    """
    Render pytest test code from scenarios using LLM.

    Args:
        scenarios: List of TestCase objects
        base_url: Base URL for API endpoints

    Returns:
        Pure Python code string without markdown markers

    Raises:
        ValueError: If LLM returns empty or invalid response
    """
    if not scenarios:
        raise ValueError("Scenarios list cannot be empty")

    prompt_template = _load_prompt("gen_code")

    scenarios_data = [
        {
            "test_id": s.test_id,
            "endpoint": s.endpoint,
            "method": s.method,
            "payload": s.payload,
            "expected_status": s.expected_status,
            "covered_condition_ids": s.covered_condition_ids,
        }
        for s in scenarios
    ]

    prompt = prompt_template.replace("SCENARIOS_PLACEHOLDER", json.dumps(scenarios_data, indent=2))
    prompt = prompt.replace("BASE_URL_PLACEHOLDER", base_url)

    llm_client = LLMClient()
    raw_response = llm_client.call(prompt, dict)

    code = _parse_code_response(raw_response)

    if not code:
        raise ValueError("LLM returned empty code")

    code = _clean_code(code)

    return code


def _load_prompt(prompt_name: str) -> str:
    """Load prompt template from file"""
    prompt_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompt_dir / f"{prompt_name}.txt"
    return prompt_file.read_text(encoding="utf-8")
