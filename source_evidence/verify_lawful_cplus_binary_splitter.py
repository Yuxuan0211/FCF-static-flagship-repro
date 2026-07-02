#!/usr/bin/env python3
"""Verify lawful C+ binary splitters for the Kolmogorov contact graphs.

The splitters below use only frozen C+ contact coordinates. They do not use
endpoint ids, d_Q values, graph color labels, block ids, or metadata at runtime.

This verifies lawful contact-refinement realization:
    C_refined(r) = (C_plus(r), splitter(C_plus(r)))

It is still not an action-created V5 certificate. It proves that the binary
split can be realized as a finite contact refinement.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path("/workspace/kolmogorov_creation")
OUTPUT = ROOT / "lawful_cplus_binary_splitter_certificate"
ARRAYS = (
    ROOT
    / "a4_contact_only_unseen_audit_four_part_diagnostic"
    / "UNSEEN_CONTACT_ONLY_AUDIT_ARRAYS.npz"
)
NORMALIZER = (
    ROOT
    / "a4_contact_only_unseen_audit_four_part_diagnostic"
    / "FROZEN_CPLUS_NORMALIZERS.npz"
)
FOURPART_GRAPH = (
    ROOT
    / "a4_contact_only_unseen_audit_four_part_diagnostic"
    / "UNSEEN_CPLUS_CONTACT_EDGES.csv"
)
FULL_CELL_GRAPH = ROOT / "a4_cplus_fourier_vorticity_full_audit" / "A4_CPLUS_CONTACT_EDGES.csv"
CONTRACT = ROOT / "frozen_contract" / "CHAOTIC_PDE_CREATION_CONTRACT.json"

Tree = tuple[Any, ...]

FOURPART_1099_TREE: Tree = (
    "node",
    128,
    -0.8366104364395142,
    ("node", 7, -0.12538572400808334, ("leaf", 0), ("leaf", 1)),
    (
        "node",
        0,
        0.05874338746070862,
        (
            "node",
            99,
            -1.2131552696228027,
            ("leaf", 1),
            (
                "node",
                0,
                -0.5450520813465118,
                (
                    "node",
                    0,
                    -0.761202335357666,
                    ("node", 6, 0.8766142129898071, ("leaf", 0), ("leaf", 1)),
                    ("leaf", 0),
                ),
                ("leaf", 0),
            ),
        ),
        ("leaf", 0),
    ),
)

FULL_CELL_1509_TREE: Tree = (
    "node",
    106,
    1.160978078842163,
    (
        "node",
        49,
        -0.9805869460105896,
        ("node", 10, -0.9465833008289337, ("leaf", 0), ("leaf", 1)),
        (
            "node",
            0,
            -0.048747343942523,
            (
                "node",
                1,
                -1.45675528049469,
                ("leaf", 1),
                ("node", 60, 1.3249221444129944, ("leaf", 0), ("leaf", 1)),
            ),
            (
                "node",
                0,
                0.3793182075023651,
                ("node", 27, -2.172544002532959, ("leaf", 1), ("leaf", 0)),
                ("leaf", 0),
            ),
        ),
    ),
    ("leaf", 1),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, data: object) -> None:
    temporary = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="ascii")
    os.replace(temporary, path)


def tree_predict(tree: Tree, vector: np.ndarray) -> int:
    if tree[0] == "leaf":
        return int(tree[1])
    _, feature, threshold, left, right = tree
    return tree_predict(left if float(vector[int(feature)]) <= float(threshold) else right, vector)


def tree_features(tree: Tree) -> list[int]:
    if tree[0] == "leaf":
        return []
    _, feature, _, left, right = tree
    return sorted({int(feature), *tree_features(left), *tree_features(right)})


def tree_depth(tree: Tree) -> int:
    if tree[0] == "leaf":
        return 0
    return 1 + max(tree_depth(tree[3]), tree_depth(tree[4]))


def read_rows(path: Path) -> np.ndarray:
    rows = np.genfromtxt(path, delimiter=",", names=True)
    if rows.shape == ():
        rows = np.asarray([rows])
    return rows


def verify_graph(
    graph_path: Path,
    tree: Tree,
    cplus_contacts: np.ndarray,
    tau: float,
    *,
    same_cell_only: bool,
) -> dict[str, object]:
    rows = read_rows(graph_path)
    nodes: set[int] = set()
    considered_rows = []
    for row in rows:
        if same_cell_only and int(row["cell_i"]) != int(row["cell_j"]):
            continue
        considered_rows.append(row)
        nodes.add(int(row["global_i"]))
        nodes.add(int(row["global_j"]))
    colors = {
        node: tree_predict(tree, cplus_contacts[node].astype(float))
        for node in sorted(nodes)
    }
    retained = 0
    original_obstructions = 0
    post_obstructions = 0
    worst_retained = 0.0
    for row in considered_rows:
        left, right = int(row["global_i"]), int(row["global_j"])
        dq = float(row["d_Q"])
        if dq > tau:
            original_obstructions += 1
        if colors[left] == colors[right]:
            retained += 1
            worst_retained = max(worst_retained, dq)
            if dq > tau:
                post_obstructions += 1
    sizes = {
        str(color): int(sum(1 for value in colors.values() if value == color))
        for color in sorted(set(colors.values()))
    }
    return {
        "graph": str(graph_path),
        "same_cell_only": same_cell_only,
        "node_count": len(nodes),
        "edge_count": len(considered_rows),
        "original_obstructions": original_obstructions,
        "retained_same_subcell_edges": retained,
        "post_split_obstructions": post_obstructions,
        "worst_retained_dQ": worst_retained,
        "pass": post_obstructions == 0,
        "color_sizes": sizes,
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    arrays = np.load(ARRAYS, allow_pickle=True)
    contract = json.loads(CONTRACT.read_text(encoding="ascii"))
    tau = float(contract["obstruction"]["tau"])
    cplus_contacts = arrays["cplus_contacts"]

    fourpart = verify_graph(
        FOURPART_GRAPH,
        FOURPART_1099_TREE,
        cplus_contacts,
        tau,
        same_cell_only=False,
    )
    full_cell = verify_graph(
        FULL_CELL_GRAPH,
        FULL_CELL_1509_TREE,
        cplus_contacts,
        tau,
        same_cell_only=True,
    )

    summary = {
        "status": (
            "LAWFUL_CPLUS_BINARY_SPLITTER_REALIZATION_PASS"
            if fourpart["pass"] and full_cell["pass"]
            else "LAWFUL_CPLUS_BINARY_SPLITTER_REALIZATION_FAIL"
        ),
        "certificate_type": "finite_contact_refinement_realization_not_dynamic_create",
        "runtime_inputs_allowed": ["frozen cplus_contacts coordinates only"],
        "runtime_inputs_forbidden": ["endpoint_id", "block_id", "metadata", "d_Q", "graph coloring label"],
        "tau": tau,
        "arrays_sha256": digest(ARRAYS),
        "normalizer_sha256": digest(NORMALIZER),
        "contract_sha256": digest(CONTRACT),
        "fourpart_graph_sha256": digest(FOURPART_GRAPH),
        "full_cell_graph_sha256": digest(FULL_CELL_GRAPH),
        "fourpart_1099_splitter": {
            "features": tree_features(FOURPART_1099_TREE),
            "depth": tree_depth(FOURPART_1099_TREE),
            "tree": FOURPART_1099_TREE,
            "verification": fourpart,
        },
        "full_cell_1509_splitter": {
            "features": tree_features(FULL_CELL_1509_TREE),
            "depth": tree_depth(FULL_CELL_1509_TREE),
            "tree": FULL_CELL_1509_TREE,
            "verification": full_cell,
        },
        "final_gate": {
            "contact_repair_realized": bool(fourpart["pass"] and full_cell["pass"]),
            "dynamic_action_create_validated": False,
            "v5_create_certificate": False,
            "reason_not_create": (
                "The split is now realized as a lawful finite-contact refinement, "
                "but no action has been shown to dynamically create this refinement "
                "or to pass half-dt/perturbation/nontrivial-dynamics gates."
            ),
        },
    }
    summary_path = OUTPUT / "LAWFUL_CPLUS_BINARY_SPLITTER_SUMMARY.json"
    atomic_json(summary_path, summary)
    (OUTPUT / "RESULT_SHA256.txt").write_text(
        f"{digest(summary_path)}  {summary_path.name}\n",
        encoding="ascii",
    )
    print(json.dumps({
        "status": summary["status"],
        "fourpart_1099": fourpart,
        "full_cell_1509_same_cell": full_cell,
        "summary": str(summary_path),
    }, indent=2))


if __name__ == "__main__":
    main()
