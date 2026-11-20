---
state: confirmed
source: human
priority: P3
kind: chore
---

## Depends on
- training-export
- training-export-kinds
- training-export-ticket
- training-export-trajectory

## Context
- docs/training-data-plan.md#Rights and privacy
- docs/training-data-plan.md#4. The flywheel: how a host uses it
- clutch/docs/host-gemini.md
- clutch/training.py::NOTICE
- clutch/config.py::TrainingData
- tests/unit/test_docs_verb.py
- tests/integration/test_cli.py::test_docs_reports_installed_guides

## Goal / Why
Roadmap row 61, section 5 of `docs/training-data-plan.md`. Today a host learns about `training_data` and `clutch training export` only from the config inventory and the verb table. After this ticket a shipped guide, `clutch/docs/host-training.md`, tells a host how to enable training data, what is excluded, what the export writes, what the provider-terms notice means, and why to try retrieval first. `clutch host docs` lists it as a sixth guide, `training`, so agents on any host find it by the same path they find the others. Why: the plan says the host guide must state the provider-terms position, and nothing shipped does.

## Boundary contract
### Host guide listing
- disposition: extend
- owner: clutch/__main__.py::handle_docs
- consumers: `clutch host docs` and the agents and operators who read its output
- observable change: `clutch host docs` prints a sixth line, `.../clutch/docs/host-training.md  training data export`, after the `gemini` line; the five existing lines are unchanged
- compatibility: the five existing guide lines and their order are unchanged; the new guide is appended last
- acceptance: `tests/unit/test_docs_verb.py` and `tests/integration/test_cli.py::test_docs_reports_installed_guides` expect six guides ending with `training`
- tests: tests/unit/test_docs_verb.py, tests/unit/test_main_host_group.py and tests/integration/test_cli.py::test_docs_reports_installed_guides
- post-merge source of truth: clutch/__main__.py::handle_docs

### Training host guide
- disposition: create
- owner: clutch/docs/host-training.md
- consumers: `clutch host docs`, the README guide list, and host operators deciding whether to export training data
- observable change: a new shipped guide with the sections named in Scope in
- compatibility: no existing guide or verb changes; the guide restates no behavior the code owns beyond what it links to
- acceptance: the guide exists and contains each phrase listed in the acceptance criteria
- tests: the `python -c` check in `## Verification`
- post-merge source of truth: clutch/docs/host-training.md
- closest existing: `clutch/docs/host-gemini.md` and `clutch/docs/host-qwen.md` (provider setup guides), and `clutch/docs/host-contract.md` (the config inventory). None can hold it: the provider guides are per provider, and the contract is a field inventory that must not grow operator advice.
- earning reason: a process and operator-facing boundary; the plan's rights section requires the host guide to carry the provider-terms position, and the guide has one consumer set (`clutch host docs` and README) that already lists one guide per topic.

## Scope in / Scope out
Scope in:
- `clutch/docs/host-training.md` (new). Sections, in this order, each short and each linking to its owner rather than copying it:
  - `## Retrieval first`: past tickets, `run.md` decisions and review findings are the cheapest win; tune a model only after retrieval stops being enough. Names no verb for it (`clutch context` does not exist at HEAD) and says "the project index" where the plan does.
  - `## Enable it`: set `training_data: {enabled: true, exclude: [...]}` in `config.yaml`; only attempts after that carry a diff; with it off, `clutch training export` refuses with the paved road in `clutch/config.py::TrainingData.require_enabled`. Links to `host-contract.md` for the field inventory.
  - `## What is excluded`: the fixed always-excluded globs `.env*`, `*.pem`, `*.key`, `id_*` (read from `_TRAINING_EXCLUDE` in `clutch/config.py`), that `exclude` only adds to them, and that export drops, never partly writes, a record that fails its scrub and counts it.
  - `## Export`: `clutch training export --out DIR` with the kinds `implement`, `preference`, `review`, `diagnosis` and `ticket`, `--since`, `--holdout PCT` (splits by ticket and writes the held-out stems), `--no-trajectory`, and that ticket records carry `authored_by` (`human` or `author`) so a host can filter. Links to `host-running.md` for the verb row; copies no argv beyond `clutch training export --out DIR`.
  - `## Provider terms`: model outputs come from third-party providers whose terms may restrict training other models on them; the host checks each provider's terms before training; `export` prints that notice each run (`clutch/training.py::NOTICE`) and clutch decides nothing for the host.
  - `## Privacy`: everything stays under `state_dir`, clutch never uploads or trains, redaction beyond configured secrets is best effort, and a host with regulated data keeps `enabled: false` or excludes those paths.
- `clutch/__main__.py`: add `("training", "training data export")` as the last tuple in `handle_docs`'s guide list.
- `tests/unit/test_docs_verb.py`, `tests/unit/test_main_host_group.py` (`test_docs_and_doctor_need_no_config`, its name tuple on line 39) and `tests/integration/test_cli.py`: the `host docs` assertions expect six guides ending with `training` (the name tuple and `len(lines) == 5` become six).
- `README.md`: add one bullet under its guide list, `- [Training data guide](https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-training.md).`, after the Gemini bullet.
Scope out: `clutch training eval` and any text naming it, because it has no verb yet; it is `training-eval`, which adds its own paragraph here when it merges. Also out: the how-it-works doc, the contract and run guides (their training rows are already true), `clutch/help.py` (it describes extension surfaces), the extension directory, the roadmap (the driver strikes row 61 on merge), and any code behavior change. The only edits in `tests/integration/test_cli.py` and `tests/unit/test_main_host_group.py` are the `host docs` assertions named above, which the new guide forces.

## Scope fence
- clutch/docs/host-training.md
- clutch/__main__.py
- tests/unit/test_docs_verb.py
- tests/unit/test_main_host_group.py
- tests/integration/test_cli.py
- README.md

## Acceptance criteria
1. `clutch/docs/host-training.md` exists and contains each of `## Retrieval first`, `## Enable it`, `## What is excluded`, `## Export`, `## Provider terms`, `## Privacy`, `training_data`, `enabled: true`, `.env*`, `authored_by`, `--holdout`, `--no-trajectory`, `third-party providers`; checked by the first `python -c` command in `## Verification`.
2. The guide names no unbuilt verb: it contains none of `training eval`, `./dev.py`, or `clutch context`; checked by the first `python -c` command in `## Verification`.
3. `clutch host docs` prints six lines whose last path ends `host-training.md` and whose purpose is non-empty, and the first five are unchanged, not a list of five; checked by `./dev.py test tests/unit/test_docs_verb.py`.
4. The integration `host docs` test expects six guides and a `training` entry, not `len(lines) == 5`; checked by `./dev.py test tests/integration/test_cli.py -k test_docs_reports_installed_guides`.
5. `README.md` links `clutch/docs/host-training.md` once; checked by the second `python -c` command in `## Verification`.

## Verification
```
./dev.py test tests/unit/test_docs_verb.py
./dev.py test tests/integration/test_cli.py -k test_docs_reports_installed_guides
uv run python -c "import pathlib; g = pathlib.Path('clutch/docs/host-training.md').read_text(); assert all(s in g for s in ['## Retrieval first', '## Enable it', '## What is excluded', '## Export', '## Provider terms', '## Privacy', 'training_data', 'enabled: true', '.env*', 'authored_by', '--holdout', '--no-trajectory', 'third-party providers']); assert not any(s in g for s in ['training eval', './dev.py', 'clutch context'])"
uv run python -c "import pathlib; assert pathlib.Path('README.md').read_text().count('clutch/docs/host-training.md') == 1"
```

## Definition of rejected
The branch adds a verb or code behavior, describes `training eval`, copies `NOTICE` or the exclude list as a second source instead of linking or quoting them from the code, edits the how-it-works doc, the roadmap, or any file outside the fence, reorders the existing five guides, or tells the operator to hand-build a provider command line.

## Time budget
- expected: 12m
- stuck: 24m
