# Data Schema

`data_release/universe_A_frozen_edges.csv`

- `edge_id`: local edge id.
- `global_i`, `global_j`: endpoint node ids.
- `block_i`, `block_j`, `index_i`, `index_j`: frozen source metadata.
- `d_contact`: C+ contact distance for Universe A.
- `d_Q`: consequence distance.
- `original_obstruction`: `d_Q > tau`.
- `split_i`, `split_j`: lawful binary split membership.
- `retained_after_split`: whether the split keeps the edge.
- `post_split_obstruction`: retained edge still obstructs.

`data_release/universe_B_frozen_edges.csv`

Same as Universe A, with `cell_i`, `cell_j`, and `d_Cplus`; Universe B
is filtered to same-cell edges.

`C_contact_coordinates.csv`, `Cplus_contact_coordinates.csv`, `Q_labels.csv`

- One row per frozen node id.
- Coordinate columns are `c_###`, `cplus_###`, and `q_###`.

`lawful_split_membership.csv`

- One row per node id.
- Contains the lawful split labels used for Universe A and Universe B.
