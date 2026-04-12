"""Integration tests for AITestFlow"""

import pathlib

import pytest
import yaml

from src.coordinator import WorkflowCoordinator


def test_smoke_single_round():
    """Smoke test: load sample Petstore YAML, run coordinator, verify generated code"""
    input_path = pathlib.Path(__file__).parent.parent / "input" / "sample_petstore.yaml"
    assert input_path.exists(), f"Sample input file not found: {input_path}"

    spec = yaml.safe_load(input_path.read_text(encoding="utf-8"))
    assert spec is not None, "Failed to parse OpenAPI spec"
    assert "paths" in spec, "Invalid OpenAPI spec: missing paths"

    coordinator = WorkflowCoordinator(
        coverage_threshold=0.85,
        max_iter=1,
        output_dir="output",
    )

    test_code, coverage_state = coordinator.run_full_pipeline(spec)

    assert test_code is not None, "Generated test code is None"
    assert isinstance(test_code, str), "Generated test code is not a string"
    assert len(test_code) > 0, "Generated test code is empty"

    assert "def test_" in test_code, "Generated code does not contain test functions"
    assert "assert" in test_code, "Generated code does not contain assertions"

    assert coverage_state is not None, "Coverage state is None"
    assert coverage_state.coverage_rate >= 0.0, "Invalid coverage rate"
    assert coverage_state.iteration >= 0, "Invalid iteration count"
