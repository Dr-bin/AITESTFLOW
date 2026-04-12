# AITestFlow Skill: Condition Generator

"""Condition generation module using LLM for EP/BVA analysis"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

from pydantic import BaseModel, ValidationError

from src.llm_client import LLMClient
from src.models import EPCondition


logger = logging.getLogger(__name__)


class EPConditionList(BaseModel):
    """Wrapper model for list of EPCondition"""

    items: List[EPCondition] = []


def _normalize_value(v: Any) -> Any:
    """Normalize complex values to serializable types"""
    if v is None:
        return None
    if isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, list):
        return [_normalize_value(i) for i in v]
    if isinstance(v, dict):
        return {str(k): _normalize_value(val) for k, val in v.items()}
    return str(v)


def _parse_conditions_response(data: Union[dict, list]) -> List[EPCondition]:
    """Parse conditions from various response formats"""
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if "items" in data:
            items = data["items"]
        elif "conditions" in data and isinstance(data["conditions"], list):
            items = data["conditions"]
        elif "test_conditions" in data and isinstance(data["test_conditions"], list):
            items = data["test_conditions"]
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
                if 'values' in item and isinstance(item['values'], list):
                    normalized_values = []
                    for v in item['values']:
                        normalized_values.append(_normalize_value(v))

                    item['values'] = normalized_values
                
                if not item.get('values') or len(item.get('values', [])) == 0:
                    logger.warning(f"Skipping condition with empty values array: {item.get('id', 'unknown')}")
                    continue
                
                result.append(EPCondition.model_validate(item))
            except ValidationError as e:
                logger.warning(f"Failed to parse condition: {e}")
                continue
    return result


def _validate_condition(condition: EPCondition, endpoint_meta: dict) -> bool:
    """Validate that condition parameter exists in endpoint specification"""
    valid_params = set()
    
    for param in endpoint_meta.get("parameters", []):
        if isinstance(param, dict) and "name" in param:
            valid_params.add(param["name"])
    
    request_body = endpoint_meta.get("requestBody")
    if request_body and isinstance(request_body, dict):
        properties = request_body.get("properties", {})
        if isinstance(properties, dict):
            valid_params.update(properties.keys())
    
    path = endpoint_meta.get("path", "")
    import re
    path_param_matches = re.findall(r'\{(\w+)\}', path)
    valid_params.update(path_param_matches)
    
    param_name = condition.parameter
    
    if ',' in param_name:
        params = [p.strip() for p in param_name.split(',')]
        all_valid = all(p in valid_params for p in params)
        if not all_valid:
            invalid_params = [p for p in params if p not in valid_params]
            logger.warning(
                f"Condition {condition.id} references invalid compound parameter(s): {invalid_params}. "
                f"Valid parameters: {valid_params}"
            )
            return False
        logger.debug(f"Condition {condition.id} uses valid compound parameters: {params}")
        return True
    
    if param_name not in valid_params:
        logger.warning(
            f"Condition {condition.id} references unknown parameter: {param_name}. "
            f"Valid parameters: {valid_params}"
        )
        return False
    
    return True


def generate_conditions(endpoint_meta: dict, validate_params: bool = True) -> List[EPCondition]:
    """
    Generate test conditions for an endpoint using LLM.

    Args:
        endpoint_meta: Endpoint metadata dictionary containing method, path,
                       parameters, requestBody, constraints
        validate_params: Whether to validate that conditions match endpoint parameters

    Returns:
        List of EPCondition objects

    Raises:
        ValueError: If LLM returns empty or invalid response
    """
    if not endpoint_meta:
        raise ValueError("Endpoint metadata cannot be empty")

    prompt_template = _load_prompt("gen_conditions")
    prompt = prompt_template.replace("ENDPOINT_PLACEHOLDER", json.dumps(endpoint_meta, indent=2))

    llm_client = LLMClient()
    raw_response = llm_client.call(prompt, dict)

    conditions = _parse_conditions_response(raw_response)

    if not conditions:
        raise ValueError("LLM returned empty conditions list")

    valid_conditions = []
    for condition in conditions:
        if not condition.id:
            logger.warning("Condition missing ID, skipping")
            continue
        
        if not condition.parameter:
            logger.warning(f"Condition {condition.id} missing parameter, skipping")
            continue
        
        if not condition.values:
            logger.warning(f"Condition {condition.id} has no test values, skipping")
            continue
        
        if validate_params:
            if _validate_condition(condition, endpoint_meta):
                valid_conditions.append(condition)
            else:
                logger.info(f"Skipping invalid condition {condition.id}")
        else:
            valid_conditions.append(condition)

    if not valid_conditions:
        raise ValueError("No valid conditions after validation")

    logger.info(
        f"Generated {len(valid_conditions)} valid conditions for "
        f"{endpoint_meta.get('method', 'UNKNOWN')} {endpoint_meta.get('path', 'UNKNOWN')}"
    )
    
    return valid_conditions


def _load_prompt(prompt_name: str) -> str:
    """Load prompt template from file"""
    prompt_dir = Path(__file__).parent.parent / "prompts"
    prompt_file = prompt_dir / f"{prompt_name}.txt"
    return prompt_file.read_text(encoding="utf-8")
