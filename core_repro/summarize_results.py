#!/usr/bin/env python3
from __future__ import annotations

import json
import pandas as pd
from repro_core import ROOT, load_edges, summarize_edges

def main():
    forced = pd.read_csv(ROOT / "results" / "forced_answer_system_outputs.csv")
    nuisance = pd.read_csv(ROOT / "results" / "nuisance_split_trials.csv")
    a = summarize_edges(load_edges("universe_A"))
    b = summarize_edges(load_edges("universe_B"))
    summary = {
        "universe_A_original_obstructions": f"{a['original_obstructions']}/{a['edge_count']}",
        "universe_A_repaired_obstructions": a["repaired_obstructions"],
        "universe_B_original_obstructions": f"{b['original_obstructions']}/{b['edge_count']}",
        "universe_B_repaired_obstructions": b["repaired_obstructions"],
        "forced_answer_failures": int((forced["pass_fail"] == "FAIL").sum()),
        "nuisance_split_trials": int(len(nuisance)),
        "nuisance_split_zero_successes": int(nuisance["zero_obstruction_success"].sum()),
    }
    out = ROOT / "recomputed" / "summary.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
