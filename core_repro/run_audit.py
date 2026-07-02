#!/usr/bin/env python3
from __future__ import annotations

import json
from repro_core import ROOT, load_edges, summarize_edges

def main():
    result = {
        "universe_A": summarize_edges(load_edges("universe_A")),
        "universe_B": summarize_edges(load_edges("universe_B")),
    }
    out = ROOT / "recomputed" / "audit_summary.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
