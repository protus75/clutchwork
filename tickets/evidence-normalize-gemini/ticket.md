---
priority: P3
kind: feature
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: confirmed
---

## Depends on
- evidence-store
- gemini-provider

## Context
- clutch/evidence/codex.py
- clutch/evidence/schema.py::Event
- tickets/gemini-provider/evidence/fact-01-result-event-shape.txt

## Goal / Why
A pure Gemini normalizer turns the raw stdout of one `gemini -o stream-json` call into a list of `clutch.evidence.events/1.0` events, id `gemini-stream/1`. A golden fixture holds one real Gemini stream that has paired tool calls. After this ticket a Gemini call's stream has a normalized view with the same closed event kinds as the Claude and Codex views, and the `result` event reports token buckets on a stated basis. Gemini's `input_tokens` already includes `cached`, and its `input` field is the uncached part. The fixture pins that fact, so Gemini buckets compare with Codex and Claude buckets.

## Scope in / Scope out
Scope in:
- New module `clutch/evidence/gemini.py` with `NORMALIZER_ID = "gemini-stream/1"` and `normalize(stdout: bytes, times_ns: list[int] | None, put_blob: Callable[[bytes], str]) -> list[Event]`, the same signature as `clutch/evidence/codex.py`. It performs no I/O of its own. Large text (message content, tool output) goes through the injected `put_blob`, and events carry only the returned id.
- Mapping is one event per stdout line, in order. `seq` is the 0-based line index. `t_ms` is `times_ns[seq] // 1_000_000`, or 0 when `times_ns` is None. The native line is kept in `native` with the large text removed, as the Codex normalizer does:
  - `init` -> `session_start`.
  - `message` -> `message` with `role` taken from the line (`user` or `assistant`) and `text_blob` from `content`. Each assistant `delta` chunk is its own event; chunks are never joined.
  - `tool_use` -> `tool_call` with `tool` {id: `tool_id`, class from the table below, native: `tool_name`} and `args` equal to `parameters`.
  - `tool_result` -> `tool_result` with the `status` from the line, the `tool` of the `tool_use` that has the same `tool_id`, and `output_blob` from `output` when the key is present, otherwise None. A `tool_result` whose `tool_id` has no earlier `tool_use` gets tool class `other` and native `unknown`.
  - `error` -> `error`.
  - `result` -> `result` with `status` from the line and a `tokens` dict (below).
  - Any other `type` and any line that is not a JSON object -> `unknown`, with the line kept in `native` (a non-JSON line as `{"line": <text>}`). No line is dropped.
- Tool class table, a closed module constant keyed by native tool name: `read_file` -> `read`, `write_file` -> `write`, `run_shell_command` -> `shell`, `update_topic` -> `plan`. Every other tool name maps to `other`; the native name is always kept.
- The `result` event `tokens` dict has keys `input_uncached` (`stats.input`), `input_cache_read` (`stats.cached`), `input_cache_write` (None, Gemini reports none), `output_total` (`stats.output_tokens`), `output_reasoning` (None: the stream does not report thinking tokens, and `total_tokens - input_tokens - output_tokens` also holds tool tokens) and `tokenizer` (`gemini`). A key whose source field is absent is None, never 0. A `result` with no `stats` (the failure shape may omit it) gives all token keys None except `tokenizer`.
- Golden fixture `tests/fixtures/evidence/gemini/stream.jsonl`: the stdout lines of run `t17-tools-yolo-write` in `tickets/gemini-provider/evidence/fact-01-result-event-shape.txt` (gemini-cli 0.49.0, real capture, tracked in the repo), copied byte for byte. It has `update_topic`, `write_file` and `run_shell_command` pairs, three assistant delta chunks, and a `result` with `cached` 8344 and `input` 13638. `tests/fixtures/evidence/gemini/README.md` names the source file, the run id, and the CLI version `0.49.0`.
- Read the fixture and fact-01 for the real field names before writing the mapping.

Scope out: `Parsed`, `GeminiAdapter`, the journal, `CallMeter` and `live_call` are unchanged. No envelope writer, no `evidence` verbs, no renormalize, no CLI-version flagging, no joining of reply chunks, no `-o json` output, and no docs change (the evidence record section lands with the envelope ticket).

## Scope fence
- clutch/evidence/gemini.py
- tests/unit/test_evidence_gemini.py
- tests/integration/test_evidence_gemini_fixture.py
- tests/fixtures/evidence/gemini

## Acceptance criteria
1. An `init` line normalizes to kind `session_start` with `native_type` `init`, never `unknown`; `./dev.py test tests/unit/test_evidence_gemini.py` asserts it.
2. A `message` line with role `assistant` and `delta` true yields kind `message`, role `assistant`, and `text_blob` equal to the id the injected `put_blob` returned for the content, not the content text. Two consecutive assistant chunks yield two events, not one; `./dev.py test tests/unit/test_evidence_gemini.py` asserts both.
3. A `tool_use` of `run_shell_command` yields a `tool_call` of class `shell` with native `run_shell_command`, tool id equal to `tool_id`, and `args` equal to `parameters`. A `tool_use` of `write_file` has class `write`, and of an unlisted name such as `made_up_tool` has class `other`, not `read`. The `tool_result` with the same `tool_id` carries the same tool id, class and native name. A `tool_result` with no `output` key has `output_blob` None and one with `output` "" has a `put_blob` id; `./dev.py test tests/unit/test_evidence_gemini.py` asserts these.
4. A `tool_result` whose `tool_id` was never seen yields tool class `other` and native `unknown`, and does not raise; `./dev.py test tests/unit/test_evidence_gemini.py` asserts it.
5. A `result` line with `stats` of `input_tokens` 100, `cached` 40, `input` 60, `output_tokens` 7 and `total_tokens` 120 yields kind `result`, status `success`, and `tokens` with `input_uncached` 60 (not 100), `input_cache_read` 40, `input_cache_write` None (not 0), `output_total` 7, `output_reasoning` None (not 13) and `tokenizer` `gemini`. A `result` with status `error` and no `stats` yields all token buckets None, not 0; `./dev.py test tests/unit/test_evidence_gemini.py` asserts both.
6. An `error` line yields kind `error`. An unmapped `type`, and a non-JSON line, each yield one `unknown` event with the original content in `native`, and the output has exactly one event per input line; `./dev.py test tests/unit/test_evidence_gemini.py` asserts this.
7. `times_ns=[0, 5_000_000]` gives `t_ms` 0 and 5 on two events, and `times_ns=None` gives 0 on every event. Every returned event passes `Event.model_validate`; `./dev.py test tests/unit/test_evidence_gemini.py` asserts both.
8. The golden fixture normalizes with zero `unknown` events and with `tool_call` and `tool_result` counts equal (3 each). Its `result` event satisfies `input_uncached + input_cache_read == stats.input_tokens` read from the raw fixture line, which pins that Gemini's `input_tokens` includes cached tokens. `./dev.py test tests/integration/test_evidence_gemini_fixture.py` asserts all three.
9. `clutch/evidence/gemini.py` stays at or above the default 90% unit coverage floor from `test-gate.toml`, measured by `./dev.py test tests/unit/test_evidence_gemini.py`.

## Verification
```
./dev.py test tests/unit/test_evidence_gemini.py tests/integration/test_evidence_gemini_fixture.py
```

## Definition of rejected
The fixture is synthetic, edited, or hand-written rather than the real captured stream. A mapped event type falls through to `unknown`. Reply chunks are joined into one event. The normalizer writes to disk or the journal, or edits `GeminiAdapter`, `Parsed` or any other existing file.

## Time budget
- expected: 40m
- stuck: 80m
- reason: one normalizer module, its unit tests and a fixture test share one mapping table and one fixture; splitting would leave a normalizer with no test or a fixture with no reader.
