#!/usr/bin/env python3
"""Compute a refined-contact split upper bound from the action closure matrix.

The standard finite-contact policy requires one action per frozen contact cell.
This diagnostic asks a stronger-but-structured question:

    If a lawful online/post-action contact were allowed to split a frozen cell
    into finitely many subcells, how many action-labeled subcells would suffice?

For an edge inside the same original cell, endpoints assigned to different
subcells are distinguished by the refined contact and therefore do not require
response closure. Endpoints assigned to the same action-labeled subcell must be
closed by that action in the frozen matrix.

This is an upper-bound target for a future lawful splitter, not a CREATE
certificate by itself.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import time
from pathlib import Path

import numpy as np


ROOT = Path("/workspace/kolmogorov_creation")
MATRIX = ROOT / "pair59_spatial_full_271_replay" / "EXTENDED_WITH_PAIR59_SPATIAL_MATRIX.npz"
QUANTIZER = ROOT / "delayed_action_closure_matrix" / "FROZEN_E0_QUANTIZER.npz"
OUTPUT = ROOT / "refined_contact_split_upper_bound"

MAX_K = 4
CELL_TIME_LIMIT_SECONDS = 30.0


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def solve_for_actions(
    node_count: int,
    edges: list[tuple[int, int, np.ndarray]],
    action_subset: tuple[int, ...],
    deadline: float,
) -> list[int] | None:
    k = len(action_subset)
    adjacency: list[list[tuple[int, np.ndarray]]] = [[] for _ in range(node_count)]
    for left, right, allowed in edges:
        adjacency[left].append((right, allowed))
        adjacency[right].append((left, allowed))

    domains = [set(range(k)) for _ in range(node_count)]
    assignment = [-1] * node_count

    def search() -> bool:
        if time.time() > deadline:
            raise TimeoutError
        target = -1
        best_size = 10**9
        for node in range(node_count):
            if assignment[node] >= 0:
                continue
            domain = domains[node]
            size = len(domain)
            if size == 0:
                return False
            if size < best_size or (
                size == best_size and len(adjacency[node]) > len(adjacency[target])
            ):
                target = node
                best_size = size
        if target < 0:
            return True

        ordered = sorted(domains[target])
        for color in ordered:
            action = action_subset[color]
            ok = True
            changed: list[tuple[int, int]] = []
            assignment[target] = color
            for neighbor, allowed_actions in adjacency[target]:
                if assignment[neighbor] == color and not allowed_actions[action]:
                    ok = False
                    break
                if assignment[neighbor] < 0 and not allowed_actions[action]:
                    if color in domains[neighbor]:
                        domains[neighbor].remove(color)
                        changed.append((neighbor, color))
                        if not domains[neighbor]:
                            ok = False
                            break
            if ok and search():
                return True
            for node, removed in reversed(changed):
                domains[node].add(removed)
            assignment[target] = -1
        return False

    if search():
        return [action_subset[color] for color in assignment]
    return None


def solve_cell(
    cell: int,
    pair_indices: np.ndarray,
    metadata: np.ndarray,
    closure: np.ndarray,
    action_ids: np.ndarray,
) -> dict[str, object]:
    endpoints = sorted(
        {
            int(endpoint)
            for pair in pair_indices.tolist()
            for endpoint in metadata[pair, :2].astype(int).tolist()
        }
    )
    endpoint_to_local = {endpoint: index for index, endpoint in enumerate(endpoints)}
    edges = [
        (
            endpoint_to_local[int(metadata[pair, 0])],
            endpoint_to_local[int(metadata[pair, 1])],
            closure[pair],
        )
        for pair in pair_indices.tolist()
    ]

    closed_counts = closure[pair_indices].sum(axis=0)
    useful_actions = np.flatnonzero(closed_counts > 0).tolist()
    useful_actions.sort(
        key=lambda idx: (-int(closed_counts[idx]), str(action_ids[idx]))
    )

    for k in range(1, MAX_K + 1):
        deadline = time.time() + CELL_TIME_LIMIT_SECONDS
        checked = 0
        for subset in itertools.combinations(useful_actions, k):
            checked += 1
            try:
                assignment = solve_for_actions(
                    len(endpoints),
                    edges,
                    subset,
                    deadline,
                )
            except TimeoutError:
                return {
                    "cell": cell,
                    "status": "TIME_LIMIT",
                    "endpoint_count": len(endpoints),
                    "pair_count": int(len(pair_indices)),
                    "searched_k": k,
                    "checked_subsets_at_k": checked,
                }
            if assignment is not None:
                action_to_endpoints: dict[str, list[int]] = {}
                for endpoint, action_index in zip(endpoints, assignment, strict=True):
                    action_to_endpoints.setdefault(str(action_ids[action_index]), []).append(endpoint)
                return {
                    "cell": cell,
                    "status": "REFINED_SPLIT_FEASIBLE",
                    "endpoint_count": len(endpoints),
                    "pair_count": int(len(pair_indices)),
                    "minimum_split_count": k,
                    "actions": [str(action_ids[index]) for index in subset],
                    "subcell_sizes": {
                        action: len(items)
                        for action, items in sorted(action_to_endpoints.items())
                    },
                    "endpoint_action_assignment": {
                        str(endpoint): str(action_ids[action_index])
                        for endpoint, action_index in zip(endpoints, assignment, strict=True)
                    },
                }
    return {
        "cell": cell,
        "status": "NO_REFINED_SPLIT_WITHIN_MAX_K",
        "endpoint_count": len(endpoints),
        "pair_count": int(len(pair_indices)),
        "max_k": MAX_K,
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    matrix = np.load(MATRIX, allow_pickle=True)
    quantizer = np.load(QUANTIZER)
    action_ids = matrix["action_ids"].astype(str)
    closure = matrix["closure"]
    metadata = matrix["pair_metadata"]
    tau = float(matrix["tau"])
    labels = quantizer["development_labels"]
    left = metadata[:, 0].astype(int)
    right = metadata[:, 1].astype(int)
    left_cells = labels[left]
    right_cells = labels[right]
    same_cell = left_cells == right_cells
    active_cells = sorted(set(left_cells[same_cell].astype(int).tolist()))

    cells = {}
    for cell in active_cells:
        pair_indices = np.flatnonzero(same_cell & (left_cells == cell))
        cells[str(cell)] = solve_cell(
            int(cell),
            pair_indices,
            metadata,
            closure,
            action_ids,
        )

    feasible = all(row["status"] == "REFINED_SPLIT_FEASIBLE" for row in cells.values())
    max_split = max(
        int(row.get("minimum_split_count", MAX_K + 1))
        for row in cells.values()
    )
    summary = {
        "status": (
            "REFINED_CONTACT_SPLIT_UPPER_BOUND_ALL_SAME_CELL_CLOSED"
            if feasible
            else "REFINED_CONTACT_SPLIT_UPPER_BOUND_INCOMPLETE"
        ),
        "matrix_sha256": digest(MATRIX),
        "quantizer_sha256": digest(QUANTIZER),
        "tau": tau,
        "same_cell_pair_count": int(np.sum(same_cell)),
        "action_count": int(len(action_ids)),
        "max_k_searched": MAX_K,
        "max_minimum_split_count": max_split,
        "certificate_type": "upper_bound_target_not_create_certificate",
        "legality_condition": (
            "A future protocol must realize these subcells using lawful finite "
            "contact available before assigning the subcell action. The endpoint "
            "assignment below is a structural target, not permitted evidence by "
            "itself."
        ),
        "cells": cells,
    }
    path = OUTPUT / "REFINED_CONTACT_SPLIT_UPPER_BOUND_SUMMARY.json"
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")
    (OUTPUT / "RESULT_SHA256.txt").write_text(
        f"{digest(path)}  {path.name}\n",
        encoding="ascii",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
