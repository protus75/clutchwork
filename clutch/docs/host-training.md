<!-- clutch:meta
schema: clutch.meta/1.0
kind: guide
purpose: Host guide to training data: turning capture on, fixed exclusions, `training export` kinds and flags, how `training eval` scores agreement, provider terms and privacy
relates: [clutch/config.py, clutch/docs/host-contract.md, clutch/docs/host-running.md, clutch/training.py]
owner: engine
verified: 9aa0931a
hash: fc208d2e064b11ade19e34fa43c2a07ae7104595b1c39f07fb17bd6df43b21c7
-->
# Training data export and evaluation

## Retrieval first

Past tickets, decisions in `run.md`, and review findings are the cheapest win. Use the project index for retrieval first; tune a model only after retrieval stops being enough.

## Enable it

Set `training_data: {enabled: true, exclude: [...]}` in `config.yaml`, replacing the example list with paths to exclude. Only attempts after enabling it carry a diff. When disabled, `clutch training export` and `clutch training eval` refuse and tell you to set `training_data.enabled: true`; only later attempts carry a diff. See the [host contract](host-contract.md) for the field inventory.

## What is excluded

The fixed always-excluded globs are `.env*`, `*.pem`, `*.key`, and `id_*`; `exclude` only adds to them. The canonical list is `_TRAINING_EXCLUDE` in [config.py](../config.py). Export drops a record that fails its scrub instead of partly writing it, and counts the drop.

## Export

Run `clutch training export --out DIR`. The kinds are `implement`, `preference`, `review`, `diagnosis`, `ticket`, `conflict`, and `triage`. Use `--require-records` to exit 2 after writing the report and files if any requested kind has no records. Use `--since` to filter by date, `--holdout PCT` to split by ticket and write the held-out stems, and `--no-trajectory` to omit implement trajectories. Run `clutch index build` first to add `file_purposes` to implement records for indexed changed files; a missing or stale index may omit the field. Triage labels reflect operator overrides of the verdict. Ticket records carry `authored_by` (`human` or `author`) so you can filter them. See the [host run guide](host-running.md) for the verb row.

## Evaluate a review route

Run `clutch training eval --route medium/review --holdout FILE` with the holdout file from export. Only the review lens is supported; tiers are `low`, `medium`, `high` and `max`. Eval rebuilds review records for those stems and calls the route with each recorded prompt.

A recorded label is negative for logic, acceptance, scope or leak findings, and neutral otherwise. Agreement means the model replies `snag` exactly when the label is negative; `approve` and `rma` agree with neutral labels. Replies without a valid JSON verdict count as unparsed, never as agreement. The agreement fraction is agreements divided by all records (zero for no records, when the run exits 2). Eval also exits 2 when no held-out review record received a parsed verdict. The report prints total, agree, disagree and unparsed counts to stdout only; eval writes no journal, evidence records or engine log.

## Provider terms

Model outputs come from third-party providers whose terms may restrict training other models on them. Check each provider's terms before training. Export prints the [provider-terms notice](../training.py) every run; clutch does not decide for the host.

## Privacy

Captured data stays on the host under `state_dir`; exports are written to the directory you choose. clutch never uploads data or trains a model. Redaction beyond configured secrets is best effort. If you handle regulated data, keep `enabled: false` or exclude those paths.
