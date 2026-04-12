# AITestFlow Skill: API Parser

"""API parser module for extracting endpoint metadata from OpenAPI specifications"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


def parse_openapi(spec: Union[dict, str]) -> List[dict]:
    """
    Parse OpenAPI specification and extract endpoint metadata.

    Args:
        spec: OpenAPI specification as dict or JSON/YAML string

    Returns:
        List of standardized endpoint dictionaries

    Raises:
        ValueError: If spec format is invalid
    """
    if isinstance(spec, str):
        try:
            spec = json.loads(spec)
        except json.JSONDecodeError:
            try:
                spec = yaml.safe_load(spec)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid specification format: {e}")

    if not isinstance(spec, dict):
        raise ValueError("Specification must be a dict or valid JSON/YAML string")

    paths = spec.get("paths", {})
    if not paths:
        raise ValueError("No paths found in specification")

    components = spec.get("components", {}).get("schemas", {})

    endpoints: List[Dict[str, Any]] = []

    for path, path_item in paths.items():
        for method in ["get", "post", "put", "delete", "patch", "options", "head"]:
            if method not in path_item:
                continue

            operation = path_item[method]
            parameters = _extract_parameters(operation, path_item)

            request_body = None
            if "requestBody" in operation:
                request_body = _extract_request_body(operation["requestBody"], components)

            responses = operation.get("responses", {})

            constraints = _extract_constraints(operation, parameters, request_body)

            endpoints.append({
                "method": method.upper(),
                "path": path,
                "parameters": parameters,
                "requestBody": request_body,
                "responses": responses,
                "constraints": constraints,
            })

    if not endpoints:
        raise ValueError("No endpoints found in specification")

    return endpoints


def _extract_parameters(operation: dict, path_item: dict) -> List[dict]:
    """Extract parameters from operation and path item"""
    params: List[dict] = []
    param_sources = [
        path_item.get("parameters", []),
        operation.get("parameters", []),
    ]

    for source in param_sources:
        for param in source:
            if isinstance(param, dict):
                params.append({
                    "name": param.get("name", ""),
                    "in": param.get("in", "query"),
                    "type": _infer_param_type(param),
                    "required": param.get("required", False),
                    "description": param.get("description", ""),
                    "constraints": _format_param_constraints(param),
                })

    return params


def _infer_param_type(param: dict) -> str:
    """Infer parameter type from OpenAPI schema"""
    schema = param.get("schema", {})
    if schema:
        param_type = schema.get("type", "string")
    else:
        param_type = param.get("type", "string")

    if param_type == "array":
        items = schema.get("items", {}) if schema else param.get("items", {})
        item_type = items.get("type", "string") if isinstance(items, dict) else "string"
        return f"array<{item_type}>"

    return param_type


def _format_param_constraints(param: dict) -> str:
    """Format parameter constraints as string"""
    constraints: List[str] = []
    schema = param.get("schema", {})

    if "minimum" in schema:
        constraints.append(f"min={schema['minimum']}")
    if "maximum" in schema:
        constraints.append(f"max={schema['maximum']}")
    if "minLength" in schema:
        constraints.append(f"minLength={schema['minLength']}")
    if "maxLength" in schema:
        constraints.append(f"maxLength={schema['maxLength']}")
    if "pattern" in schema:
        constraints.append(f"pattern={schema['pattern']}")
    if "enum" in schema:
        constraints.append(f"enum={schema['enum']}")

    return "; ".join(constraints)


def _extract_request_body(request_body: dict, components: dict = None) -> Optional[dict]:
    """Extract request body schema with properties"""
    content = request_body.get("content", {})
    if not content:
        return None

    first_content = next(iter(content.values()))
    schema = first_content.get("schema", {})
    
    if components and "$ref" in schema:
        ref_path = schema["$ref"]
        if ref_path.startswith("#/components/schemas/"):
            schema_name = ref_path.split("/")[-1]
            schema = components.get(schema_name, schema)
    
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])

    return {
        "required": request_body.get("required", False),
        "content_type": list(content.keys())[0],
        "schema": schema,
        "properties": properties,
        "required_fields": required_fields,
    }


def _extract_constraints(
    operation: dict,
    parameters: List[dict],
    request_body: Optional[dict],
) -> Dict[str, Any]:
    """Extract all constraints from operation"""
    constraints: Dict[str, Any] = {
        "parameters": {},
        "request_body": {},
    }

    for param in parameters:
        if param.get("constraints"):
            constraints["parameters"][param["name"]] = param["constraints"]

    if request_body and request_body.get("schema"):
        constraints["request_body"] = request_body["schema"]

    return constraints
