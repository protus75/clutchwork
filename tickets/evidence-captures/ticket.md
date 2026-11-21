---
state: confirmed
source: human
priority: P3
kind: feature
---

## Depends on
- evidence-verbs

## Context
- clutch/evidence/store.py
- clutch/tickets.py::STEM
- clutch/runner.py::Refusal
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
- `captures(stem, attempt=None)` returns the `(attempt, name)` pairs stored for the stem, sorted by integer attempt then name, or only those of `attempt` when it is given. It skips a directory whose name is not a positive integer and a pointer file whose unquoted name fails the name rule, as `EvidenceStore` already skips non-numeric attempt names; a skipped entry is never an error.
- `clutch evidence captures <stem> [--attempt N] [--name NAME]`: with no options it lists every capture of the stem; with `--attempt N --name NAME` it prints that capture's text.

Every input is validated, each field and every time, by `put_capture`, `get_capture` and `captures` (the verb passes its arguments through them unchanged, so the verb has no validation of its own):

- `stem` must fully match `clutch.tickets.STEM` (the engine's one stem rule, imported, not copied).
- `attempt` must be an `int` that is not a `bool` and is at least 1.
- `name` must fully match `[A-Za-z0-9][A-Za-z0-9._/-]{0,199}`, so a name can hold a stage subpath such as `implement/prompt.md`, and an empty name, a leading `/` or `.`, a space or a control character is refused. The pointer file name is `urllib.parse.quote(name, safe="")` plus `.json`, so a name never adds a path segment.
- a stored pointer must parse as a JSON object, its `schema` must be `clutch.evidence.capture/<major>.<minor>` with major `1`, and its `blob` must be a `sha256:<64 hex>` reference; a pointer failing any of these is unreadable.

The store raises exactly three error types, so a caller can tell the cases apart: `ValueError` for a rejected input field (stem, attempt or name; `captures` validates `attempt` only when it is given); `CaptureNotFound` (a `LookupError`) when `get_capture` finds no pointer file; and `CaptureUnreadable` for anything wrong with stored data: a pointer that is unparsable, is not a JSON object, or fails the schema or blob check, and a blob that is missing or corrupt (the underlying `FileNotFoundError` or `zstd.ZstdError` is wrapped and chained). Both classes are defined in `clutch/evidence/store.py`. Bad input never writes a file and never becomes a path.

## Boundary contract
### Capture store
- disposition: extend
- owner: clutch/evidence/store.py
- consumers: the `evidence captures` handler now; `spools-onto-evidence-store` (row 63) later, which writes captures from `Spool`, reads them in harvest and points the two ask specs here
- observable change: `EvidenceStore` gains `put_capture`, `get_capture` and `captures` as described in Goal / Why. Pointer files live under `<state_dir>/evidence/captures/`, a directory the store never wrote before. Failures: an invalid stem, attempt or name raises `ValueError`; a missing pointer raises `CaptureNotFound`; an unparsable or invalid pointer and a missing or corrupt blob raise `CaptureUnreadable` (the wrapped `FileNotFoundError` or `zstd.ZstdError` from the existing `get_blob` is its `__cause__`). `put_capture` writes the blob before the pointer, so a crash leaves an unreferenced blob, never a pointer without a blob. `EvidenceStore.prune` counts every capture pointer's blob as referenced for the whole pass, so a blob a capture points at is never removed, even when an older call also references the same bytes.
- compatibility: existing calls, attempts, normalized views, blobs and `prune` for calls with no captures behave exactly as before
- acceptance: put then get returns the same bytes; every field is rejected when invalid; prune keeps a captured blob shared with a pruned call
- tests: tests/unit/test_evidence_captures_store.py
- post-merge source of truth: clutch/evidence/store.py

### Evidence captures verb
- disposition: extend
- owner: clutch/__main__.py, the existing `evidence` group
- consumers: operators and, after row 63, the diagnose and running ask specs; `docs/how-clutch-works.md` section 2 and `clutch/docs/host-running.md` verb tables
- observable change: `clutch evidence captures <stem> [--attempt N] [--name NAME]` exists. It reads the store and writes nothing, takes no lock and appends no journal event. Outcomes, each with its exit code and the store error that selects it: `listed` (exit 0) is no `--name` and one line `<attempt> <name>` per pair `captures(stem, attempt)` returns, `--attempt` passed as its second argument; `empty` (exit 0) is no `--name` and no pairs, printing `no captures for <stem>`; `printed` (exit 0) is `--attempt N --name NAME` naming a stored capture, with stdout its text decoded as UTF-8 with `errors="replace"`; `refused-input` (exit 2) is `--name` without `--attempt` (checked by the verb before any store call), or any `ValueError` from the store, including `--attempt 0` or a negative `--attempt` on a listing; `refused-missing` (exit 2) is `CaptureNotFound`, with a refusal message starting `no capture`; `refused-unreadable` (exit 2) is `CaptureUnreadable` or an `OSError` reading the store, with a refusal message starting `unreadable capture`. Every refusal is a `runner.Refusal` rendered by the existing shared handler and `_fail`, so stderr is `clutch evidence: <message> -- <paved road>`: the message follows the unchanged `clutch evidence: ` prefix, and the paved road ends in `clutch evidence captures <stem>` to list what exists, with no traceback. The two messages differ. argparse's own usage errors (a missing stem, a non-integer `--attempt`) also exit 2.
- compatibility: `show`, `schema`, `renormalize` and `coverage` are untouched; `training` is untouched; `_fail` and the shared `runner.Refusal` handler in `main` are untouched, so every other verb's refusal output is unchanged
- acceptance: the parser accepts exactly the five verbs; `captures` carries the `_command` help fields; every outcome name above maps to its exit code in an integration test
- tests: tests/unit/test_main_evidence_group.py and tests/integration/test_evidence_captures_verb.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/evidence/store.py`: add the three methods, the capture-name rule, the pointer schema check, and the `prune` change that counts pointer refs (a base count added before the per-call subtraction loop, never subtracted). Import `STEM` from `clutch.tickets`; the module imports nothing else new beyond what these need. Nothing else in the file changes.
- `clutch/__main__.py`: add the `captures` subcommand to the `evidence` group through `_command` (description, reads, writes, lock, exit codes, example), with the group's description line and epilog example list naming it, and its branch in `handle_evidence`. Build the store as the other branches do; raise `runner.Refusal` for every `refused-*` outcome with the paved road above, and let the existing handler render it. `_fail` and the shared exception handler in `main` stay unchanged. Nothing else in the file changes.
- `clutch/docs/host-running.md` and `docs/how-clutch-works.md`: add one `evidence captures` row after the `evidence coverage` row in the verb table of each (section 2 in the latter). In `docs/how-clutch-works.md` section 10.1, append one sentence to the `evidence/` state-dir row naming `captures/<stem>/<attempt>/<escaped name>.json` pointers to blobs. No other text in either document changes.
- `tests/unit/test_main_evidence_group.py`: the one expectation that changes is the exact verb set, which gains `captures`; add a `captures` row (`["captures", "my-ticket", "--attempt", "2", "--name", "a/b.txt"]`) to the parse table and `["captures"]` and `["captures", "my-ticket", "--attempt", "x"]` to the invalid list. Nothing else there changes.
- New `tests/unit/test_evidence_captures_store.py` (uses `memory_store` from `tests/unit/test_evidence_views.py` and `tmp_path`) and new `tests/integration/test_evidence_captures_verb.py` (uses `CONFIG` from `tests/integration/test_cli.py` like `tests/integration/test_evidence_verbs.py`).
- New `tests/unit/test_main_evidence_captures.py` runs every new `handle_evidence` line (the `__main__.py` unit-coverage floor needs it): it writes `config.yaml` (the `CONFIG` text from `tests/integration/test_cli.py`) into `tmp_path`, stores a capture through `EvidenceStore` with `LocalFileSystem` under `tmp_path`, and calls `main(["evidence", "captures", ...], cwd=tmp_path)` for `listed`, `empty`, `printed` and one `refused-input` case. The full outcome-to-exit-code matrix stays in the integration test. Unit tests cover the new `store.py` lines.

Scope out:
- `_fail`, the shared `runner.Refusal` handler in `main`, and `clutch/runner.py`: the refusal prefix `clutch <verb>: ` is shared by every verb and stays as it is.
- `Spool`, `clutch/driver.py`, harvest, every writer or reader of `spools/`, and the diagnose and running ask prompt specs: `spools-onto-evidence-store` (roadmap row 63) moves them and swaps their `spools/` paths for this verb. Naming the verb in a spec now would point at a store nothing writes.
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
- tests/unit/test_main_evidence_captures.py
- tests/integration/test_evidence_captures_verb.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_evidence_captures_store.py` shows `put_capture` of the text `"error: boom"` followed by `get_capture` returns `b"error: boom"`, a second `put_capture` of the same stem, attempt and name with other text makes `get_capture` return the new bytes (not the old), and `captures(stem)` lists the name once, not twice.
2. The same file shows each method raises `ValueError`, not success, for every one of these invalid fields it takes (`captures` takes the stem and an optional attempt, and validates the attempt whenever it is not `None`): stem `"Bad Stem"`, `""` and `"../x"`; attempt `0`, `-1`, `True` and `"1"`; name `""`, `"/a"`, `".hidden"`, `"a b"`, `"a\nb"`, `".."` and a 201-character name. It also shows no file appears under the store root for a rejected `put_capture`, not a partial pointer.
3. The same file shows a pointer whose `schema` is `clutch.evidence.capture/2.0`, a pointer whose `blob` is `"nope"`, a pointer file holding `[1]` (valid JSON, not an object) and one holding `{` each make `get_capture` raise `CaptureUnreadable`, not `ValueError` and not return bytes, while schema `clutch.evidence.capture/1.3` with a valid `blob` is read. It also shows a stem and attempt with no pointer file raise `CaptureNotFound`, not `CaptureUnreadable`, and a pointer whose blob file was deleted raises `CaptureUnreadable` with a `FileNotFoundError` as its `__cause__`.
4. The same file shows names `implement/prompt.md` and `a.txt` in attempts 2 and 10 come back from `captures` ordered `(2, "a.txt"), (2, "implement/prompt.md"), (10, "a.txt")`, not in string order of the attempt, and that the `implement/prompt.md` pointer file name is `implement%2Fprompt.md.json`, not a nested directory. It also shows `captures(stem, 2)` returns only the attempt-2 pairs, and that a stray directory `abc`, a directory `0` and a pointer file named `%20.json` under the stem are skipped without raising.
5. The same file shows `prune` with a tiny `max_bytes` after a capture whose bytes equal a pruned call's stdout blob keeps the blob and `get_capture` still returns it, not `FileNotFoundError`; and that a blob only an old call references is still pruned.
6. `./dev.py test tests/integration/test_evidence_captures_verb.py` shows each outcome maps to its exit code: `listed` and `empty` and `printed` exit 0 with the expected stdout (the `empty` line is `no captures for <stem>`, not an empty string); `refused-input` (`--name` alone, an invalid stem `Bad Stem`, and `--attempt 0` on a listing), `refused-missing` (no pointer for the named attempt and name) and `refused-unreadable` (a pointer file holding `{"schema": "bad"}`, and a pointer whose blob file was deleted) each exit 2 with stderr starting `clutch evidence: ` and containing ` -- ` and `clutch evidence captures`, and no `Traceback`. For `refused-missing` the stderr text after the `clutch evidence: ` prefix starts with `no capture`, and for `refused-unreadable` it starts with `unreadable capture`, and the two stderr texts differ. It also shows the verb writes no new file and no journal event for any outcome.
7. `./dev.py test tests/unit/test_main_evidence_group.py tests/unit/test_main_help.py` shows the evidence group accepts exactly `show`, `schema`, `renormalize`, `coverage` and `captures`, rejects `captures` with no stem and `--attempt x`, and `captures` carries Reads, Writes, Lock and Exit codes help and an epilog example.
8. `./dev.py test tests/unit/test_main_evidence_captures.py` shows `main(["evidence", "captures", "my-ticket"], cwd=tmp_path)` prints one `<attempt> <name>` line and exits 0 for a stored capture, prints `no captures for my-ticket` and exits 0 for none, `--attempt 1 --name a.txt` prints the stored text, and `--name a.txt` alone exits 2, not 0.
9. `uv run clutch help evidence` lists `captures`; a one-time review check confirms each of `clutch/docs/host-running.md` and `docs/how-clutch-works.md` gained exactly one `evidence captures` table row, that `docs/how-clutch-works.md` also gained exactly one sentence in the section 10.1 `evidence/` row, and no other text in either file changed.

## Verification
```
./dev.py test tests/unit/test_evidence_captures_store.py tests/unit/test_main_evidence_group.py tests/unit/test_main_help.py tests/unit/test_main_evidence_captures.py tests/integration/test_evidence_captures_verb.py tests/integration/test_evidence_verbs.py
```

## Definition of rejected
`put_capture` writes an unredacted blob or a pointer before its blob; any field of stem, attempt (including the optional one in `captures`), name or a stored pointer goes unvalidated or a name becomes a path segment; the store raises a type other than `ValueError`, `CaptureNotFound` or `CaptureUnreadable` for a bad field, a missing pointer or bad stored data; `prune` can remove a blob a capture pointer references; the verb writes a file, takes the lock, appends a journal event or prints a traceback; an outcome exits with a code other than the one named for it; `_fail` or the shared `runner.Refusal` handler changes; `Spool`, harvest, a prompt spec or any `spools/` path changes; a test is added to `tests/integration/test_evidence_verbs.py`; or either verb table or the `evidence/` row is left without its captures text.

## Time budget
- expected: 20m
- stuck: 40m