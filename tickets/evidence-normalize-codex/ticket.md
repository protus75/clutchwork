---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- evidence-store

## Context
- clutch/evidence/schema.py
- docs/evidence-trail-plan.md

## Goal / Why
A pure Codex normalizer turns the raw stdout of one `codex exec --json` call into a list of `clutch.evidence.events/1.0` events, id `codex-stream/1`. A golden fixture holds one redacted real Codex stream. The fixture pins whether Codex's `input_tokens` already includes `cached_input_tokens`, a fact nothing in clutch pins today. The journaled token totals may mix two scales because Claude's `input_tokens` is the sum of its three input buckets while Codex's is the raw value. The normalized `usage` event reports `input_uncached` on a stated basis, so Codex and Claude buckets can be compared.

## Scope in / Scope out
Scope in:
- New module `clutch/evidence/codex.py` with `NORMALIZER_ID = "codex-stream/1"` and `normalize(stdout: bytes, times_ns: list[int] | None, put_blob: Callable[[bytes], str]) -> list[Event]`. It performs no I/O of its own. Large text (agent message text, command output, reasoning text) goes through the injected `put_blob`, which returns a `sha256:` id. Events carry only that id.
- Mapping, one JSON object per stdout line, in order; `seq` is the 0-based line index and `t_ms` is `times_ns[i] // 1_000_000`, or 0 when `times_ns` is None:
  - `thread.started` -> `session_start`.
  - `item.started` of a `command_execution` item -> `tool_call` with tool class `shell` and native `command_execution`. The tool id is the item id, and `args` holds the command.
  - `item.completed` of a `command_execution` item -> `tool_result` with `status` and `output_blob`.
  - `item.completed` of a `file_change` item -> `file_change`.
  - `item.completed` of an `agent_message` item -> `message` with role `assistant` and `text_blob`.
  - `item.completed` of a reasoning item -> `reasoning`, with visibility `summary` and `text_blob` when the item carries text, otherwise `count_only`.
  - `turn.completed` -> one `usage` event.
  - `turn.failed` and `error` -> `error`.
  - `turn.started`, any unmapped event or item type, and any line that is not a JSON object -> `unknown`, with the event kept in `native` (a non-JSON line as `{"line": <text>}`). No line is dropped.
- The `usage` event `tokens` dict has keys `input_uncached`, `input_cache_read`, `input_cache_write`, `output_total`, `output_reasoning` and `tokenizer` (value `openai-o200k`). A key whose source field is absent is `None`, never 0. `input_cache_read` is `cached_input_tokens` and `input_cache_write` is `cache_write_input_tokens`. `input_uncached` follows one module constant, `INPUT_INCLUDES_CACHED`, set from what the fixture shows. When it is true, `input_uncached = input_tokens - cached_input_tokens`; when it is false, `input_uncached = input_tokens`.
- The golden fixture is one real Codex stream taken from the provider captures. Those captures are untracked runtime state in the main checkout's state dir at `<state_dir>/spools/providers/`, so they are not inside the ticket worktree; under the default `worktree_root` that directory is `../../spools/providers/` relative to the worktree. A known-good source is `spools/providers/phase3-continue-14/codex-0006/events.jsonl` there (80 lines, with `command_execution` items, `agent_message` items and a `turn.completed` whose `cached_input_tokens` is greater than 0). Any other `events.jsonl` that contains `command_execution` items and a `turn.completed` with `cached_input_tokens` > 0 also qualifies. Copy it and redact secrets and host-private paths. It is stored at `tests/fixtures/evidence/codex/stream.jsonl` with `tests/fixtures/evidence/codex/README.md` naming the CLI version it covers (read from `codex --version` output in the stream or capture when present, otherwise recorded as `unknown`). Set `INPUT_INCLUDES_CACHED` to false only if some `turn.completed` in the fixture has `cached_input_tokens` greater than `input_tokens`; otherwise set it to true.
- Read the fixture for the real field names before writing the mapping.

Scope out: `Parsed`, the journal and `CallMeter` are unchanged. If the fixture shows that the journaled `input_tokens` mix scales, name that in the run record and file it with `clutch suggest` as a bug against `Parsed`; do not fix it here. No envelope writer, no `evidence` verbs, no renormalize, no CLI-version coverage flagging, and no docs change (the evidence record section lands with the envelope ticket).

## Scope fence
- clutch/evidence/codex.py
- tests/unit/test_evidence_codex.py
- tests/integration/test_evidence_codex_fixture.py
- tests/fixtures/evidence/codex

## Acceptance criteria
1. A `thread.started` line normalizes to an event with kind `session_start` and `native_type` `thread.started`; `./dev.py test tests/unit/test_evidence_codex.py` asserts this and that the result is never `unknown`.
2. An `item.started` `command_execution` line yields a `tool_call` whose tool class is `shell` (not `read`) with native `command_execution` and tool id equal to the item id. The matching `item.completed` yields a `tool_result` whose `output_blob` is the id returned by the injected `put_blob` for the output text, not the text itself; `./dev.py test tests/unit/test_evidence_codex.py` asserts both.
3. A `turn.completed` line with `input_tokens` 100, `cached_input_tokens` 40 and `output_tokens` 7, and no `cache_write_input_tokens`, yields a `usage` event whose `tokens` has `input_cache_read` 40, `input_cache_write` `None` (not 0), `output_total` 7 and `input_uncached` set per `INPUT_INCLUDES_CACHED` (60 when true, 100 when false); `./dev.py test tests/unit/test_evidence_codex.py` asserts it, and a stream with no `reasoning_output_tokens` gives `output_reasoning` `None`.
4. A line with an unmapped event type, a `turn.started` line, and a non-JSON line each yield one `unknown` event with the original content in `native`; the output has exactly one event per input line, checked by `./dev.py test tests/unit/test_evidence_codex.py`.
5. `times_ns=[0, 5_000_000]` gives `t_ms` 0 and 5 on two events, and `times_ns=None` gives 0 on every event; every returned event passes `Event.model_validate`; `./dev.py test tests/unit/test_evidence_codex.py` asserts both.
6. The golden fixture normalizes with zero events of kind `unknown` caused by a mapped native type (`thread.started`, `item.*` of the mapped item types, `turn.completed`, `error`, `turn.failed`). The test also asserts that, for every `turn.completed` in the fixture, `INPUT_INCLUDES_CACHED` is consistent with the data (when true, `cached_input_tokens` <= `input_tokens`), and that the `usage` event's `input_uncached` equals the value that constant implies. It runs with `./dev.py test tests/integration/test_evidence_codex_fixture.py`.
7. `clutch/evidence/codex.py` stays at or above the default 90% unit coverage floor from `test-gate.toml`, measured by `./dev.py test tests/unit/test_evidence_codex.py`.

## Verification
```
./dev.py test tests/unit/test_evidence_codex.py tests/integration/test_evidence_codex_fixture.py
```

## Definition of rejected
The fixture is synthetic or hand-written rather than a redacted real Codex stream, or `INPUT_INCLUDES_CACHED` is set without a test tied to the fixture data. A mapped event type falls through to `unknown`. The normalizer writes to disk or the journal, or edits `Parsed`.

## Time budget
- expected: 45m
- stuck: 90m
