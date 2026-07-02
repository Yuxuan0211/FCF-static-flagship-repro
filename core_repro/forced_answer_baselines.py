#!/usr/bin/env python3
from __future__ import annotations

import json
import pandas as pd
from repro_core import ROOT, RESULTS

def main():
    df = pd.read_csv(RESULTS / "forced_answer_system_outputs.csv")
    out = {
        "systems": int(len(df)),
        "failures": int((df["pass_fail"] == "FAIL").sum()),
        "passes": int((df["pass_fail"] == "PASS").sum()),
    }
    target = ROOT / "recomputed" / "forced_answer_fail_summary.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, indent=2) + "\n", encoding="ascii")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
