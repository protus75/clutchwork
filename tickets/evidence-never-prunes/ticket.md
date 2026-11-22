---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/evidence/store.py::EvidenceStore.prune
- clutch/providers.py::CliAdapter.invoke
- clutch/config.py::Evidence
- clutch/doctor.py
- docs/how-clutch-works.md#10.4 Evidence records
- tests/unit/test_evidence_envelope.py::Rig
- tests/unit/test_evidence_config.py
- tests/unit/test_main_evidence_group.py
- tests/unit/test_main_host_group.py
- tests/unit/test_main_view_group.py
- tests/unit/test_host_running.py

## On-demand
- clutch/__main__.py

## Goal / Why
Today, after every completed provider record, `CliAdapter.invoke` calls `EvidenceStore.prune` with `evidence.max_gb`, which silently deletes the oldest calls' stdout, stderr and arrival-time blobs. Those blobs are the model replies that `clutch/training.py` reads (`_reply_text`, `_trajectory`), so the engine destroys training data with no notice. The owner (2026-11-22) calls silent data discard unacceptable.

After this ticket nothing deletes evidence on its own. The size setting is renamed `evidence.warn_gb` (default 20) and only triggers a warning. `clutch host doctor` shows a `WARN evidence` row (the run still passes) and `clutch view status` prints one `evidence:` line when the blob store's on-disk size exceeds the threshold; both name the size, the threshold and the paved road: back up with `clutch training export --out <dir>`, raise `evidence.warn_gb`, or run `clutch evidence prune --to-gb N`. Pruning survives only as that explicit operator verb, which reuses the existing `prune` function.

Class prevention: evidence deletion has exactly one entry point, the writer-locked `evidence prune` verb, and a unit test fails if `invoke` removes any blob.

## Boundary contract
### Evidence retention policy
- disposition: replace
- owner: clutch/providers.py::CliAdapter.invoke (the automatic caller) and clutch/evidence/store.py (the store)
- consumers: every keyed provider call; `clutch/training.py` and `latest_stdout` readers of stdout blobs
- observable change: `invoke` never deletes a blob; evidence grows until an operator runs `clutch evidence prune --to-gb N`
- compatibility: breaking by design. The old contract (automatic prune to `evidence.max_gb` after each end record) is removed with no flag or alias; no consumer depended on blobs disappearing, and readers already tolerate a missing blob via `FileNotFoundError`. Records and the on-disk layout are unchanged.
- acceptance: a provider call with the store over the threshold leaves every pre-existing blob file present
- tests: new unit test drives `CliAdapter.invoke` through the `Rig` fake with the store's `size` reporting far over the threshold and asserts no blob was removed
- post-merge source of truth: docs/how-clutch-works.md section 10.4 and clutch/providers.py

### Evidence size setting
- disposition: replace
- owner: clutch/config.py::Evidence
- consumers: clutch/providers.py (no longer), clutch/doctor.py, clutch/__main__.py status handler, clutch/docs/host-contract.md config-fields block, docs/how-clutch-works.md section 11
- observable change: `evidence.max_gb` becomes `evidence.warn_gb` (positive integer GB, default 20); a config still setting `max_gb` is refused by the strict model like any unknown key
- compatibility: old name removed in place with every reader updated in the same change; `config.yaml` in this repo does not set it, so no migration here
- acceptance: `Evidence().warn_gb == 20`, `Evidence(warn_gb=0)` is refused, and `Evidence(max_gb=20)` is refused
- tests: tests/unit/test_evidence_config.py
- post-merge source of truth: clutch/config.py

### Evidence size warning
- disposition: create
- owner: clutch/evidence/store.py (a `blob_bytes` method on `EvidenceStore` and a `size_warning` function beside it)
- consumers: `host doctor` and `view status`
- observable change: one message string, or none, built from the blob store's on-disk size and `evidence.warn_gb`; doctor shows it as a `WARN` row (exit stays 0) and status prints it as an `evidence:` line
- compatibility: additive; absent when at or under the threshold, so existing doctor and status output is unchanged for small stores
- acceptance: over the threshold both surfaces show the message with size, threshold and the three roads; at or under it neither does
- tests: new unit tests for the helper, the doctor row, and the status line
- post-merge source of truth: clutch/evidence/store.py
- closest existing: `EvidenceStore.prune` (computes the same total inline but returns nothing), `doctor.Check` (pass/fail only), `status.render` (journal projection only)
- earning reason: two production consumers (doctor and status) need the same message, and a shared owner prevents two wordings of the paved road; `prune` cannot return the total without changing its contract, and the journal-only status projection must stay free of store I/O.

### Evidence prune verb
- disposition: create
- owner: clutch/__main__.py (`evidence prune` under the existing `evidence` group)
- consumers: operators and the warning's paved road
- observable change: `clutch evidence prune --to-gb N` takes the writer lock, calls the existing `EvidenceStore.prune` with `N * 10**9` bytes, and prints the blob size before and after; refuses a negative N with a paved road; refuses while the lock is held
- compatibility: additive; `prune` itself is unchanged
- acceptance: with the store over N GB the oldest eligible blobs are removed until under N and records remain; a store already under N is untouched
- tests: new unit test for the verb, extending the closed evidence verb set test
- post-merge source of truth: clutch/__main__.py help, docs/how-clutch-works.md section 2.1, clutch/docs/host-running.md
- closest existing: `evidence renormalize` (the other store-mutating evidence verb, lock none) and the `_locked` helper used by `index build` and `release`
- earning reason: the removed automatic call needs an explicit, locked, operator-run entry point; no existing verb deletes evidence, and `renormalize` rewrites views only.

## Scope in / Scope out
Scope in:
- `clutch/config.py`: rename `Evidence.max_gb` to `warn_gb` (default 20, still `Count`).
- `clutch/providers.py`: delete the `store.prune(...)` call after the end record in `invoke`; nothing else changes there.
- `clutch/evidence/store.py`: add `EvidenceStore.blob_bytes()` (sum of blob file sizes via the store's `fs` and `size`) and a module function `size_warning(store, warn_gb)` returning the message string or `None`. Do not change `prune`'s behavior.
- `clutch/doctor.py`: add a `warn` flag to `Check`; when `size_warning` returns a message, add a `evidence` row with `passed=True, warn=True`; `render` prints `WARN` for it and `doctor: ok` is unaffected. No row when under the threshold or when the store does not exist. Doctor builds the store over `LocalFileSystem` like its lock probe already uses real disk.
- `clutch/__main__.py`: add the `evidence prune --to-gb N` subcommand through `_command` with Reads, Writes, Lock, Exit codes and examples; add it to the `evidence` group description and epilog; handle it in `handle_evidence` under `_locked(config.state_dir, "evidence prune", ...)`; print the `evidence:` warning line after the status projection in `handle_status`. A unit test runs these lines through `main(..., cwd=tmp_path)` against a store under `tmp_path`, which is the seam; real-disk behaviour needs no allowlisted test.
- `clutch/docs/host-contract.md`: both `max_gb` mentions in the config-fields block become `warn_gb`.
- `docs/how-clutch-works.md`: update the `evidence/` row in section 9 (the sentence about `evidence.max_gb` bounding blobs), the section 10.4 paragraph that says `invoke` calls `prune` after each `end.json` (now: nothing prunes automatically; `evidence prune` is the explicit path; `prune`'s walk rules stay described), the section 11 `evidence.max_gb` row, the section 2.1 verb table (add `evidence prune`, update `host doctor` and `view status` rows), the section 10.3 `view status` list (add the evidence line), and the doctor bullet near the end of section 12.
- `clutch/docs/host-running.md`: add an `evidence prune` verb row (writer lock: stops serve first, so `Works while serve runs?` is `No`), update the `host doctor` and `view status` rows, and add `evidence prune` to the stop-serve sentence listing lock-taking verbs.
- Tests: update `tests/unit/test_evidence_config.py` to the new name; extend the verb set in `tests/unit/test_main_evidence_group.py` with `prune`; add new test files named below.
- Engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them.

- `tests/unit/test_main_view_group.py`: its fake config in `test_dispatch_and_optional_locks` gains `evidence=SimpleNamespace(warn_gb=20)`; `view status` output stays exactly `rendered projection\n` for an empty store under the threshold.
- The `clutch/docs/host-running.md` verb row is written as `| `evidence prune` | No | ... |`: the backticked cell is exactly `group verb` (no `--to-gb N` inside it), as `tests/unit/test_host_running.py::test_verb_table_matches_parser` requires; one row only.
- Before handing off, run the full `./dev.py test`, not only the Verification files.
Scope out:
- No extension, snapshot or `clutch/help.py` surface; the warning is a CLI-only line and row. If an implementer finds the snapshot needs a change, stop and report instead.
- No change to `prune`'s walk rules, blob layout, record schema, training export, or `config.yaml` (it does not set the key).
- No automatic or scheduled prune, no journal event, no config alias for `max_gb`.
- No backup logic; the warning only names `clutch training export --out <dir>`.

Simpler approach rejected: reusing a doctor-only check without `size_warning` leaves status without the line; putting the total into `Status` would add store I/O to the journal projection. The shared function in the store is the minimum that serves both.

## Scope fence
- clutch/config.py
- clutch/providers.py
- clutch/evidence/store.py
- clutch/doctor.py
- clutch/__main__.py
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_evidence_config.py
- tests/unit/test_main_evidence_group.py
- tests/unit/test_evidence_warn_threshold.py
- tests/unit/test_evidence_prune_verb.py
- tests/unit/test_main_view_group.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_evidence_warn_threshold.py` proves that a `CliAdapter.invoke` call run through the `Rig` fake with the store's `size` reporting over `warn_gb` leaves a pre-seeded old blob file present, not removed as the old automatic prune did.
2. `./dev.py test tests/unit/test_evidence_config.py` proves `Evidence().warn_gb == 20`, `Evidence(warn_gb=0)` raises, and `Evidence(max_gb=20)` raises (the old name is not accepted).
3. `./dev.py test tests/unit/test_evidence_warn_threshold.py` proves `host doctor` output has a `WARN evidence:` line naming the size, `evidence.warn_gb`, `clutch training export --out`, and `clutch evidence prune --to-gb` when the blob size exceeds the threshold, still prints `doctor: ok`, and has no `evidence` row when at or under it.
4. `./dev.py test tests/unit/test_evidence_warn_threshold.py` proves `clutch view status` prints exactly one `evidence:` line with the same message when over the threshold and none when under.
5. `./dev.py test tests/unit/test_evidence_prune_verb.py` proves `clutch evidence prune --to-gb 1` over a store larger than 1 GB (sizes faked at the store's size seam) removes the oldest eligible blobs until under the target while every record file remains, leaves a store already under target untouched, refuses a negative `--to-gb` with exit 2, and takes the writer lock (exit 2 when held).
6. `./dev.py test tests/unit/test_main_evidence_group.py` proves the evidence verb set is exactly show, schema, renormalize, coverage, captures, prune and `prune` help carries Reads, Writes, Lock, Exit codes and a `clutch evidence prune` example.
7. `grep -rn "max_gb" clutch tests docs/how-clutch-works.md config.yaml` finds nothing outside tests that assert the old name is refused, and `./dev.py test tests/unit/test_help.py tests/unit/test_main_help.py` pass.
8. `./dev.py test` passes.

## Verification
```
./dev.py test tests/unit/test_evidence_warn_threshold.py tests/unit/test_evidence_prune_verb.py tests/unit/test_evidence_config.py tests/unit/test_main_evidence_group.py tests/unit/test_main_help.py tests/unit/test_help.py
```

## Definition of rejected
- Any code path other than `evidence prune` deletes an evidence blob.
- `max_gb` remains readable, aliased or documented anywhere.
- The warning fails `host doctor` (exit 2) instead of warning.
- The prune verb runs without the writer lock, or its help or docs omit it.
- New tests are added to a hot test file, or an extension or snapshot surface is added.

## Time budget
- expected: 30m
- stuck: 60m
