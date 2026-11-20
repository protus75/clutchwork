---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- training-config
- evidence-envelope

## Context
- docs/training-data-plan.md#2. The attempt manifest
- clutch/evidence/schema.py
- clutch/evidence/store.py
- clutch/runner.py::harvest
- clutch/runner.py::harvest_failure
- clutch/config.py::TrainingData
- tests/unit/test_evidence_store.py

## On-demand
- docs/how-clutch-works.md

## Goal / Why
When `training_data.enabled` is true, every failed or abandoned attempt leaves one attempt manifest in the evidence store before its worktree is removed. Today the code a review snagged is discarded (`harvest.json` keeps only a diff stat and a log tail), so the negative half of every preference pair is lost.

The manifest is `<state_dir>/evidence/attempts/<stem>/<run_seq>/<attempt>.json`, schema `clutch.evidence.attempt/1.0`. It holds:
- `stem`, `run_seq`, `attempt`;
- `base_sha` and `head_sha`;
- the blob id of the full attempt diff, with excluded paths removed;
- blob ids for each Check command output;
- the call keys the attempt made;
- the terminal outcome and reason, and the findings;
- the `engine_version` and spec versions carried by those calls.

It is written from `runner.harvest`, which every failed attempt, rework terminal, and orphan already reaches before any worktree removal. A failed manifest write is logged and never blocks the terminal.

## Boundary contract
### Attempt manifest record
- disposition: extend
- owner: clutch/evidence/schema.py (model) and clutch/evidence/store.py (writer and reader); the evidence store already owns call records, blobs and redaction
- consumers: `runner.harvest` (writer); the later `training-export` ticket (reader)
- observable change: new strict `Attempt` model, `EvidenceStore.write_attempt` and a tolerant `EvidenceStore.read_attempt`. Both follow `write_record` and `read_record`: the writer is strict, and the reader accepts any `clutch.evidence.attempt/1.<minor>`, drops unknown fields, and returns `SKIP` for another major version. A `call_keys(prefix)` lister over `evidence/calls/` feeds the manifest.
- compatibility: call records, `write_record`, `read_record`, `json_schema` and existing blobs are unchanged. With `training_data.enabled: false` (the default) nothing is written.
- acceptance: a valid manifest round-trips; a record with an extra field or a wrong type is refused by the writer; a minor-version-newer record reads with unknown fields dropped; a major-2 record reads as `SKIP`.
- tests: tests/unit/test_evidence_attempt_manifest.py
- post-merge source of truth: clutch/evidence/schema.py and clutch/evidence/store.py

### Harvest terminal path
- disposition: extend
- owner: clutch/runner.py::harvest
- consumers: `harvest_failure`, the rework terminal, and `harvest_orphan`, which all call `harvest`
- observable change: after the harvest artifact is written, and only when `config.training_data.enabled`, `harvest` writes the manifest. The diff is `git.diff(repo, "main", stem)`, split per file, with any file whose path matches `TrainingData.effective_exclude()` removed before storing. Check outputs are the spool files under `spools/<stem>/<attempt>/check/`. `run_seq` is `harvest`'s `attempt` argument (the journal run_seq), so the manifest path is `evidence/attempts/<stem>/<attempt>/<attempt>.json` even when the attempt made no calls. Call keys are `call_keys(f"llm/{stem}/{attempt}/")`, so calls from other runs of the same stem are never listed even when their surface-attempt segment is equal. Engine and spec versions come from those keys' start records, and both are empty when no call exists.
- compatibility: harvest output, lift and signals are unchanged. Any exception from the manifest write is journaled as the existing `harvest_failed` signal shape or logged to the engine log, never raised; failure and dispatch behavior is preserved. `harvest` reads `ctx.config.training_data.enabled` directly, with no `getattr` fallback.
- acceptance: see criteria.
- tests: tests/unit/test_runner_attempt_manifest.py
- post-merge source of truth: clutch/runner.py::harvest

## Scope in / Scope out
Scope in:
- the `Attempt` model, `write_attempt`, `read_attempt` and `call_keys` in the evidence package;
- the manifest write in `runner.harvest`;
- per-file exclusion of the diff by `effective_exclude()` globs, matched against the full path and the basename;
- an update to `docs/how-clutch-works.md` covering only the evidence store section (add the `attempts/` directory and the schema) and the harvest description in section 6.2 (mention the manifest);
- in `tests/unit/test_harvest_redaction.py`, `tests/unit/test_artifacts_harvest_cost_source.py` and `tests/integration/test_harvest_cost_source.py`, the only edit is adding `training_data=TrainingData()` (with its import) to each hand-built `config=SimpleNamespace(...)` that is passed to `runner.harvest`, because `harvest` now reads that attribute.

Scope out:
- `training export` and `training eval`, tracked as `training-export` and `training-eval`;
- the host guide `host-training.md`;
- the successful merge path in `merge.py` (its code is in git);
- the `json_schema` verb, which stays unchanged;
- the review verdict beyond the findings already passed to `harvest`;
- retention (`evidence.max_gb` already bounds the store).

## Scope fence
- clutch/evidence/schema.py
- clutch/evidence/store.py
- clutch/runner.py
- docs/how-clutch-works.md
- tests/unit/test_evidence_attempt_manifest.py
- tests/unit/test_runner_attempt_manifest.py
- tests/unit/test_harvest_redaction.py
- tests/unit/test_artifacts_harvest_cost_source.py
- tests/integration/test_harvest_cost_source.py

## Acceptance criteria
1. `EvidenceStore.write_attempt` followed by `read_attempt` returns an equal `Attempt`, and writing a dict with an extra key raises a validation error rather than writing a file; checked by `./dev.py test tests/unit/test_evidence_attempt_manifest.py`.
2. `read_attempt` of a `clutch.evidence.attempt/1.7` record with an unknown field returns the model without that field, and of a `clutch.evidence.attempt/2.0` record returns `SKIP`, not an exception; checked by `./dev.py test tests/unit/test_evidence_attempt_manifest.py`.
3. With `training_data.enabled: true`, `harvest` writes exactly one file at `evidence/attempts/<stem>/<run_seq>/<attempt>.json`, and the diff blob it references decompresses to the attempt diff; checked by `./dev.py test tests/unit/test_runner_attempt_manifest.py`.
4. With `training_data.enabled: false`, `harvest` creates no `evidence/attempts` directory, not an empty one; checked by `./dev.py test tests/unit/test_runner_attempt_manifest.py`.
5. A diff touching `.env.local` and `app.py` stores a blob that contains the `app.py` section and contains neither the `.env.local` path nor its content; checked by `./dev.py test tests/unit/test_runner_attempt_manifest.py`.
6. When the manifest write raises, `harvest` still writes the harvest artifact and lifts it, and the exception does not propagate; checked by `./dev.py test tests/unit/test_runner_attempt_manifest.py`.
7. A gate-failed, premise-failed, rejected-terminal and abandoned (orphan) harvest each write a manifest whose `outcome` equals the `terminal` passed to `harvest`; checked by `./dev.py test tests/unit/test_runner_attempt_manifest.py`.
8. Two attempts with an identical diff reference the same blob id; checked by `./dev.py test tests/unit/test_runner_attempt_manifest.py`.
9. The existing evidence and harvest tests still pass with `training_data=TrainingData()` added to their hand-built configs; checked by `./dev.py test tests/unit/test_evidence_store.py tests/unit/test_harvest_redaction.py tests/integration/test_harvest.py tests/integration/test_harvest_cost_source.py`.
10. With calls seeded under `llm/<stem>/0/...` and `llm/<stem>/1/...`, both at surface attempt 0, harvesting attempt 1 lists only the `llm/<stem>/1/` keys, not the run-0 keys; harvesting an orphan attempt with no calls still writes `evidence/attempts/<stem>/<attempt>/<attempt>.json` with an empty call-key list, not no file; checked by `./dev.py test tests/unit/test_runner_attempt_manifest.py`.

## Verification
```
./dev.py test tests/unit/test_evidence_attempt_manifest.py tests/unit/test_runner_attempt_manifest.py tests/unit/test_evidence_store.py tests/unit/test_harvest_redaction.py tests/unit/test_artifacts_harvest_cost_source.py tests/integration/test_harvest.py tests/integration/test_harvest_cost_source.py
```

## Definition of rejected
The branch is thrown away if it writes any manifest while `training_data.enabled` is false, if a manifest write failure can fail or block a terminal, if an excluded path's name or content appears in a stored diff blob, if `harvest` reads `training_data` through a `getattr` fallback, if it adds a second writer or SQLite use, or if it changes call record behavior.

## Time budget
- expected: 25m
- stuck: 50m
- reason: one schema model, one store writer, and one hook in harvest, with new test files; splitting would separate a writer from its only caller.
