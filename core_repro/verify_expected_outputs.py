#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    expected = json.loads((ROOT / "expected_outputs" / "expected_summary.json").read_text(encoding="ascii"))
    if not (ROOT / "recomputed" / "summary.json").exists():
        subprocess.run([sys.executable, str(ROOT / "core_repro" / "reproduce_all.py")], check=True, cwd=str(ROOT))
    actual = json.loads((ROOT / "recomputed" / "summary.json").read_text(encoding="ascii"))
    checks = {key: actual.get(key) == value for key, value in expected.items()}
    payload = {
        "pass": all(checks.values()),
        "checks": checks,
        "actual": actual,
        "expected": expected,
    }
    out = ROOT / "recomputed" / "verify_expected_outputs.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))
    if not payload["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
