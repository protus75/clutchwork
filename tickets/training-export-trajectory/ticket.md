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

## Context
- clutch/training.py
- clutch/evidence/schema.py
- clutch/evidence/claude.py::normalize
- clutch/evidence/codex.py
- clutch/evidence/gemini.py
- clutch/evidence/store.py::EvidenceStore.read_record
- clutch/evidence/store.py::EvidenceStore.get_blob

## On-demand
- clutch/__main__.py
- tests/unit/test_training_export.py
- tests/unit/test_main_training_group.py

## Goal / Why
Today `clutch training export` writes `implement` records whose target is only the final diff. After this ticket each `implement` record also carries a `trajectory`: the normalized `tool_call` events of the call that produced it, read from that call's stored stdout through the adapter normalizer (`clutch/evidence/claude.py`, `codex.py`, `gemini.py`). `--no-trajectory` omits the field for hosts tuning only review- or triage-style surfaces. The `training_data.exclude` globs (and the fixed always-excluded list, via `effective_exclude()`) drop any tool call whose path argument matches, so excluded paths never reach the export through the trajectory. This is roadmap row 175 and the plan's decision 1 (full normalized trajectory, trimmed by a per-run flag).

## Boundary contract
### Training export record format
- disposition: extend
- owner: clutch/training.py
- consumers: `clutch training export` users and later `training-eval`
- observable change: each `implement` record gains a `trajectory` list of `{seq, tool, native, args}` objects, one per `tool_call` event, in event order, where `seq` is `event.seq`, `tool` is `event.tool.class_` (the tool class), `native` is `event.tool.native` (the provider's tool name string), and `args` is `event.args`. `Event.native` (the raw provider payload, which can carry whole message envelopes) is never exported. The field is absent when `--no-trajectory` is given, when the call's end record or stdout blob is missing, or when the call's adapter is not in the lookup table. `preference` records are unchanged.
- compatibility: existing fields and the `sft.jsonl` / `preference.jsonl` file names are unchanged; the new field is additive.
- acceptance: a tool call whose path argument matches an exclude glob is absent from the trajectory; a record whose trajectory still matches the credential patterns or the redactor is dropped and counted, never partly written.
- tests: new unit test with a fake store and fake normalizer output.
- post-merge source of truth: clutch/training.py

### Training export CLI
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators running `clutch training export`
- observable change: new `--no-trajectory` flag; default behavior includes trajectories.
- compatibility: existing flags and exit codes are unchanged.
- acceptance: the flag reaches `training.render` as a parameter and the verb's help and docs name it.
- tests: parser test in a new test file.
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
In:
- In `clutch/training.py`, add a private helper that reads the call's `end` record via `store.read_record(key, "end")`, loads `raw.stdout` with `store.get_blob`, selects the normalizer from the start record's `provider.adapter` (the adapter class name) through this explicit table: `{"ClaudeAdapter": claude.normalize, "CodexAdapter": codex.normalize, "GeminiAdapter": gemini.normalize}`. `QwenAdapter` is deliberately not in the table (its stream is unverified; `VERIFIED_PROVIDERS` in the claude module holds only claude), so it and any other adapter yield no `trajectory`. Call the normalizer with `times_ns=None` and a non-writing `put_blob` such as `lambda data: hashlib.sha256(data).hexdigest()`, so export never writes blobs into the store. Keep `tool_call` events, build each element as `{seq: event.seq, tool: event.tool.class_, native: event.tool.native, args: event.args}`, never include `Event.native`, and remove events whose `args` path values (keys `file_path`, `path`, `paths`, `notebook_path`) match `config.effective_exclude()` by the same full-path or basename match `_safe` uses. Read the normalizer modules and the fixtures before writing the helper.
- Add a `trajectory=True` parameter to `render`; pass the trajectory into `implement` records for both merged and attempt records.
- In `clutch/__main__.py`, add `--no-trajectory` (`store_false`, dest `trajectory`) to `export` and pass it to `training.render`; extend that command's help text and example.
- Update `docs/how-clutch-works.md` only where it describes training export records, and the `training export` row in `clutch/docs/host-running.md`, to name `--no-trajectory` and the trajectory field.
- In `tests/unit/test_training_export.py`, the only changes are: give the `call()` stand-in a `provider=NS(adapter=...)` attribute, make the `Store` fake's `read_record` raise `FileNotFoundError` when `kind == "end"` (so those tests get no trajectory), and state the expected absence of `trajectory` in the existing implement-record shape assertions. Edit `tests/unit/test_main_training_group.py` only if it pins the export argument set.
Out: new record kinds, `review`/`ticket`/`triage` exports, tool results or reasoning text in the trajectory, changes to normalizers or the evidence schema, and `training eval`.

## Scope fence
- clutch/training.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_training_trajectory.py
- tests/unit/test_training_export.py
- tests/unit/test_main_training_group.py

## Acceptance criteria
1. With a fake store whose call stdout normalizes to one `tool_call` event carrying a raw `Event.native` payload, `training.render(...)` returns an `implement` record whose `trajectory` is exactly `[{seq, tool, native, args}]` with `seq`, `tool` (the class), `native` (the tool name) and `args` equal to the event's values, not a missing or empty `trajectory`, and no element contains the raw payload; checked by `./dev.py test tests/unit/test_training_trajectory.py`.
2. With `trajectory=False`, the `implement` record has no `trajectory` key, not `trajectory: []`; checked by `./dev.py test tests/unit/test_training_trajectory.py`.
3. A `tool_call` whose `args["file_path"]` is `.env.local` or matches a configured `exclude` glob is absent from `trajectory` while a sibling call on `src/app.py` remains, and the record is still written (not dropped); checked by `./dev.py test tests/unit/test_training_trajectory.py`.
4. A trajectory containing a string matching `AKIA` plus 16 alphanumerics causes the whole record to be dropped and counted in `dropped`, never written; checked by `./dev.py test tests/unit/test_training_trajectory.py`.
5. A call whose end record or stdout blob is missing yields a record without `trajectory` and does not raise or count as skipped; checked by `./dev.py test tests/unit/test_training_trajectory.py`.
6. `clutch training export --out X --no-trajectory` parses to `trajectory=False` and omitting the flag parses to `True`; checked by `./dev.py test tests/unit/test_training_trajectory.py`.
7. A call whose `provider.adapter` is `QwenAdapter` (or any name outside the lookup table) yields an `implement` record with no `trajectory` key and no store write; checked by `./dev.py test tests/unit/test_training_trajectory.py`.
8. Existing export, help and docs tests pass; checked by `./dev.py test tests/unit/test_training_export.py tests/unit/test_main_training_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py`.

## Verification
```
./dev.py test tests/unit/test_training_trajectory.py tests/unit/test_training_export.py tests/unit/test_main_training_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py
```

## Definition of rejected
The branch adds a new store, schema or normalizer; includes tool results, reasoning, message text or `Event.native` payloads in the trajectory; writes blobs to the store during export; lets an excluded path appear in an exported trajectory; changes `preference` records; or edits any file outside the fence.

## Time budget
- expected: 20m
- stuck: 40m
