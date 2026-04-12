"""Run full AITestFlow pipeline once (for local comparison). Usage: python scripts/run_pipeline_once.py"""

from __future__ import annotations

import os
import pathlib
import sys

import yaml
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(ROOT / ".env")


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "未检测到 OPENAI_API_KEY。\n"
            "请在本机 PowerShell 中设置后重试，例如：\n"
            '  $env:OPENAI_API_KEY = "sk-..."\n'
            "或在项目根目录创建 .env，写入：OPENAI_API_KEY=sk-...\n"
            "（可选）LLM_BASE_URL、LLM_MODEL 与 README 一致。"
        )
        sys.exit(2)
    spec_path = ROOT / "input" / "sample_petstore.yaml"
    from src.coordinator import WorkflowCoordinator

    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    coordinator = WorkflowCoordinator(
        coverage_threshold=0.85,
        max_iter=2,
        output_dir=str(ROOT / "output"),
    )
    code, coverage = coordinator.run_full_pipeline(spec)
    out_dir = ROOT / "output"
    print("Done.")
    print(f"  coverage_rate: {coverage.coverage_rate:.4f}")
    print(f"  total_conditions: {coverage.total_conditions}")
    print(f"  covered ids: {len(coverage.covered_condition_ids)}")
    print(f"  generated lines: {len(code.splitlines())}")
    print(f"  written: {out_dir / 'test_api.py'}, {out_dir / 'coverage_report.json'}")


if __name__ == "__main__":
    main()
