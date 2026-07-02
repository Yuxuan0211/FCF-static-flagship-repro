# Static Hidden-Twin Load-Repair Flagship

Status: `STATIC_HIDDEN_TWIN_LOAD_REPAIR_FLAGSHIP_COMPLETE`

## Decision

- Static flagship: `complete`.
- Dynamic action CREATE: `not claimed`.
- Stable V5 CREATE certificate: `not claimed`.

## Core Transition

- `V(C_plus,Q)=0 -> V((C_plus, splitter(C_plus)),Q)=1`.
- Contact primitive creation gate: `True`.

## Hidden-Twin Load

- Fourpart C+ graph: `85/1099` original obstructions; post-split `0`; worst retained dQ `1.0040470361709595`.
- Full same-cell graph: `110/1437` original obstructions; post-split `0`; worst retained dQ `1.0347025394439695`.
- Maximum minimum split count: `2` on both audited graphs.

## Forced-Answer Failure

A forced C-only answer must be stable on contact edges and true to Q within tau/2. All audited witnesses fail:

- `GLOBAL_MEAN_FORCED_QBAR`: pass `False`, failure `stable_but_not_true_to_Q`, unstable edges `0`, max endpoint error `0.9692957868642598`.
- `CONTACT_COMPONENT_MEAN_QBAR`: pass `False`, failure `stable_but_not_true_to_Q`, unstable edges `0`, max endpoint error `0.7999732494978865`.
- `ONE_NEAREST_NEIGHBOR_MEMORIZER`: pass `False`, failure `unstable_on_contact_edges`, unstable edges `85`, max endpoint error `0.0`.
- `RIDGE_ON_C_ONLY`: pass `False`, failure `stable_but_not_true_to_Q`, unstable edges `0`, max endpoint error `0.9811658822448731`.
- `RIDGE_ON_CPLUS_NO_SPLITTER`: pass `False`, failure `stable_but_not_true_to_Q`, unstable edges `0`, max endpoint error `1.0897554448106914`.
- `RIDGE_ON_C_PLUS_512_RANDOM_NUISANCE_FEATURES`: pass `False`, failure `unstable_on_contact_edges`, unstable edges `2`, max endpoint error `1.26005337562757`.

## Irrelevant-Info Control

- Random binary nuisance trials: `512`.
- Zero-obstruction random trials: `0`.
- Best random post-split obstructions: `22`.
- Median random post-split obstructions: `42.0`.

## Refusal vs Repair

- Fourpart forced accept-all unsafe edges: `85`.
- Fourpart refusal accepted edges: `713`, unsafe `0`.
- Fourpart lawful repair retained edges: `762`, unsafe `0`.
- Full forced accept-all unsafe edges: `110`.
- Full refusal accepted edges: `1239`, unsafe `0`.
- Full lawful repair retained edges: `1261`, unsafe `0`.

## Final Claim

PDE-level hidden-twin obstruction and lawful minimal contact repair are demonstrated; forced answering and irrelevant binary nuisance splits do not supply the missing required distinction; refusal is safer than forced answering, and the lawful splitter restores safe release.

Not claimed: dynamic action creation or V5 stable CREATE.
