"""Render EP / BVA / test-case tables to Markdown for submission-style reports."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from src.models import EPCondition, TestCase


def _fmt_values(values: List[Any]) -> str:
    parts: List[str] = []
    for v in values:
        if v is None:
            parts.append("null")
        elif isinstance(v, str):
            parts.append(json.dumps(v, ensure_ascii=False))
        else:
            parts.append(str(v))
    return ", ".join(parts)


def _scenario_line(tc: TestCase) -> str:
    bits: List[str] = [f"{tc.method.upper()} `{tc.endpoint}`"]
    if tc.query:
        bits.append(f"query `{json.dumps(tc.query, ensure_ascii=False)}`")
    if tc.payload:
        bits.append(f"body `{json.dumps(tc.payload, ensure_ascii=False)}`")
    return " — ".join(bits)


def _partition_outcome(c: EPCondition) -> str:
    pt = (c.partition_type or "").lower().strip()
    if pt == "valid":
        return "valid"
    if pt == "invalid":
        return "invalid"
    if pt == "boundary":
        return "boundary"
    return pt or "—"


def render_design_markdown(
    runs: List[Dict[str, Any]],
    title: str = "AITestFlow — Test Design Report",
) -> str:
    """
    runs: list of dicts with keys method, path, conditions (List[EPCondition]), test_cases (List[TestCase])
    """
    lines: List[str] = [
        f"# {title}",
        "",
        f"*Generated: {datetime.now().isoformat(timespec='seconds')}*",
        "",
    ]

    for block in runs:
        method = block["method"]
        path = block["path"]
        conditions: List[EPCondition] = block["conditions"]
        test_cases: List[TestCase] = block["test_cases"]

        lines.append(f"## {method} `{path}`")
        lines.append("")

        ep_rows = [c for c in conditions if (c.partition_type or "").lower().strip() != "boundary"]
        bva_rows = [c for c in conditions if (c.partition_type or "").lower().strip() == "boundary"]

        lines.append("### Equivalence partitioning")
        lines.append("")
        lines.append("| ID | Parameter | Description | Outcome |")
        lines.append("|----|-----------|-------------|---------|")
        for c in ep_rows:
            desc = (c.description or "").replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {c.id} | `{c.parameter}` | {desc} | {_partition_outcome(c)} |"
            )
        if not ep_rows:
            lines.append("| — | — | *(no non-boundary rows)* | — |")
        lines.append("")

        lines.append("### Boundary value analysis")
        lines.append("")
        lines.append("| ID | Parameter | Description | Values |")
        lines.append("|----|-----------|-------------|--------|")
        for c in bva_rows:
            desc = (c.description or "").replace("|", "\\|").replace("\n", " ")
            lines.append(
                f"| {c.id} | `{c.parameter}` | {desc} | {_fmt_values(c.values)} |"
            )
        if not bva_rows:
            lines.append("| — | — | *(no boundary rows)* | — |")
        lines.append("")

        lines.append("### Sample test cases")
        lines.append("")
        lines.append("| Test case | Scenario | Expected result |")
        lines.append("|-----------|----------|-----------------|")
        for tc in test_cases:
            scen = _scenario_line(tc).replace("|", "\\|")
            exp = f"HTTP {tc.expected_status}"
            if tc.covered_condition_ids:
                ids = ", ".join(tc.covered_condition_ids[:5])
                if len(tc.covered_condition_ids) > 5:
                    ids += ", …"
                exp += f" *(conditions: {ids})*"
            lines.append(f"| {tc.test_id} | {scen} | {exp} |")
        if not test_cases:
            lines.append("| — | — | — |")
        lines.append("")

    return "\n".join(lines)


def write_design_report(output_dir: Path, runs: List[Dict[str, Any]]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "design_report.md"
    path.write_text(render_design_markdown(runs), encoding="utf-8")
    return path
