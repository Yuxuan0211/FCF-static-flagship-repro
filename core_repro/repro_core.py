from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data_release"
RESULTS = ROOT / "results"
AUDIT = ROOT / "audit_archive"
EXPECTED = ROOT / "expected_outputs" / "expected_summary.json"

def qdist(a, b):
    return np.sqrt(np.mean((a - b) ** 2, axis=-1))

def load_expected():
    return json.loads(EXPECTED.read_text(encoding="ascii"))

def load_q():
    df = pd.read_csv(DATA / "Q_labels.csv")
    qcols = [c for c in df.columns if c.startswith("q_")]
    return df["node_id"].to_numpy(dtype=int), df[qcols].to_numpy(dtype=float)

def load_coords(name, prefix):
    df = pd.read_csv(DATA / name)
    cols = [c for c in df.columns if c.startswith(prefix)]
    return df["node_id"].to_numpy(dtype=int), df[cols].to_numpy(dtype=float)

def load_edges(universe):
    return pd.read_csv(DATA / f"{universe}_frozen_edges.csv")

def summarize_edges(df):
    total = len(df)
    original = int(df["original_obstruction"].sum())
    repaired = int(df["post_split_obstruction"].sum())
    retained = int(df["retained_after_split"].sum())
    worst_retained = float(df.loc[df["retained_after_split"], "d_Q"].max())
    return {
        "edge_count": total,
        "original_obstructions": original,
        "repaired_obstructions": repaired,
        "retained_after_split": retained,
        "worst_retained_dQ": worst_retained,
    }
