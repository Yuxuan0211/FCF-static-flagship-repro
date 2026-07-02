#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core_repro"
EXPECTED = json.loads((ROOT / "expected_outputs" / "expected_summary.json").read_text(encoding="ascii"))

def run(name, *args):
    cmd = [sys.executable, str(CORE / name), *args]
    subprocess.run(cmd, check=True, cwd=str(CORE))

def main():
    run("run_audit.py")
    run("compute_obstruction_edges.py", "--universe", "universe_A")
    run("compute_obstruction_edges.py", "--universe", "universe_B")
    run("lawful_binary_split.py", "--universe", "universe_A")
    run("lawful_binary_split.py", "--universe", "universe_B")
    run("forced_answer_baselines.py")
    run("nuisance_split_controls.py")
    run("summarize_results.py")
    actual = json.loads((ROOT / "recomputed" / "summary.json").read_text(encoding="ascii"))
    checks = {key: actual.get(key) == value for key, value in EXPECTED.items()}
    result = {"pass": all(checks.values()), "checks": checks, "actual": actual, "expected": EXPECTED}
    (ROOT / "recomputed" / "PASS_FAIL.json").write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result, indent=2))
    if not result["pass"]:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
