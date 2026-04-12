"""Data models for AITestFlow using Pydantic v2"""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class EPCondition(BaseModel):
    """Equivalence Partitioning Condition model"""

    id: str = Field(..., description="Unique identifier for the condition")
    parameter: str = Field(..., description="Parameter name")
    partition_type: str = Field(..., description="Partition type: valid/invalid/boundary")
    description: str = Field(..., description="Description of the condition")
    values: List[Any] = Field(
        ..., description="List of test values for this condition (str, int, float, list, dict, bool, None)"
    )


class TestCase(BaseModel):
    """Test case model"""

    test_id: str = Field(..., description="Unique test case identifier")
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method")
    payload: Dict[str, Any] = Field(..., description="Request payload")
    expected_status: int = Field(..., description="Expected HTTP status code")
    covered_condition_ids: List[str] = Field(
        ..., description="List of condition IDs covered by this test"
    )


class CoverageState(BaseModel):
    """Coverage state tracking model"""

    total_conditions: int = Field(..., description="Total number of conditions")
    covered_condition_ids: List[str] = Field(
        ..., description="List of covered condition IDs"
    )
    failed_test_cases: List[Dict[str, Any]] = Field(
        ..., description="List of failed test cases with details"
    )
    iteration: int = Field(..., description="Current iteration number")
    coverage_rate: float = Field(..., description="Coverage rate (0.0 to 1.0)")


class CodeResponseModel(BaseModel):
    """Response model for generated Python code"""

    python_code: str = Field(..., description="Generated Python test code")
