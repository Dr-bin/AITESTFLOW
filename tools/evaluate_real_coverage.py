"""Run real API test execution against local mock server and compute coverage.

Usage:
    python tools/evaluate_real_coverage.py
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.mock_petstore_server import start_server


def _extract_scenario_blocks(test_file: Path) -> Dict[str, List[Dict[str, Any]]]:
    tree = ast.parse(test_file.read_text(encoding="utf-8"))
    blocks: Dict[str, List[Dict[str, Any]]] = {}

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        scenario_target = next(
            (
                t
                for t in targets
                if t == "test_scenarios" or t.startswith("test_scenarios_")
            ),
            None,
        )
        if not scenario_target:
            continue
        if not isinstance(node.value, ast.List):
            continue

        one_block: List[Dict[str, Any]] = []
        for elt in node.value.elts:
            if not isinstance(elt, ast.Dict):
                continue
            scenario: Dict[str, Any] = {}
            ok = True
            for k_node, v_node in zip(elt.keys, elt.values):
                if not isinstance(k_node, ast.Constant) or not isinstance(k_node.value, str):
                    ok = False
                    break
                key = k_node.value
                try:
                    scenario[key] = ast.literal_eval(v_node)
                except Exception:
                    ok = False
                    break
            if ok:
                one_block.append(scenario)
        if one_block:
            blocks[scenario_target] = one_block
    return blocks


def _extract_function_scenario_bindings(test_file: Path) -> Dict[str, str]:
    """Map pytest function name -> scenario list variable name."""
    tree = ast.parse(test_file.read_text(encoding="utf-8"))
    bindings: Dict[str, str] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            # match pytest.mark.parametrize(...)
            func = dec.func
            if not isinstance(func, ast.Attribute) or func.attr != "parametrize":
                continue
            if len(dec.args) < 2:
                continue
            scenario_arg = dec.args[1]
            if not isinstance(scenario_arg, ast.Name):
                continue
            sname = scenario_arg.id
            if sname == "test_scenarios" or sname.startswith("test_scenarios_"):
                bindings[node.name] = sname
    return bindings


def _extract_condition_ids(scenarios: List[Dict[str, Any]]) -> Set[str]:
    ids: Set[str] = set()
    for scenario in scenarios:
        cids = scenario.get("covered_condition_ids", [])
        if isinstance(cids, list):
            for cid in cids:
                if isinstance(cid, str) and cid:
                    ids.add(cid)
    return ids


def _collect_endpoint_templates(spec_data: Dict[str, Any]) -> List[Tuple[str, str]]:
    ops: List[Tuple[str, str]] = []
    paths = spec_data.get("paths", {})
    if not isinstance(paths, dict):
        return ops
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method in ("get", "post", "put", "delete", "patch", "head", "options"):
            if method in path_item:
                ops.append((method.upper(), str(path)))
    return ops


def _path_to_regex(template: str) -> re.Pattern[str]:
    escaped = re.escape(template)
    pattern = re.sub(r"\\\{[^/]+\\\}", r"[^/]+", escaped)
    return re.compile("^" + pattern + "$")


def _normalize_operation(
    method: str, endpoint: str, templates: List[Tuple[str, str]]
) -> Tuple[str, str] | None:
    method_u = method.upper()
    for m, t in templates:
        if m != method_u:
            continue
        if _path_to_regex(t).match(endpoint):
            return (m, t)
    return None


def _run_pytest(test_file: Path, cwd: Path) -> Tuple[int, str]:
    cmd = [sys.executable, "-m", "pytest", str(test_file), "-v", "--no-header", "-rA"]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    output = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return proc.returncode, output


def _parse_pytest_results(output: str) -> Tuple[Set[Tuple[str, str]], Set[Tuple[str, str]]]:
    passed: Set[Tuple[str, str]] = set()
    failed: Set[Tuple[str, str]] = set()
    line_re = re.compile(r"::([^\[\s:]+)\[([^\]]+)\]\s+(PASSED|FAILED|ERROR)")

    for line in output.splitlines():
        m = line_re.search(line)
        if not m:
            continue
        func_name, test_id, status = m.group(1), m.group(2), m.group(3)
        key = (func_name, test_id)
        if status == "PASSED":
            passed.add(key)
        else:
            failed.add(key)
    return passed, failed


def _load_yaml(path: Path) -> Dict[str, Any]:
    import yaml  # lazy import

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML content in {path}")
    return data


def evaluate(
    test_file: Path,
    spec_file: Path,
    report_file: Path,
) -> Dict[str, Any]:
    scenario_blocks = _extract_scenario_blocks(test_file)
    if not scenario_blocks:
        raise ValueError(f"No test_scenarios blocks found in {test_file}")

    fn_bindings = _extract_function_scenario_bindings(test_file)
    documented_scenarios: List[Dict[str, Any]] = []
    for block in scenario_blocks.values():
        documented_scenarios.extend(block)

    # In namespaced output all scenario blocks are executable; use union as active set.
    active_scenarios = documented_scenarios
    active_map: Dict[Tuple[str, str], List[str]] = {}
    for fn_name, scenario_var in fn_bindings.items():
        block = scenario_blocks.get(scenario_var, [])
        for s in block:
            tid = s.get("test_id")
            cids = s.get("covered_condition_ids", [])
            if isinstance(tid, str) and isinstance(cids, list):
                active_map[(fn_name, tid)] = [x for x in cids if isinstance(x, str)]

    documented_condition_ids = _extract_condition_ids(documented_scenarios)
    active_condition_ids = _extract_condition_ids(active_scenarios)

    spec_data = _load_yaml(spec_file)
    templates = _collect_endpoint_templates(spec_data)
    spec_ops = set(templates)

    documented_ops: Set[Tuple[str, str]] = set()
    for scenario in documented_scenarios:
        method = scenario.get("method")
        endpoint = scenario.get("endpoint")
        if not isinstance(method, str) or not isinstance(endpoint, str):
            continue
        op = _normalize_operation(method, endpoint, templates)
        if op:
            documented_ops.add(op)

    covered_spec_ops = sorted([f"{m} {p}" for m, p in documented_ops])
    missing_spec_ops = sorted([f"{m} {p}" for m, p in (spec_ops - documented_ops)])
    endpoint_coverage = len(documented_ops) / len(spec_ops) if spec_ops else 0.0

    server, _thread = start_server(host="127.0.0.1", port=8000)
    try:
        rc, pytest_output = _run_pytest(test_file, cwd=test_file.parent.parent)
    finally:
        server.shutdown()
        server.server_close()

    passed_keys, failed_keys = _parse_pytest_results(pytest_output)
    collection_error = rc == 2 and "ERROR collecting" in pytest_output

    validated_condition_ids: Set[str] = set()
    for key in passed_keys:
        validated_condition_ids.update(active_map.get(key, []))

    active_total = len(active_condition_ids)
    documented_total = len(documented_condition_ids)
    real_active_coverage = len(validated_condition_ids) / active_total if active_total else 0.0
    real_documented_coverage = (
        len(validated_condition_ids) / documented_total if documented_total else 0.0
    )

    report: Dict[str, Any] = {
        "test_file": str(test_file),
        "spec_file": str(spec_file),
        "note": (
            "real_active_coverage uses ONLY the last active test_scenarios block in test_api.py "
            "(Python redefinition semantics). real_documented_coverage uses all documented blocks."
        ),
        "pytest": {
            "return_code": rc,
            "collection_error": collection_error,
            "passed_test_ids": sorted([f"{k[0]}[{k[1]}]" for k in passed_keys]),
            "failed_test_ids": sorted([f"{k[0]}[{k[1]}]" for k in failed_keys]),
            "output_excerpt": pytest_output[-4000:],
        },
        "coverage": {
            "validated_condition_ids": sorted(validated_condition_ids),
            "active_condition_ids": sorted(active_condition_ids),
            "documented_condition_ids": sorted(documented_condition_ids),
            "real_active_coverage": round(real_active_coverage, 6),
            "real_documented_coverage": round(real_documented_coverage, 6),
            "active_condition_total": active_total,
            "documented_condition_total": documented_total,
            "validated_condition_total": len(validated_condition_ids),
        },
        "spec_endpoint_coverage": {
            "spec_operations_total": len(spec_ops),
            "covered_operations_total": len(documented_ops),
            "coverage_rate": round(endpoint_coverage, 6),
            "covered_operations": covered_spec_ops,
            "missing_operations": missing_spec_ops,
        },
    }

    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate real coverage via mock petstore API")
    parser.add_argument(
        "--test-file",
        default="output/test_api.py",
        help="Path to generated pytest module",
    )
    parser.add_argument(
        "--spec-file",
        default="input/sample_petstore.yaml",
        help="Path to OpenAPI spec YAML",
    )
    parser.add_argument(
        "--report-file",
        default="output/real_coverage_report.json",
        help="Path to output real coverage report JSON",
    )
    args = parser.parse_args()

    root = PROJECT_ROOT
    test_file = (root / args.test_file).resolve()
    spec_file = (root / args.spec_file).resolve()
    report_file = (root / args.report_file).resolve()

    report = evaluate(test_file=test_file, spec_file=spec_file, report_file=report_file)
    cov = report["coverage"]["real_active_coverage"]
    d_cov = report["coverage"]["real_documented_coverage"]
    ep_cov = report["spec_endpoint_coverage"]["coverage_rate"]
    print(f"Real active coverage: {cov:.2%}")
    print(f"Real documented coverage: {d_cov:.2%}")
    print(f"Spec endpoint coverage: {ep_cov:.2%}")
    print(f"Report written to: {report_file}")


if __name__ == "__main__":
    main()
