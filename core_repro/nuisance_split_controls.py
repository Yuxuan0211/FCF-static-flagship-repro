#!/usr/bin/env python3
from __future__ import annotations

import json
import pandas as pd
from repro_core import ROOT, RESULTS

def main():
    df = pd.read_csv(RESULTS / "nuisance_split_trials.csv")
    out = {
        "trials": int(len(df)),
        "zero_successes": int(df["zero_obstruction_success"].sum()),
        "best_remaining_obstruction_count": int(df["remaining_obstruction_count"].min()),
        "median_remaining_obstruction_count": float(df["remaining_obstruction_count"].median()),
    }
    target = ROOT / "recomputed" / "nuisance_split_summary.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, indent=2) + "\n", encoding="ascii")
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
