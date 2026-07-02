#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
from repro_core import ROOT, load_edges

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", choices=["universe_A", "universe_B"], required=True)
    args = parser.parse_args()
    df = load_edges(args.universe)
    out = ROOT / "recomputed" / f"obstruction_edges_{args.universe}.csv"
    out.parent.mkdir(exist_ok=True)
    df[df["original_obstruction"]].to_csv(out, index=False)
    print({"universe": args.universe, "obstructions": int(df["original_obstruction"].sum()), "out": str(out)})

if __name__ == "__main__":
    main()
