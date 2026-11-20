---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- training-export
- training-export-trajectory

## Context
- docs/training-data-plan.md#3. Export: training records
- clutch/training.py
- clutch/__main__.py::_command
- clutch/evidence/schema.py::Attempt
- clutch/evidence/store.py::EvidenceStore
- tests/unit/test_training_export.py
- tests/unit/test_main_training_group.py

## On-demand
- docs/roadmap.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md

## Goal / Why
`clutch training export` today writes the `implement` and `preference` kinds (and, once `training-export-trajectory` merges, a trajectory on `implement`). After this ticket it also writes two more kinds and can limit the export by date, so a host can tune a small local model on its review and diagnosis work.

New kinds (each a chat-message record, `{"messages": [{"role": "user", ...}, {"role": "assistant", ...}], <the identity fields `training._identity` already writes>}`, one file per kind, written only when the kind is requested):
- `review` (`review.jsonl`): one record per attempt manifest whose `call_keys` include a call whose start record has surface `review`. User content is that call's prompt blob. Assistant content is `json.dumps({"outcome": manifest.outcome, "findings": manifest.findings}, sort_keys=True)`. Label is `negative` when a finding code is in `logic`, `acceptance`, `scope` or `leak`, otherwise `neutral`, the same rule `implement` uses. The plan's later-blamed label needs a retro attribution source that no code provides, so it is not built here.
- `diagnosis` (`diagnosis.jsonl`): one record per stem that has a call with surface `diagnose` under `llm/<stem>/` (the highest `(run_seq, attempt, call)` one) and a readable `tickets/<stem>/diagnosis.json`. User content is the call's prompt blob; assistant content is the file's text. Label is `merged` when the stem is a merged ticket (the later attempt succeeded), otherwise `neutral`.

`--since YYYY-MM-DD` keeps only records whose source call's `clock.wall_start` is on or after that date, for every kind including `implement` and `preference`; an invalid date is refused by the parser with exit 2.

This ticket delivers the row in parts, each deferred part with a follow-up roadmap row added here:
- `ticket` kind with `authored_by` attribution: row 178 `training-export-ticket`. It is deferred because the Author stage runs with no ticket, so its calls are keyed `llm/author/<pass>/...` with no stem (`clutch/author.py`, `clutch/driver.py`), and the `source:` frontmatter values are `human`, `seed` or `box:<class>` (`clutch/tickets.py`), not `author`. The row must specify the call-to-stem link and the `source` mapping.
- `conflict` kind: row 177 `training-export-conflict`. The export counts, as `conflict skipped`, the stems that have a call whose key's surface segment is `resolve`.
- `triage` stays out until the owner names a label source, because no code produces an `override_report` message.

Why: plan section 3 names these kinds, and the host's own review and diagnosis records are the narrow high-volume surfaces the flywheel targets.

## Boundary contract
### Training export
- disposition: extend
- owner: clutch/training.py
- consumers: the `clutch training export` handler in `clutch/__main__.py`; later `training-eval`
- observable change: `render` also builds the `review` and `diagnosis` kinds and honours a `since` date; its counts gain `review`, `diagnosis` and `conflict_skipped`; `report` prints them; `render` takes one more parameter, a `read_bytes(path)` reader used for the `tickets/<stem>/diagnosis.json` files, so the handler passes `checkout.fs.read_bytes` and the function does no I/O of its own. Failures: a missing prompt blob, call, or diagnosis file skips the record and counts it in `skipped`; the same second scrub (`_safe`) drops a record whole and counts it in `dropped`. Ordering: records are sorted by `(stem, run_seq, attempt)`, so two exports of the same sources are byte-identical. Held-out stems write no record of any kind.
- compatibility: `implement` and `preference` records, `sft.jsonl`, `preference.jsonl` and `holdout.txt` keep their shape; the default `--kinds` widens to four kinds, so a default export now also writes the two new files.
- acceptance: criteria 1-5.
- tests: tests/unit/test_training_export_kinds.py; its stand-in store and manifests carry `provider=NS(adapter=...)` and raise FileNotFoundError on `end`-record reads, so they work with the trajectory code in `render`.
- post-merge source of truth: clutch/training.py

### Command surface
- disposition: extend
- owner: clutch/__main__.py (`training export` parser and handler)
- consumers: operators, `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`
- observable change: `--kinds` accepts `implement`, `preference`, `review`, `diagnosis`; new `--since DATE` option; help, examples and the two verb tables describe them.
- compatibility: existing flags and exit codes are unchanged; no other verb changes.
- acceptance: criteria 6-7.
- tests: tests/unit/test_main_training_group.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/training.py`: the two kinds, `since` filtering, new counts, the `report` line, the reader parameter.
- `clutch/__main__.py`: widen `--kinds`, add `--since` (a type function that parses `YYYY-MM-DD` and exits 2 on a bad value), pass `checkout.fs.read_bytes`, update the `export` help text. Add no stderr print.
- `tests/unit/test_training_export.py`, `tests/unit/test_training_trajectory.py` and `tests/unit/test_main_training_group.py`: update only the expectations the change forces, namely the new `read_bytes` argument at `render` call sites, the `report` counts line and the accepted `--kinds` choices and default.
- `docs/how-clutch-works.md` section 2.1 and `clutch/docs/host-running.md`: update only the `training export` row to show `--kinds` and `--since`.
- `docs/roadmap.md`: add row 177 `training-export-conflict` (training plan 3, feature, P3, Depends on `training-export-kinds`) for building the `conflict` kind from `resolve` calls, and row 178 `training-export-ticket` (training plan 3, feature, P2, Depends on `training-export-kinds`) for the `ticket` kind as described in Goal. The check is that the roadmap parses; no standing text test.

Scope out: trajectory events (`training-export-trajectory`); the `ticket`, `conflict` and `triage` kinds (rows 178, 177, none); `training eval`; the host guide; `clutch/evidence/`; the attempt manifest writer.

## Scope fence
- clutch/training.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- docs/roadmap.md
- tests/unit/test_training_export.py
- tests/unit/test_training_trajectory.py
- tests/unit/test_main_training_group.py
- tests/unit/test_training_export_kinds.py

## Acceptance criteria
1. A manifest with a `review`-surface call and a `logic` finding yields a `review` record labelled `negative` whose assistant content decodes to its `outcome` and `findings`; a manifest with no `review` call yields no `review` record, not an empty-prompt one; checked by `./dev.py test tests/unit/test_training_export_kinds.py`.
2. A stem with a `diagnose` call and `diagnosis.json` yields a `diagnosis` record labelled `merged` when merged and `neutral` when not; a stem with the call but no file is skipped and counted in `skipped`, not written with empty content; checked by `./dev.py test tests/unit/test_training_export_kinds.py`.
3. `--since 2026-11-10` drops a record whose call `wall_start` is `2026-11-09T23:59:59Z` and keeps one on `2026-11-10`, for `implement` and `review` alike; checked by `./dev.py test tests/unit/test_training_export_kinds.py`.
4. Two stems with `resolve`-surface calls make the counts report `conflict skipped: 2` and write no conflict file; checked by `./dev.py test tests/unit/test_training_export_kinds.py`.
5. A held-out stem writes no `review` or `diagnosis` record, and a record containing a `Bearer` token of 20 or more characters is dropped and counted in `dropped`, not truncated; checked by `./dev.py test tests/unit/test_training_export_kinds.py`.
6. `--kinds` accepts the four kinds and rejects `ticket` and `conflict` with exit 2; `--since 2026-13-45` exits 2; the default kinds list has four entries; the formatted `training export` parser help contains `--since` and `diagnosis`; checked by `./dev.py test tests/unit/test_main_training_group.py`.
7. `docs/roadmap.md` still parses with rows 177 and 178 added, and the existing `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py` and `tests/unit/test_training_trajectory.py` still pass; checked by `uv run clutch roadmap status` and `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_training_trajectory.py`. The `training export` rows of both verb tables naming `--since` and the new kinds is a one-time review check.

## Verification
```
./dev.py test tests/unit/test_training_export.py tests/unit/test_training_export_kinds.py tests/unit/test_training_trajectory.py tests/unit/test_main_training_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py
uv run clutch roadmap status
```

## Definition of rejected
The branch writes a partly built record, writes a record for a held-out stem, exports a `ticket`, `conflict` or `triage` record, opens files other than through the passed reader, adds a `./dev.py` wrapper, or edits a file outside the fence.

## Time budget
- expected: 25m
- stuck: 50m
