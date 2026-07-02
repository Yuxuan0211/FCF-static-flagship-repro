#!/usr/bin/env python3
from __future__ import annotations

import argparse
from repro_core import load_edges, summarize_edges

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", choices=["universe_A", "universe_B"], required=True)
    args = parser.parse_args()
    print(summarize_edges(load_edges(args.universe)))

if __name__ == "__main__":
    main()
