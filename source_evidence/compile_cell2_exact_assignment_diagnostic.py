#!/usr/bin/env python3
"""Exact assignment diagnostic for the cell-2 obstruction.

This is a matrix-only audit. It does not run DNS and does not change C, Q,
tau, endpoints, the normalizer, or any validation graph. It separates two
questions:

1. Is there a single action that closes every same-cell pair in cell 2?
2. If each pair were allowed to choose its own action, are local closers present?

Question 2 is an oracle diagnostic only; pair-specific action assignment is not
a valid finite-contact policy when all those pairs live in the same frozen
contact cell.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np


ROOT = Path("/workspace/kolmogorov_creation")
OUTPUT = ROOT / "cell2_exact_assignment_diagnostic"
MATRIX = ROOT / "pair59_spatial_full_271_replay" / "EXTENDED_WITH_PAIR59_SPATIAL_MATRIX.npz"
QUANTIZER = ROOT / "delayed_action_closure_matrix" / "FROZEN_E0_QUANTIZER.npz"
TARGET_CELL = 2


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    matrix = np.load(MATRIX, allow_pickle=True)
    quantizer = np.load(QUANTIZER)
    action_ids = matrix["action_ids"].astype(str)
    distances = matrix["distances"]
    metadata = matrix["pair_metadata"]
    tau = float(matrix["tau"])
    labels = quantizer["development_labels"]
    left = metadata[:, 0].astype(int)
    right = metadata[:, 1].astype(int)
    same_cell = np.flatnonzero(
        (labels[left] == TARGET_CELL) & (labels[right] == TARGET_CELL)
    )
    cell_distances = distances[same_cell]

    max_by_action = cell_distances.max(axis=0)
    closed_by_action = (cell_distances <= tau).sum(axis=0)
    best_action_index = int(np.argmin(max_by_action))
    single_pass_indices = np.flatnonzero(max_by_action <= tau)

    best_action_by_pair = np.argmin(cell_distances, axis=1)
    best_dq_by_pair = cell_distances[np.arange(len(same_cell)), best_action_by_pair]
    pair_oracle_pass = bool(np.all(best_dq_by_pair <= tau))
    hard_order = np.argsort(-best_dq_by_pair)

    pair_rows = []
    for local_rank, local_idx in enumerate(hard_order.tolist()):
        pair_index = int(same_cell[local_idx])
        action_index = int(best_action_by_pair[local_idx])
        pair_rows.append(
            {
                "hard_rank": local_rank + 1,
                "pair_index": pair_index,
                "endpoint_i": int(metadata[pair_index, 0]),
                "endpoint_j": int(metadata[pair_index, 1]),
                "best_action": str(action_ids[action_index]),
                "best_dQ": float(best_dq_by_pair[local_idx]),
                "best_margin_to_tau": float(best_dq_by_pair[local_idx] - tau),
                "oracle_closed": bool(best_dq_by_pair[local_idx] <= tau),
            }
        )

    action_rows = []
    for idx in np.argsort(max_by_action).tolist():
        action_rows.append(
            {
                "action": str(action_ids[idx]),
                "max_dQ": float(max_by_action[idx]),
                "margin_to_tau": float(max_by_action[idx] - tau),
                "closed_pairs": int(closed_by_action[idx]),
                "pair_count": int(len(same_cell)),
                "single_action_pass": bool(max_by_action[idx] <= tau),
            }
        )

    summary = {
        "status": (
            "CELL2_PAIR_ORACLE_PASS_BUT_SINGLE_CONTACT_ACTION_UNSAT"
            if pair_oracle_pass and len(single_pass_indices) == 0
            else "CELL2_EXACT_ASSIGNMENT_DIAGNOSTIC_OTHER"
        ),
        "matrix_sha256": digest(MATRIX),
        "quantizer_sha256": digest(QUANTIZER),
        "target_cell": TARGET_CELL,
        "tau": tau,
        "pair_count": int(len(same_cell)),
        "action_count": int(len(action_ids)),
        "single_contact_action": {
            "feasible": bool(len(single_pass_indices) > 0),
            "passing_actions": [str(action_ids[idx]) for idx in single_pass_indices.tolist()],
            "best_action": str(action_ids[best_action_index]),
            "best_max_dQ": float(max_by_action[best_action_index]),
            "best_margin_to_tau": float(max_by_action[best_action_index] - tau),
            "best_closed_pairs": int(closed_by_action[best_action_index]),
        },
        "pair_specific_oracle": {
            "feasible": pair_oracle_pass,
            "closed_pairs": int(np.sum(best_dq_by_pair <= tau)),
            "pair_count": int(len(same_cell)),
            "max_best_pair_dQ": float(np.max(best_dq_by_pair)),
            "max_best_pair_margin_to_tau": float(np.max(best_dq_by_pair) - tau),
            "legal_as_finite_contact_policy": False,
            "reason": (
                "All audited pairs are in the same frozen contact cell, so a "
                "finite-contact policy must assign one action to the cell, not "
                "one action per hidden pair."
            ),
        },
        "hardest_pair_oracle_rows": pair_rows[:12],
        "actions_by_single_cell_max": action_rows,
        "interpretation": (
            "The extended action matrix contains local actions that close every "
            "cell-2 pair individually, but the library has no single action that "
            "closes the entire frozen contact cell. A strict win therefore needs "
            "either a new action whose response approximates the pair-oracle "
            "assignment at the cell level, or a protocol upgrade allowing lawful "
            "online finite-contact feedback that splits the cell after observing "
            "post-action contact. Pair-specific assignment itself is not a "
            "valid certificate."
        ),
    }

    summary_path = OUTPUT / "CELL2_EXACT_ASSIGNMENT_DIAGNOSTIC_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")
    (OUTPUT / "RESULT_SHA256.txt").write_text(
        f"{digest(summary_path)}  {summary_path.name}\n",
        encoding="ascii",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
