# Unseen Refined-Contact Split Certificate Verification

overall_status: PASS
tau: 1.035319346634406
certificate_type: verified_contact_repair_not_action_create

## Hash Checks

- contract_sha256: PASS
- full_cell_graph_sha256: PASS
- fourpart_graph_sha256: PASS

## Audit Results

### cplus_cell_labeled_full_audit

- ok: True
- total_contact_edges: 1437
- retained_same_subcell_edges: 1261
- post_split_obstructions: 0
- max_minimum_split_count: 2

- group 3: k=2, edges=650, original_obstructions=49, retained=572, post_obstructions=0, minimality=k=1 impossible because at least one original obstruction exists; k=2 assignment verified
- group 4: k=2, edges=637, original_obstructions=8, retained=614, post_obstructions=0, minimality=k=1 impossible because at least one original obstruction exists; k=2 assignment verified
- group 7: k=2, edges=106, original_obstructions=44, retained=40, post_obstructions=0, minimality=k=1 impossible because at least one original obstruction exists; k=2 assignment verified
- group 9: k=2, edges=9, original_obstructions=9, retained=0, post_obstructions=0, minimality=k=1 impossible because at least one original obstruction exists; k=2 assignment verified

### fourpart_cplus_1099_graph_unlabeled

- ok: True
- total_contact_edges: 1099
- retained_same_subcell_edges: 762
- post_split_obstructions: 0
- max_minimum_split_count: 2

- group all: k=2, edges=1099, original_obstructions=85, retained=762, post_obstructions=0, minimality=k=1 impossible because at least one original obstruction exists; k=2 assignment verified

## Formal Meaning

This verifies a contact-repair theorem: after the reported finite split, every retained same-subcell contact edge satisfies d_Q <= tau.

It does not verify dynamic creation. A V5 CREATE certificate would still need a lawful action or online finite-contact rule that realizes the split before using it.

