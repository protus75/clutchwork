---
state: draft
source: human
priority: P3
kind: feature
---

## Depends on
- evidence-verbs

## Context
- clutch/evidence/store.py
- clutch/tickets.py::STEM
- tests/unit/test_main_evidence_group.py
- tests/unit/test_evidence_views.py::memory_store
- tests/integration/test_evidence_verbs.py
- docs/roadmap.md#6. Owner decisions (decided 2026-11-13)

## On-demand
- clutch/__main__.py

## Goal / Why
Roadmap row 184, the second of the two slices before `spools-onto-evidence-store` (decision 12, row 63). After this ticket the evidence store can hold a named capture per ticket attempt: a redacted blob plus a pointer file per name, and `clutch evidence captures` lists or prints them. `clutch/specs/ask/diagnose.md` and `clutch/specs/ask/running.md` still send the reader to `<state_dir>/spools/<stem>/`; once `spools-onto-evidence-store` writes captures here, it can swap those paths for this verb. Nothing writes a capture in production yet: `Spool`, harvest, the two prompt specs and every `spools/` path are untouched by this ticket.

The store gains three methods and the verb gains one subcommand:

- `put_capture(stem, attempt, name, data)` redacts and stores `data` as a blob (`put_blob`) and writes the pointer `<state_dir>/evidence/captures/<stem>/<attempt>/<escaped name>.json`, holding `{"schema": "clutch.evidence.capture/1.0", "blob": "<ref>"}`. A second put of the same stem, attempt and name overwrites the pointer.
- `get_capture(stem, attempt, name)` returns the blob bytes.
- `captures(stem)` returns the sorted `(attempt, name)` pairs stored for the stem.
- `clutch evidence captures <stem> [--attempt N] [--name NAME]`: with no options it lists every capture of the stem; with `--attempt N --name NAME` it prints that capture's text.

Every input is validated, each field and every time, by `put_capture`, `get_capture` and `captures` (the verb passes its arguments through them unchanged):

- `stem` must fully match `clutch.tickets.STEM` (the engine's one stem rule, imported, not copied).
- `attempt` must be an `int` that is not a `bool` and is at least 1.
- `name` must fully match `[A-Za-z0-9][A-Za-z0-9._/-]{0,199}`, so a name can hold a stage subpath such as `implement/prompt.md`, and an empty name, a leading `/` or `.`, a space or a control character is refused. The pointer file name is `urllib.parse.quote(name, safe="")` plus `.json`, so a name never adds a path segment.
- a stored pointer's `schema` must be `clutch.evidence.capture/<major>.<minor>` with major `1`, and its `blob` must be a `sha256:<64 hex>` reference; a pointer failing either is unreadable.

A rejected field raises `ValueError`; the verb turns it into a refusal. Bad input never writes a file and never becomes a path.

## Boundary contract
### Capture store
- disposition: extend
- owner: clutch/evidence/store.py
- consumers: the `evidence captures` handler now; `spools-onto-evidence-store` (row 63) later, which writes captures from `Spool`, reads them in harvest and points the two ask specs here
- observable change: `EvidenceStore` gains `put_capture`, `get_capture` and `captures` as described in Goal / Why. Pointer files live under `<state_dir>/evidence/captures/`, a directory the store never wrote before. Failures: invalid stem, attempt, name or pointer raise `ValueError`; a missing pointer raises `FileNotFoundError`; a missing or corrupt blob raises `FileNotFoundError` or `zstd.ZstdError` from the existing `get_blob`. `put_capture` writes the blob before the pointer, so a crash leaves an unreferenced blob, never a pointer without a blob. `EvidenceStore.prune` counts every capture pointer's blob as referenced for the whole pass, so a blob a capture points at is never removed, even when an older call also references the same bytes.
- compatibility: existing calls, attempts, normalized views, blobs and `prune` for calls with no captures behave exactly as before
- acceptance: put then get returns the same bytes; every field is rejected when invalid; prune keeps a captured blob shared with a pruned call
- tests: tests/unit/test_evidence_captures_store.py
- post-merge source of truth: clutch/evidence/store.py

### Evidence captures verb
- disposition: extend
- owner: clutch/__main__.py, the existing `evidence` group
- consumers: operators and, after row 63, the diagnose and running ask specs; `docs/how-clutch-works.md` section 2 and `clutch/docs/host-running.md` verb tables
- observable change: `clutch evidence captures <stem> [--attempt N] [--name NAME]` exists. It reads the store and writes nothing, takes no lock and appends no journal event. Outcomes, each with its exit code: Outcomes, each with its exit code: `listed` (exit 0) is no `--name` and one line `<attempt> <name>` per capture of the stem, in `(attempt, name)` order, optionally narrowed by `--attempt`; `empty` (exit 0) is no `--name` and no captures for the stem or attempt, printing `no captures for <stem>`; `printed` (exit 0) is `--attempt N --name NAME` naming a stored capture, with stdout its text decoded as UTF-8 with `errors="replace"`; `refused-input` (exit 2) is `--name` without `--attempt`, or an invalid stem, attempt or name, and no file is read for it; `refused-missing` (exit 2) is `--attempt N --name NAME` naming a capture with no pointer; `refused-unreadable` (exit 2) is an unreadable store, a pointer failing validation, or a missing or corrupt blob. Every refusal prints the message and a paved road ending in `clutch evidence captures <stem>` to list what exists, with no traceback. argparse's own usage errors (a missing stem, a non-integer `--attempt`) also exit 2.
- compatibility: `show`, `schema`, `renormalize` and `coverage` are untouched; `training` is untouched
- acceptance: the parser accepts exactly the five verbs; `captures` carries the `_command` help fields; every outcome name above maps to its exit code in an integration test
- tests: tests/unit/test_main_evidence_group.py and tests/integration/test_evidence_captures_verb.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/evidence/store.py`: add the three methods, the capture-name rule, the pointer schema check, and the `prune` change that counts pointer refs (a base count added before the per-call subtraction loop, never subtracted). Import `STEM` from `clutch.tickets`; the module imports nothing else new beyond what these need. Nothing else in the file changes.
- `clutch/__main__.py`: add the `captures` subcommand to the `evidence` group through `_command` (description, reads, writes, lock, exit codes, example), with the group's description line and epilog example list naming it, and its branch in `handle_evidence`. Build the store as the other branches do; raise `runner.Refusal` for every `refused-*` outcome with the paved road above. Nothing else in the file changes.
- `clutch/docs/host-running.md` and `docs/how-clutch-works.md`: add one `evidence captures` row after the `evidence coverage` row in the verb table of each (section 2 in the latter). In `docs/how-clutch-works.md` section 10.1, append one sentence to the `evidence/` state-dir row naming `captures/<stem>/<attempt>/<escaped name>.json` pointers to blobs. No other text in either document changes.
- `tests/unit/test_main_evidence_group.py`: the one expectation that changes is the exact verb set, which gains `captures`; add a `captures` row (`["captures", "my-ticket", "--attempt", "2", "--name", "a/b.txt"]`) to the parse table and `["captures"]` and `["captures", "my-ticket", "--attempt", "x"]` to the invalid list. Nothing else there changes.
- New `tests/unit/test_evidence_captures_store.py` (uses `memory_store` from `tests/unit/test_evidence_views.py` and `tmp_path`) and new `tests/integration/test_evidence_captures_verb.py` (uses `CONFIG` from `tests/integration/test_cli.py` like `tests/integration/test_evidence_verbs.py`).
- Unit tests cover the new `store.py` lines; the new `__main__.py` lines are run by the integration test through `main([...], cwd=tmp_path)`.

Scope out:
- `Spool`, `clutch/driver.py`, harvest, `clutch/runner.py`, every writer or reader of `spools/`, and the diagnose and running ask prompt specs: `spools-onto-evidence-store` (roadmap row 63) moves them and swaps their `spools/` paths for this verb. Naming the verb in a spec now would point at a store nothing writes.
- the extension, `clutch/help.py`, the roadmap table and the evidence trail plan.
- the repository README (it lists no evidence verb).
- Overlap with confirmed, unmerged tickets: `spools-scratch-dir` also fences `docs/how-clutch-works.md`, adding a `scratch/` row after the `spools/` row in section 10.1; this ticket edits the `evidence/` row and the section 2 table, so the two edits touch different lines and either merge order keeps both. No other fenced file overlaps `index-config-touches` or `spools-scratch-dir`.

## Scope fence
- clutch/evidence/store.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_main_evidence_group.py
- tests/unit/test_evidence_captures_store.py
- tests/integration/test_evidence_captures_verb.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_evidence_captures_store.py` shows `put_capture` of the text `"error: boom"` followed by `get_capture` returns `b"error: boom"`, a second `put_capture` of the same stem, attempt and name with other text makes `get_capture` return the new bytes (not the old), and `captures(stem)` lists the name once, not twice.
2. The same file shows each method raises `ValueError`, not success, for every one of these invalid fields it takes (`captures` takes only the stem): stem `"Bad Stem"`, `""` and `"../x"`; attempt `0`, `-1`, `True` and `"1"`; name `""`, `"/a"`, `".hidden"`, `"a b"`, `"a\nb"`, `".."` and a 201-character name. It also shows no file appears under the store root for a rejected `put_capture`, not a partial pointer.
3. The same file shows a pointer whose `schema` is `clutch.evidence.capture/2.0` and a pointer whose `blob` is `"nope"` each make `get_capture` raise `ValueError`, not return bytes, while schema `clutch.evidence.capture/1.3` with the same `blob` is read.
4. The same file shows names `implement/prompt.md` and `a.txt` in attempts 2 and 10 come back from `captures` ordered `(2, "a.txt"), (2, "implement/prompt.md"), (10, "a.txt")`, not in string order of the attempt, and that the `implement/prompt.md` pointer file name is `implement%2Fprompt.md.json`, not a nested directory.
5. The same file shows `prune` with a tiny `max_bytes` after a capture whose bytes equal a pruned call's stdout blob keeps the blob and `get_capture` still returns it, not `FileNotFoundError`; and that a blob only an old call references is still pruned.
6. `./dev.py test tests/integration/test_evidence_captures_verb.py` shows each outcome maps to its exit code: `listed` and `empty` and `printed` exit 0 with the expected stdout (the `empty` line is `no captures for <stem>`, not an empty string); `refused-input` (`--name` alone, and an invalid stem `Bad Stem`), `refused-missing` and `refused-unreadable` (a pointer file holding `{"schema": "bad"}`, and a pointer whose blob file was deleted) each exit 2 with stderr containing ` -- ` and `clutch evidence captures`, and no `Traceback`. It also shows the verb writes no new file and no journal event for any outcome.
7. `./dev.py test tests/unit/test_main_evidence_group.py tests/unit/test_main_help.py` shows the evidence group accepts exactly `show`, `schema`, `renormalize`, `coverage` and `captures`, rejects `captures` with no stem and `--attempt x`, and `captures` carries Reads, Writes, Lock and Exit codes help and an epilog example.
8. `uv run clutch help evidence` lists `captures`; a one-time review check confirms each of `clutch/docs/host-running.md` and `docs/how-clutch-works.md` gained exactly one `evidence captures` table row, that `docs/how-clutch-works.md` also gained exactly one sentence in the section 10.1 `evidence/` row, and no other text in either file changed.

## Verification
```
./dev.py test tests/unit/test_evidence_captures_store.py tests/unit/test_main_evidence_group.py tests/unit/test_main_help.py tests/integration/test_evidence_captures_verb.py tests/integration/test_evidence_verbs.py
```

## Definition of rejected
`put_capture` writes an unredacted blob or a pointer before its blob; any field of stem, attempt, name or a stored pointer goes unvalidated or a name becomes a path segment; `prune` can remove a blob a capture pointer references; the verb writes a file, takes the lock, appends a journal event or prints a traceback; an outcome exits with a code other than the one named for it; `Spool`, harvest, a prompt spec or any `spools/` path changes; a test is added to `tests/integration/test_evidence_verbs.py`; or either verb table or the `evidence/` row is left without its captures text.

## Time budget
- expected: 20m
- stuck: 40m
