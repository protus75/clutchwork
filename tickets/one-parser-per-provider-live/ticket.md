---
state: confirmed
source: human
priority: P3
kind: chore
---

## Depends on
- evidence-envelope

## Context
- clutch/observe.py::live_call
- clutch/observe.py::current_step
- clutch/observe.py::text_snapshot
- clutch/evidence/schema.py::Start
- clutch/evidence/store.py::EvidenceStore
- tests/unit/test_live_call.py
- tests/unit/test_live_call_gemini.py

## Goal / Why
`clutch view watch` shows the model call running now from the call's own `start.json` record, not from the provider CLI's command line in the process table (roadmap decision 13, evidence plan row 8, part 3 of `one-parser-per-provider`). Today `live_call` walks the drain's child processes and matches `codex`, `claude`, `node qwen-code` and `node gemini` argv shapes, so every new provider needs a new argv branch. `CliAdapter.invoke` already writes `start.json` before it spawns the provider, with `provider.name` and `model.requested`, so the line becomes provider-neutral and a new provider needs no change here.

## Boundary contract
### Live model line of the watch view
- disposition: replace
- owner: clutch/observe.py
- consumers: `text_snapshot` (`clutch view watch`)
- observable change: `live_call(evidence, stem, surface, began)` returns `<provider.name> <model.requested>` read from the newest `start.json` under `<state>/evidence/calls/` whose key starts with `llm/<stem>/`, whose `surface` equals the running surface, whose `clock.wall_start` is not before `began` (the stage-start timestamp, when not empty), and whose directory has no `end.json`; it returns `""` when none matches or when the `evidence` or `calls` directory does not exist (the state before the first keyed call). The Codex suffix `(reasoning effort <x>)` is dropped, because the line above it already prints the effort asked for.
- compatibility: the `model: <line>` row and its `no model call running` fallback stay. Provider and model names read from the record equal what the argv parse printed for `claude`, `codex`, `qwen` and `gemini` (the record's `model.requested` is the `-m`/`--model` value passed). A keyless call (preflight or probe) leaves no record, so it shows `no model call running`, as the argv parser's `?` rows did not distinguish.
- acceptance: the criteria below
- tests: `tests/unit/test_live_call.py`
- post-merge source of truth: `clutch/observe.py::live_call` over the `clutch.evidence.call/1.0` start record

## Scope in / Scope out
Scope in:
- Rewrite `live_call` in `clutch/observe.py` as described. It reads files with `Path` and `json`, like the rest of `observe.py`, takes the key directory name with `urllib.parse.unquote`, and returns `""` for a missing `evidence` or `calls` directory. It ignores a directory whose `start.json` is unreadable or not valid JSON.
- `text_snapshot` passes `ctx.state / "evidence"` (confirm the path by reading `EvidenceStore`), the running `stem`, `surface` and `began` it already has. The `drains` condition and the process-table helpers (`processes`, `drain_processes`) stay, since the `Drain:` line uses them.
- `tests/unit/test_live_call.py` is rewritten to build start records under `tmp_path` (one JSON file per call directory); `tests/unit/test_live_call_gemini.py` is deleted, its argv cases having no counterpart. New `tests/integration/test_live_call_source.py` holds the source-string check of criterion 6.

Scope out: the process table helpers, `Detector`, `CallMeter`, the vscode extension (it renders the text snapshot's fields it is given), and any docs, which do not describe the argv matching. A call that crashed leaves a `start.json` with no `end.json`; the `began` filter hides one from an earlier step, and cleaning such records up is not part of this ticket.

## Scope fence
- clutch/observe.py
- tests/unit/test_live_call.py
- tests/unit/test_live_call_gemini.py
- tests/integration/test_live_call_source.py

## Acceptance criteria
1. With one open record (`llm/t/1/implement/0/0`, `provider.name` `claude`, `model.requested` `opus`, no `end.json`), `live_call` returns `claude opus`; for `provider.name` `codex` and `gpt` it returns `codex gpt`, with no `reasoning effort` text; `./dev.py test tests/unit/test_live_call.py` asserts both.
2. A call directory holding an `end.json` is not returned, and the function returns `""` rather than the finished call's model; `./dev.py test tests/unit/test_live_call.py` asserts it.
3. With two open records for the stem, the one with the later `clock.wall_start` wins; a record for another stem (`llm/other/...`) and a record whose `surface` differs from the running one are not returned; `./dev.py test tests/unit/test_live_call.py` asserts all three.
4. A record whose `clock.wall_start` is earlier than `began` is not returned; with `began` equal to `""` it is returned; `./dev.py test tests/unit/test_live_call.py` asserts both.
5. A call directory whose `start.json` is truncated JSON is skipped, not raised, and a valid sibling is still returned; `./dev.py test tests/unit/test_live_call.py` asserts it.
6. `clutch/observe.py` no longer contains the strings `cli-entry.js`, `model_reasoning_effort` or `@google/gemini-cli`, and `tests/unit/test_live_call_gemini.py` does not exist; `./dev.py test tests/integration/test_live_call_source.py` asserts both by reading the file.
7. `live_call` on an empty `tmp_path` (no `evidence` directory) returns `""`, not an error; `./dev.py test tests/unit/test_live_call.py` asserts it.
8. The existing watch-view tests still pass with no edit to them: `./dev.py test tests/integration/test_watch.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_live_call.py tests/integration/test_live_call_source.py tests/integration/test_watch.py
```

## Definition of rejected
`live_call` still parses a provider argv or the process table, or a per-provider branch is added. The model line shows a finished call's model. Any file outside the fence, including `tests/integration/test_watch.py`, is edited.

## Time budget
- expected: 20m
- stuck: 40m
