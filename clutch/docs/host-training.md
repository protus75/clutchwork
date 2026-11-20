# Training data export

## Retrieval first

Past tickets, decisions in `run.md`, and review findings are the cheapest win. Use the project index for retrieval first; tune a model only after retrieval stops being enough.

## Enable it

Set `training_data: {enabled: true, exclude: [...]}` in `config.yaml`, replacing the example list with paths to exclude. Only attempts after enabling it carry a diff. When disabled, `clutch training export` refuses and tells you to set `training_data.enabled: true`; only later attempts carry a diff. See the [host contract](host-contract.md) for the field inventory.

## What is excluded

The fixed always-excluded globs are `.env*`, `*.pem`, `*.key`, and `id_*`; `exclude` only adds to them. The canonical list is `_TRAINING_EXCLUDE` in [config.py](../config.py). Export drops a record that fails its scrub instead of partly writing it, and counts the drop.

## Export

Run `clutch training export --out DIR`. The kinds are `implement`, `preference`, `review`, `diagnosis`, and `ticket`. Use `--since` to filter by date, `--holdout PCT` to split by ticket and write the held-out stems, and `--no-trajectory` to omit implement trajectories. Ticket records carry `authored_by` (`human` or `author`) so you can filter them. See the [host run guide](host-running.md) for the verb row.

## Provider terms

Model outputs come from third-party providers whose terms may restrict training other models on them. Check each provider's terms before training. Export prints the [provider-terms notice](../training.py) every run; clutch does not decide for the host.

## Privacy

Captured data stays on the host under `state_dir`; exports are written to the directory you choose. clutch never uploads data or trains a model. Redaction beyond configured secrets is best effort. If you handle regulated data, keep `enabled: false` or exclude those paths.
