---
state: confirmed
source: human
priority: P3
kind: chore
---

## Depends on
- evidence-captures

## Context
- clutch/evidence/store.py
- clutch/driver.py::Spool
- clutch/requisition.py
- clutch/tickets.py::STEM
- tests/unit/test_evidence_captures_store.py
- tests/unit/test_evidence_views.py::memory_store
- docs/roadmap.md#6. Owner decisions (decided 2026-11-13)

## On-demand
- clutch/__main__.py

## Goal / Why
Roadmap row 185, the key half of row 63's split (decision 12). `spools-onto-evidence-store` will move `Spool` onto `EvidenceStore.put_capture`, but the store rejects what `Spool` emits today. `Spool.write(stem, attempt, name, text)` is called with these forms, all read from the code:

- `stem` is a ticket stem (`my-ticket`, attempt `0` for merge and check host logs in `clutch/stages.py`, the run sequence for stage calls) or, for a ticketless stage, the surface name (`work`, `semantic`, `review_visual`: lowercase letters, digits, `_` and `-`).
- `stem` is `<stem>/<run_seq>` when `Driver` is given a `run_seq` (`work/1`) and in `clutch/requisition.py` (`author/8`, whose attempt is `0`); `clutch/__main__.py` uses `review-<stem>` as that slot, so it can exceed the 64 characters `STEM` allows.
- `attempt` is `0` for merge and ticketless spools.
- `name` is a relative path such as `implement/call-01/prompt.md`, `merge-integration/verify-01.txt` or `requisition_review/call-01/output.txt`.

The store refuses attempt `0` and every stem with `/` or `_`. After this ticket the store accepts them, and one function `capture_key(spool_stem, attempt, name)` in `clutch/evidence/store.py` maps every spool form above to a valid capture key `(stem, attempt, name)`. The `run_seq` of `<stem>/<run_seq>` moves into the name as a leading `run-<run_seq>/` segment, so the key shape stays `(stem, attempt, name)` and the on-disk layout `captures/<stem>/<attempt>/<escaped name>.json` does not change. Example: `capture_key("author/8", 0, "requisition_review/call-01/prompt.md")` returns `("author", 0, "run-8/requisition_review/call-01/prompt.md")`, and `capture_key("my-ticket", 0, "merge/host-01.txt")` returns `("my-ticket", 0, "merge/host-01.txt")`. Nothing calls `capture_key` yet: `Spool`, harvest and `spools/` are untouched, and `spools-onto-evidence-store` becomes its one production caller for every write and read of a spool file (so a write and a lookup cannot derive different keys).

Every field of a capture key is validated by `put_capture`, `get_capture` and `captures`, each time; the rules after this ticket are:

- `stem` must be a `str` that fully matches `[a-z0-9][a-z0-9_-]{1,127}`. This is a superset of `clutch.tickets.STEM`, kept in the store because a capture stem also names a ticketless surface (`_`) and a `review-<stem>` slot (over 64 characters), neither of which `STEM` admits.
- `attempt` must be an `int` that is not a `bool` and is at least 0 (it was at least 1). `captures` validates it only when it is not `None`, and skips a stored directory whose name is not an ASCII decimal number, now keeping `0`.
- `name` must fully match `[A-Za-z0-9][A-Za-z0-9._/-]{0,199}` (unchanged). The pointer file name is still `urllib.parse.quote(name, safe="")` plus `.json`.
- a stored pointer: unchanged (JSON object, schema `clutch.evidence.capture/1.x`, `blob` a `sha256:<64 hex>` reference).

`capture_key` has these named outcomes. `mapped` returns the key tuple. `refused-spool-stem` raises `ValueError` when `spool_stem` is not a `str` or is empty, has more than one `/`, or its part before the `/` fails the stem rule. `refused-run-seq` raises `ValueError` when the part after the `/` is not `0` or a decimal number with no leading zero of at most 9 digits (`run_seq` is never negative, never `01`, never non-ASCII digits). `refused-attempt` raises `ValueError` for an attempt that is a `bool`, not an `int`, or below 0. `refused-name` raises `ValueError` when the folded name fails the name rule, including a name that was valid before `run-<run_seq>/` was added but is over 200 characters after, and any name that itself starts with `run-` followed by one or more ASCII digits and `/` (checked on the input name, whether or not the stem carries a run sequence), because it could not be told apart from a folded one. The key `capture_key` returns always passes the store's own validation, so `put_capture(*capture_key(...), data)` never raises `ValueError` for a mapped key.

`clutch evidence captures` help states the new attempt floor and that a spool slot's run sequence appears as a leading `run-<n>/` in the name; its behavior is unchanged (it passes arguments through to the store, so `--attempt 0` on a listing now succeeds).

## Boundary contract
### Capture key rules
- disposition: extend
- owner: clutch/evidence/store.py
- consumers: `put_capture`, `get_capture`, `captures`, the `evidence captures` handler in `clutch/__main__.py`; `spools-onto-evidence-store` (row 63) later
- observable change: `_validate_capture` accepts attempt `0` and stems matching `[a-z0-9][a-z0-9_-]{1,127}`; `captures` lists attempt directory `0`. A stem with `/`, a capital, a leading `-` or `_`, or over 128 characters, and an attempt that is negative, a `bool` or not an `int`, still raise `ValueError` and never write a file. Every previously valid key stays valid and keeps its file path.
- compatibility: all keys valid before this ticket map to the same pointer paths; nothing is stored or read in production yet, so no stored data migrates; `put_blob`, `prune`, `CaptureNotFound` and `CaptureUnreadable` are untouched
- acceptance: criteria 1 and 2 below
- tests: tests/unit/test_evidence_captures_store.py and tests/unit/test_evidence_capture_keys.py
- post-merge source of truth: clutch/evidence/store.py

### Spool-to-capture key mapping
- disposition: create
- owner: clutch/evidence/store.py (`capture_key`)
- consumers: `spools-onto-evidence-store` (row 63), the only production caller, for `Spool.write` and for harvest and every other reader of spool files; this ticket has no production caller
- observable change: the new function `capture_key(spool_stem, attempt, name)` returns `(stem, attempt, name)` as the Goal states, raises `ValueError` for the four refused outcomes, and has no side effect and no I/O
- closest existing: `Spool.write` in `clutch/driver.py` builds `<root>/<stem>/<attempt>/<name>` by string joining and validates nothing; `EvidenceStore._validate_capture` validates a finished key but cannot split a spool stem or fold a `run_seq`
- earning reason: two production paths (write in `Spool`, read in harvest, retro and the ask specs' verb) must derive the same key from the same spool stem; one shared function is the only way both agree, and a second inline split in either would drift
- compatibility: new function; no existing caller
- acceptance: criterion 3 and 4 below
- tests: tests/unit/test_evidence_capture_keys.py
- post-merge source of truth: clutch/evidence/store.py

### Evidence captures verb help
- disposition: extend
- owner: clutch/__main__.py (`captures` through `_command`)
- consumers: operators reading `clutch help evidence captures`
- observable change: the `captures` description names the attempt floor of 0 and the leading `run-<n>/` name segment; the verb's outcomes, exit codes and refusals are unchanged
- compatibility: `--attempt 0` on a listing was exit 2 (`refused-input`) and is now exit 0 (`listed` or `empty`); every other outcome is unchanged
- acceptance: criterion 5 below
- tests: tests/integration/test_evidence_captures_verb.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/evidence/store.py`: replace the stem and attempt rules in `_validate_capture` as the Goal states and drop the `STEM` import if nothing else in the file uses it; change the attempt-directory skip in `captures` from `< 1` to `< 0`; add the module-level function `capture_key` and the stem rule it shares with `_validate_capture` (one compiled pattern, used by both). Nothing else in the file changes.
- `clutch/__main__.py`: only the `does` text (and example if it helps) of the `captures` `_command`, to state the attempt floor and the `run-<n>/` name segment. Nothing else in the file changes.
- `tests/unit/test_evidence_captures_store.py`: the expectations that flip. In the invalid-field table attempt `0` leaves the invalid list (attempt `-1`, `True` and `"1"` stay) and stems with `_` are added to valid cases (a stem with `/` stays invalid: `capture_key` folds the slash away before the store sees the stem); the `captures` listing case that wrote `0/a.json` and expected it skipped now expects `(0, "a")` listed, and a `-1` directory is the skipped one. Nothing else there changes.
- `tests/integration/test_evidence_captures_verb.py`: the `["my-ticket", "--attempt", "0"]` case exits 2 with `invalid capture input` today and now exits 0 as `empty`; replace it with `--attempt -1` for the `refused-input` case and add the `--attempt 0` empty case and one `--help` assertion (catch `SystemExit` as `tests/unit/test_main_help.py` does). Nothing else there changes.
- New `tests/unit/test_evidence_capture_keys.py` (uses `memory_store` from `tests/unit/test_evidence_views.py`) for `capture_key` and the new key forms.

Scope out:
- The shipped host run guide and the architecture document: their `evidence captures` rows and the `evidence/` state-dir row say "by attempt and name" and name the pointer layout, which does not change; neither states the old attempt or stem rule (grep for `attempt`, `stem` and `captures`), so neither is edited or fenced. That document is fenced by running `serve-polls-block-parallel-runs` and queued `meta-drift-lint`; leaving it out keeps this ticket independent of both. `spools-onto-evidence-store` and row 186 document the `spools/` swap.
- `Spool`, `clutch/driver.py`, `clutch/requisition.py`, `clutch/stages.py`, harvest in `clutch/runner.py`, `clutch/retro.py`, the ask prompt specs and every `spools/` path: `spools-onto-evidence-store` moves them. This ticket adds no call to `capture_key`.
- `prune`, `put_blob`, pointer schema and error classes.
- `clutch/help.py`: `captures` is a CLI help entry owned by the parser.
- Overlap with unmerged tickets: `serve-polls-block-parallel-runs` (`clutch/serve.py`, `clutch/daemon.py` and the architecture document), `meta-drift-lint` (`clutch/gates.py`, `clutch/stages.py`, gate tests) and `index-build-r2` (`clutch/index.py` and its tests) share no fenced file with this ticket, so merge order does not matter.

## Scope fence
- clutch/evidence/store.py
- clutch/__main__.py
- tests/unit/test_evidence_captures_store.py
- tests/unit/test_evidence_capture_keys.py
- tests/integration/test_evidence_captures_verb.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_evidence_captures_store.py` shows `put_capture` then `get_capture` round-trips for stems `work`, `review_visual` and a 100-character stem and for attempt `0` and `1`, and `captures("work")` lists attempt `0` as `(0, name)`, not skipped. The same file shows `ValueError`, not success, with no file written, for stem `"Bad Stem"`, `""`, `"../x"`, `"a/b"`, `"_x"`, `"-x"` and a 129-character stem, and for attempt `-1`, `True`, `False`, `"1"` and `1.0`, each through `put_capture`, `get_capture` and `captures`; a directory named `-1` or `abc` under a stem is skipped without raising.
2. The same file shows every unchanged name rule still raises `ValueError` (`""`, `"/a"`, `".hidden"`, `"a b"`, `"a\nb"`, `".."`, a 201-character name), and a previously valid key (`my-ticket`, `1`, `implement/prompt.md`) keeps the pointer path `captures/my-ticket/1/implement%2Fprompt.md.json`, not a new one.
3. `./dev.py test tests/unit/test_evidence_capture_keys.py` shows `mapped` for each emitted form: `capture_key("my-ticket", 0, "merge/host-01.txt")` returns `("my-ticket", 0, "merge/host-01.txt")`; `capture_key("my-ticket", 1, "implement/call-01/prompt.md")` is unchanged; `capture_key("semantic", 0, "merge-integration/verify-01.txt")` and `capture_key("review_visual", 2, "review_visual/call-01/output.txt")` are unchanged; `capture_key("work", 1, "render/a.txt")` is unchanged; `capture_key("work/1", 1, "review/call-01/output.txt")` returns `("work", 1, "run-1/review/call-01/output.txt")`; `capture_key("author/8", 0, "requisition_review/call-01/prompt.md")` returns `("author", 0, "run-8/requisition_review/call-01/prompt.md")`; `capture_key("review-" + 64-char-stem, 0, "x")` maps to a key `put_capture` accepts. Each result, passed to `put_capture` then `get_capture` on `memory_store`, returns the stored bytes, and `captures(stem)` lists the folded name, not the unfolded one.
4. The same file shows each refused outcome raises `ValueError` and writes nothing: `refused-spool-stem` for `""`, `"a/b/c"`, `"/8"`, `"Work/1"`, `None` and `5`; `refused-run-seq` for `"author/"`, `"work/01"`, `"work/-1"`, `"work/x"`, `"work/1234567890"` and a non-ASCII digit; `refused-attempt` for `-1`, `True` and `"0"`; `refused-name` for `""`, `"/a"`, a name of 200 characters under `work/1`, and a name that itself starts with `run-` followed by digits and `/` (for example `"run-1/a.txt"` under stem `work`, which would collide with the folded form of `work/1`), not a returned key. It also shows `work/0` maps to `("work", a, "run-0/<name>")`, not the unfolded `work`, and that `work/1` and `work/2` with the same name and attempt map to different keys.
5. `./dev.py test tests/integration/test_evidence_captures_verb.py` shows `clutch evidence captures my-ticket --attempt 0` exits 0 printing `no captures for my-ticket`, not exit 2, `--attempt -1` exits 2 with `invalid capture input`, and `main(["evidence", "captures", "--help"])` prints help containing `run-` and `attempt 0`.
6. `./dev.py test tests/unit/test_main_evidence_captures.py tests/integration/test_evidence_verbs.py` still passes unchanged, not edited; a one-time review check confirms `git diff` of this ticket touches no file outside the fence and adds no caller of `capture_key` outside tests.

## Verification
```
./dev.py test tests/unit/test_evidence_captures_store.py tests/unit/test_evidence_capture_keys.py tests/unit/test_main_evidence_captures.py tests/unit/test_main_help.py tests/unit/test_help.py tests/integration/test_evidence_captures_verb.py tests/integration/test_evidence_verbs.py
```

## Definition of rejected
The store accepts a negative or `bool` attempt, a stem with `/`, a capital or a leading `-` or `_`, or any unvalidated field; `capture_key` returns a key the store then refuses, or drops or merges `run_seq` so two run sequences share a key; a second function or inline split derives a capture key from a spool stem; `Spool`, harvest, a prompt spec, a `spools/` path or a doc file changes; a file outside the fence changes; or a previously valid key changes its pointer path.

## Time budget
- expected: 15m
- stuck: 30m
