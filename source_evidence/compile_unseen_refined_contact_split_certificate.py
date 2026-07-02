#!/usr/bin/env python3
"""Exact refined-contact split certificates for unseen C+ contact graphs.

This is a contact-repair certificate, not an action/creation certificate. It
keeps Q and tau fixed and asks how many finite contact subcells are sufficient
to ensure that every retained same-subcell contact edge has d_Q <= tau.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


ROOT = Path("/workspace/kolmogorov_creation")
OUTPUT = ROOT / "unseen_refined_contact_split_certificate"
FULL_CELL_GRAPH = ROOT / "a4_cplus_fourier_vorticity_full_audit" / "A4_CPLUS_CONTACT_EDGES.csv"
FOURPART_GRAPH = (
    ROOT
    / "a4_contact_only_unseen_audit_four_part_diagnostic"
    / "UNSEEN_CPLUS_CONTACT_EDGES.csv"
)
CONTRACT = ROOT / "frozen_contract" / "CHAOTIC_PDE_CREATION_CONTRACT.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def color_obstruction_graph(nodes: set[int], obstructions: list[tuple[int, int, float]]) -> dict[int, int]:
    adjacency: dict[int, set[int]] = {node: set() for node in nodes}
    for left, right, _ in obstructions:
        adjacency[left].add(right)
        adjacency[right].add(left)
    order = sorted(nodes, key=lambda node: (-len(adjacency[node]), node))

    for color_count in range(1, len(nodes) + 1):
        colors: dict[int, int] = {}

        def search(offset: int = 0) -> bool:
            if offset == len(order):
                return True
            node = order[offset]
            forbidden = {colors[other] for other in adjacency[node] if other in colors}
            for color in range(color_count):
                if color in forbidden:
                    continue
                colors[node] = color
                if search(offset + 1):
                    return True
                del colors[node]
            return False

        if search():
            return dict(colors)
    raise RuntimeError("coloring failed")


def audit_coloring(
    rows: np.ndarray,
    tau: float,
    *,
    cell_column: str | None,
) -> dict[str, object]:
    groups: dict[str, list[object]] = defaultdict(list)
    if cell_column is None:
        for row in rows:
            groups["all"].append(row)
    else:
        for row in rows:
            if int(row["cell_i"]) == int(row["cell_j"]):
                groups[str(int(row[cell_column]))].append(row)

    cells: dict[str, object] = {}
    total_edges = 0
    retained_edges = 0
    same_subcell_obstructions = 0
    max_colors = 0
    for group, group_rows in sorted(groups.items(), key=lambda item: item[0]):
        nodes: set[int] = set()
        edges: list[tuple[int, int, float]] = []
        obstructions: list[tuple[int, int, float]] = []
        for row in group_rows:
            left, right = int(row["global_i"]), int(row["global_j"])
            dq_name = "d_Q"
            dq = float(row[dq_name])
            nodes.update([left, right])
            edges.append((left, right, dq))
            if dq > tau:
                obstructions.append((left, right, dq))
        coloring = color_obstruction_graph(nodes, obstructions)
        color_count = 1 + max(coloring.values()) if coloring else 0
        max_colors = max(max_colors, color_count)
        retained = 0
        bad = 0
        for left, right, dq in edges:
            if coloring[left] == coloring[right]:
                retained += 1
                if dq > tau:
                    bad += 1
        total_edges += len(edges)
        retained_edges += retained
        same_subcell_obstructions += bad
        sizes = {
            str(color): int(sum(1 for value in coloring.values() if value == color))
            for color in range(color_count)
        }
        cells[group] = {
            "node_count": len(nodes),
            "contact_edges": len(edges),
            "original_obstructions": len(obstructions),
            "minimum_split_count": color_count,
            "subcell_sizes": sizes,
            "retained_same_subcell_edges": retained,
            "same_subcell_obstructions_after_split": bad,
            "split_assignment": {str(node): int(color) for node, color in sorted(coloring.items())},
        }

    return {
        "status": (
            "REFINED_CONTACT_SPLIT_RELEASE_PASS"
            if same_subcell_obstructions == 0
            else "REFINED_CONTACT_SPLIT_RELEASE_FAIL"
        ),
        "total_contact_edges": total_edges,
        "retained_same_subcell_edges": retained_edges,
        "same_subcell_obstructions_after_split": same_subcell_obstructions,
        "max_minimum_split_count": max_colors,
        "groups": cells,
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    contract = json.loads(CONTRACT.read_text(encoding="ascii"))
    tau = float(contract["obstruction"]["tau"])
    full_rows = np.genfromtxt(FULL_CELL_GRAPH, delimiter=",", names=True)
    fourpart_rows = np.genfromtxt(FOURPART_GRAPH, delimiter=",", names=True)
    if full_rows.shape == ():
        full_rows = np.asarray([full_rows])
    if fourpart_rows.shape == ():
        fourpart_rows = np.asarray([fourpart_rows])

    summary = {
        "status": "UNSEEN_REFINED_CONTACT_SPLIT_CERTIFICATE_COMPLETE",
        "certificate_type": "contact_repair_not_action_create",
        "tau": tau,
        "contract_sha256": digest(CONTRACT),
        "full_cell_graph_sha256": digest(FULL_CELL_GRAPH),
        "fourpart_graph_sha256": digest(FOURPART_GRAPH),
        "legality_note": (
            "This proves that a finite contact refinement can remove the listed "
            "unseen obstructions. It does not prove that a lawful dynamic action "
            "creates the refinement, and it does not constitute a V5 CREATE certificate."
        ),
        "cplus_cell_labeled_full_audit": audit_coloring(
            full_rows,
            tau,
            cell_column="cell_i",
        ),
        "fourpart_cplus_1099_graph_unlabeled": audit_coloring(
            fourpart_rows,
            tau,
            cell_column=None,
        ),
    }
    path = OUTPUT / "UNSEEN_REFINED_CONTACT_SPLIT_CERTIFICATE_SUMMARY.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")
    (OUTPUT / "RESULT_SHA256.txt").write_text(
        f"{digest(path)}  {path.name}\n",
        encoding="ascii",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
