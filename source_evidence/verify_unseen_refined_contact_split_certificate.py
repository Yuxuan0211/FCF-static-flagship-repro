#!/usr/bin/env python3
"""Verify the unseen refined-contact split certificate from source graphs.

This verifier proves the contact-repair claim encoded in
UNSEEN_REFINED_CONTACT_SPLIT_CERTIFICATE_SUMMARY.json:

1. Source hashes match the recorded certificate inputs.
2. Every node in each audited graph/group has a split assignment.
3. Every retained same-subcell contact edge has d_Q <= tau.
4. The reported split count is minimal for each group:
   - if there is no original obstruction, k=1 is feasible and minimal;
   - if there is at least one original obstruction, k=1 is impossible;
   - the reported k=2 assignment is therefore minimal.

This is a contact-repair proof. It does not prove that a dynamic action creates
the split, and it does not certify V5 CREATE.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import numpy as np


ROOT = Path("/workspace/kolmogorov_creation")
CERT_DIR = ROOT / "unseen_refined_contact_split_certificate"
SUMMARY = CERT_DIR / "UNSEEN_REFINED_CONTACT_SPLIT_CERTIFICATE_SUMMARY.json"
FULL_CELL_GRAPH = ROOT / "a4_cplus_fourier_vorticity_full_audit" / "A4_CPLUS_CONTACT_EDGES.csv"
FOURPART_GRAPH = (
    ROOT
    / "a4_contact_only_unseen_audit_four_part_diagnostic"
    / "UNSEEN_CPLUS_CONTACT_EDGES.csv"
)
CONTRACT = ROOT / "frozen_contract" / "CHAOTIC_PDE_CREATION_CONTRACT.json"
OUTPUT = CERT_DIR / "verification"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="ascii")
    os.replace(tmp, path)


def as_rows(path: Path) -> np.ndarray:
    rows = np.genfromtxt(path, delimiter=",", names=True)
    if rows.shape == ():
        rows = np.asarray([rows])
    return rows


def group_rows(rows: np.ndarray, group: str, *, cell_labeled: bool) -> list[object]:
    if not cell_labeled:
        return list(rows)
    result = []
    cell = int(group)
    for row in rows:
        if int(row["cell_i"]) == cell and int(row["cell_j"]) == cell:
            result.append(row)
    return result


def verify_group(
    rows: list[object],
    group_summary: dict[str, object],
    tau: float,
) -> dict[str, object]:
    assignment = {
        int(node): int(color)
        for node, color in dict(group_summary["split_assignment"]).items()
    }
    nodes: set[int] = set()
    original_obstructions = 0
    retained = 0
    post_obstructions = 0
    missing_nodes: set[int] = set()
    used_colors: set[int] = set()

    worst_retained_dq = float("-inf")
    worst_original_obstruction = float("-inf")

    for row in rows:
        left, right = int(row["global_i"]), int(row["global_j"])
        dq = float(row["d_Q"])
        nodes.update([left, right])
        if dq > tau:
            original_obstructions += 1
            worst_original_obstruction = max(worst_original_obstruction, dq)
        if left not in assignment:
            missing_nodes.add(left)
        if right not in assignment:
            missing_nodes.add(right)
        if left in assignment and right in assignment:
            used_colors.update([assignment[left], assignment[right]])
            if assignment[left] == assignment[right]:
                retained += 1
                worst_retained_dq = max(worst_retained_dq, dq)
                if dq > tau:
                    post_obstructions += 1

    reported_k = int(group_summary["minimum_split_count"])
    actual_k = 1 + max(used_colors) if used_colors else 0
    k1_feasible = original_obstructions == 0
    minimality = (
        "k=1 feasible and minimal"
        if k1_feasible and reported_k == 1
        else "k=1 impossible because at least one original obstruction exists; k=2 assignment verified"
        if (not k1_feasible and reported_k == 2 and post_obstructions == 0)
        else "minimality check failed"
    )

    ok = (
        not missing_nodes
        and post_obstructions == 0
        and retained == int(group_summary["retained_same_subcell_edges"])
        and original_obstructions == int(group_summary["original_obstructions"])
        and actual_k == reported_k
        and minimality != "minimality check failed"
    )

    return {
        "ok": ok,
        "node_count": len(nodes),
        "reported_node_count": int(group_summary["node_count"]),
        "contact_edges": len(rows),
        "reported_contact_edges": int(group_summary["contact_edges"]),
        "missing_nodes": sorted(missing_nodes),
        "original_obstructions": original_obstructions,
        "reported_original_obstructions": int(group_summary["original_obstructions"]),
        "retained_same_subcell_edges": retained,
        "reported_retained_same_subcell_edges": int(
            group_summary["retained_same_subcell_edges"]
        ),
        "post_split_obstructions": post_obstructions,
        "reported_post_split_obstructions": int(
            group_summary["same_subcell_obstructions_after_split"]
        ),
        "reported_k": reported_k,
        "actual_k": actual_k,
        "k1_feasible": k1_feasible,
        "minimality": minimality,
        "worst_retained_dQ": None if worst_retained_dq == float("-inf") else worst_retained_dq,
        "worst_original_obstruction_dQ": (
            None
            if worst_original_obstruction == float("-inf")
            else worst_original_obstruction
        ),
    }


def verify_audit(
    name: str,
    rows: np.ndarray,
    audit_summary: dict[str, object],
    tau: float,
    *,
    cell_labeled: bool,
) -> dict[str, object]:
    group_results = {}
    total_edges = 0
    total_retained = 0
    total_post = 0
    ok = True
    for group, group_summary in dict(audit_summary["groups"]).items():
        rows_for_group = group_rows(rows, group, cell_labeled=cell_labeled)
        result = verify_group(rows_for_group, group_summary, tau)
        group_results[group] = result
        ok = ok and bool(result["ok"])
        total_edges += result["contact_edges"]
        total_retained += result["retained_same_subcell_edges"]
        total_post += result["post_split_obstructions"]

    ok = (
        ok
        and total_edges == int(audit_summary["total_contact_edges"])
        and total_retained == int(audit_summary["retained_same_subcell_edges"])
        and total_post == int(audit_summary["same_subcell_obstructions_after_split"])
    )
    return {
        "ok": ok,
        "name": name,
        "total_contact_edges": total_edges,
        "reported_total_contact_edges": int(audit_summary["total_contact_edges"]),
        "retained_same_subcell_edges": total_retained,
        "reported_retained_same_subcell_edges": int(
            audit_summary["retained_same_subcell_edges"]
        ),
        "post_split_obstructions": total_post,
        "reported_post_split_obstructions": int(
            audit_summary["same_subcell_obstructions_after_split"]
        ),
        "max_minimum_split_count": int(audit_summary["max_minimum_split_count"]),
        "groups": group_results,
    }


def make_report(result: dict[str, object]) -> str:
    lines = [
        "# Unseen Refined-Contact Split Certificate Verification",
        "",
        f"overall_status: {result['status']}",
        f"tau: {result['tau']}",
        f"certificate_type: {result['certificate_type']}",
        "",
        "## Hash Checks",
        "",
    ]
    for key, value in result["hash_checks"].items():
        lines.append(f"- {key}: {'PASS' if value else 'FAIL'}")
    lines.extend(["", "## Audit Results", ""])
    for audit_key in ["cplus_cell_labeled_full_audit", "fourpart_cplus_1099_graph_unlabeled"]:
        audit = result[audit_key]
        lines.append(f"### {audit_key}")
        lines.append("")
        lines.append(f"- ok: {audit['ok']}")
        lines.append(f"- total_contact_edges: {audit['total_contact_edges']}")
        lines.append(f"- retained_same_subcell_edges: {audit['retained_same_subcell_edges']}")
        lines.append(f"- post_split_obstructions: {audit['post_split_obstructions']}")
        lines.append(f"- max_minimum_split_count: {audit['max_minimum_split_count']}")
        lines.append("")
        for group, group_result in audit["groups"].items():
            if (
                group_result["original_obstructions"]
                or group_result["reported_k"] > 1
                or audit_key == "fourpart_cplus_1099_graph_unlabeled"
            ):
                lines.append(
                    "- group "
                    f"{group}: k={group_result['reported_k']}, "
                    f"edges={group_result['contact_edges']}, "
                    f"original_obstructions={group_result['original_obstructions']}, "
                    f"retained={group_result['retained_same_subcell_edges']}, "
                    f"post_obstructions={group_result['post_split_obstructions']}, "
                    f"minimality={group_result['minimality']}"
                )
        lines.append("")
    lines.extend(
        [
            "## Formal Meaning",
            "",
            "This verifies a contact-repair theorem: after the reported finite split, every retained same-subcell contact edge satisfies d_Q <= tau.",
            "",
            "It does not verify dynamic creation. A V5 CREATE certificate would still need a lawful action or online finite-contact rule that realizes the split before using it.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    cert = json.loads(SUMMARY.read_text(encoding="ascii"))
    contract = json.loads(CONTRACT.read_text(encoding="ascii"))
    tau = float(contract["obstruction"]["tau"])
    full_rows = as_rows(FULL_CELL_GRAPH)
    fourpart_rows = as_rows(FOURPART_GRAPH)

    result = {
        "status": "PASS",
        "certificate_type": "verified_contact_repair_not_action_create",
        "tau": tau,
        "hash_checks": {
            "contract_sha256": cert["contract_sha256"] == digest(CONTRACT),
            "full_cell_graph_sha256": cert["full_cell_graph_sha256"] == digest(FULL_CELL_GRAPH),
            "fourpart_graph_sha256": cert["fourpart_graph_sha256"] == digest(FOURPART_GRAPH),
        },
        "cplus_cell_labeled_full_audit": verify_audit(
            "cplus_cell_labeled_full_audit",
            full_rows,
            cert["cplus_cell_labeled_full_audit"],
            tau,
            cell_labeled=True,
        ),
        "fourpart_cplus_1099_graph_unlabeled": verify_audit(
            "fourpart_cplus_1099_graph_unlabeled",
            fourpart_rows,
            cert["fourpart_cplus_1099_graph_unlabeled"],
            tau,
            cell_labeled=False,
        ),
    }
    if not all(result["hash_checks"].values()):
        result["status"] = "FAIL"
    if not result["cplus_cell_labeled_full_audit"]["ok"]:
        result["status"] = "FAIL"
    if not result["fourpart_cplus_1099_graph_unlabeled"]["ok"]:
        result["status"] = "FAIL"

    summary_path = OUTPUT / "VERIFICATION_SUMMARY.json"
    report_path = OUTPUT / "FORMAL_VERIFICATION_REPORT.md"
    atomic_write(summary_path, json.dumps(result, indent=2) + "\n")
    atomic_write(report_path, make_report(result) + "\n")
    (OUTPUT / "VERIFICATION_SHA256.txt").write_text(
        f"{digest(summary_path)}  {summary_path.name}\n"
        f"{digest(report_path)}  {report_path.name}\n",
        encoding="ascii",
    )
    print(json.dumps({
        "status": result["status"],
        "cplus_cell_labeled_full_audit": result["cplus_cell_labeled_full_audit"]["ok"],
        "fourpart_cplus_1099_graph_unlabeled": result["fourpart_cplus_1099_graph_unlabeled"]["ok"],
        "report": str(report_path),
    }, indent=2))


if __name__ == "__main__":
    main()
