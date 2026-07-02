# FCF Static Hidden-Twin Load-Repair Reproducibility Package

This package reproduces the static flagship experiment:

- Universe A: `85/1099 -> 0`
- Universe B: `110/1437 -> 0`
- Forced-answer witnesses: `6/6 fail`
- Nuisance binary split controls: `512 trials, 0 zero-obstruction successes`

Run:

```bash
python core_repro/reproduce_all.py
```

The run writes machine-checkable outputs to `recomputed/` and verifies
them against `expected_outputs/expected_summary.json`.

Scope: this is a static contact-refinement / required-distinction
reproducibility package. It does not claim dynamic action CREATE.

Public-audit note: the archive uses static load-repair terminology. Boundary
certificate files record that dynamic action CREATE is not validated here.

Integrated v3 additions:

- `source_evidence/` now includes extracted public certificate-source scripts
  and summaries;
- `core_repro/verify_expected_outputs.py` provides an explicit PASS/FAIL check;
- `.gitignore`, `SEND_READY_NOTE.md`, and manifest files make this version
  directly usable as a public GitHub/Zenodo package.
