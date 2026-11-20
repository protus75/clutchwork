---
state: draft
source: human
priority: P3
kind: chore
---

## Depends on
- evidence-normalize-codex
- evidence-normalize-claude
- evidence-normalize-gemini

## Context
- clutch/providers.py::Parsed
- clutch/providers.py::CliAdapter
- clutch/providers.py::ClaudeAdapter
- clutch/providers.py::CodexAdapter
- clutch/providers.py::GeminiAdapter
- clutch/evidence/claude.py
- clutch/evidence/codex.py
- clutch/evidence/gemini.py
- clutch/evidence/schema.py::Event
- docs/evidence-trail-plan.md#Ticket breakdown
- tests/unit/test_gemini_adapter.py
- tests/unit/test_qwen_adapter.py

## Goal / Why
`Parsed`, the result of one provider call, is built from the call's normalized `clutch.evidence.events/1.0` events by one function, so the per-provider `parse` methods of `ClaudeAdapter`, `CodexAdapter` and `GeminiAdapter` are deleted (roadmap decision 13, evidence plan row 8). Today each stream is read twice, once by the adapter parser and again by the normalizers; after this ticket the normalizers are the only code that knows a provider's stream shape for the result, text, tokens, cost and served model. This is the first of three parts: `one-parser-per-provider-meter` moves `CallMeter` and `one-parser-per-provider-live` moves `live_call`; both are listed in `docs/roadmap.md` row 64's work and neither is dropped.

Normalized events lack four facts `Parsed` needs, so the normalizers add them within schema `clutch.evidence.events/1.0` (optional fields, no version change): the call's final reply text, the call's outcome, the USD cost, and the served model. `Parsed.input_tokens` is the sum of the non-None input buckets of the closing event (Claude: `input_tokens` + cache creation + cache read; Codex: `input_tokens` already includes cached, so uncached + cache read; Gemini: `input` + `cached`), which equals the old values for all three providers once the Codex normalizer treats an absent `cached_input_tokens` as 0 (below).

The roadmap row also says to wait for "a release of real traffic and a coverage report"; `evidence-verbs` (row 62, `evidence coverage`) is not merged, so this ticket proves equivalence on every stream the existing parser tests and the three golden fixtures hold instead. The owner decides when to confirm it.

## Boundary contract
### Provider result parsing
- disposition: replace
- owner: clutch/providers.py
- consumers: `CliAdapter.invoke`, `CliAdapter.parsed_failure`, the end record's `parsed` block
- observable change: `ClaudeAdapter`, `CodexAdapter` and `GeminiAdapter` lose their `parse` overrides; `CliAdapter.parse(out)` becomes the single concrete implementation, which normalizes `out` with the adapter's `normalizer` and returns `Parsed` from the events. `Parsed` fields and the `ValueError` contract (a stream with no successful result raises `ValueError` naming the failure) are unchanged.
- compatibility: for every stream in the existing adapter, probe and failure-classifier tests, and in the three golden fixtures, `Parsed` equals what the old parser returned and each failure keeps its `failure_class`, with two deliberate exceptions: a Codex stream with an `agent_message` but no `turn.completed` now fails closed (a real Codex call that ends without `turn.completed` is a failed call, and its exit code is non-zero), and a Claude `tool_use` block with no `name` is not a stream the Claude normalizer accepts (the CLI always sends one). The two preflight tests and the qwen test that fed those shapes are fixed in this change. The old `parse` overrides are removed in the same change, with no dual path.
- acceptance: the criteria below
- tests: `tests/unit/test_provider_parsed_events.py`, `tests/integration/test_provider_parsed_fixtures.py`, the unchanged `tests/unit/test_gemini_adapter.py` and `tests/integration/test_providers.py`, and the edited `tests/unit/test_qwen_adapter.py`, `tests/unit/test_preflight_parallel.py` and `tests/unit/test_preflight_latest_lookup.py`
- post-merge source of truth: `clutch/providers.py` for `Parsed` and the closing-event rule; `clutch/evidence/<provider>.py` for what each stream's closing event carries

### Normalized event fields
- disposition: extend
- owner: clutch/evidence/schema.py
- consumers: the three normalizers, `CliAdapter.parse`, later `CallMeter` (`one-parser-per-provider-meter`)
- observable change: `Event` gains optional `usd: float | None = None` and `model: str | None = None`. Claude's `result` event, Codex's `turn.completed` event and Gemini's `result` event also set `status` and `text_blob` as Scope in states; `Codex` and `Gemini` `error` events set `text_blob`.
- compatibility: additive and optional; no record is written with a `normalized/` view yet, so no stored data changes, and `clutch.evidence.events/1.0` stays the schema id. Existing normalizer assertions stay true.
- acceptance: criteria 1-4
- tests: `tests/unit/test_evidence_claude.py`, `tests/unit/test_evidence_codex.py`, `tests/unit/test_evidence_gemini.py`, `tests/unit/test_provider_parsed_events.py`
- post-merge source of truth: `clutch/evidence/schema.py::Event`

## Scope in / Scope out
Scope in:
- `Event` in `clutch/evidence/schema.py` gains `usd: float | None = None` and `model: str | None = None`.
- The closing event is the last event of kind `result`, or of kind `usage`, whose `status` is not None. Each normalizer sets on it:
  - `status`: `success` or `error`. Claude's `result` event: `success` when `subtype` is `success` and `is_error` is not true, else `error`. Codex's `turn.completed`: `success` unless a `turn.failed` or `error` line came earlier in the stream, then `error`. Gemini's `result`: `success` when the line's `status` is `success`, else `error`.
  - `text_blob`: on `success`, the final reply text through `put_blob`. Claude: the `result` field (`""` when absent). Gemini: every assistant `message` content joined in order (`""` when none). Codex: the text of the last `agent_message` item before it, and None when there was none. On `error`, the failure message: Claude the `result` field; Gemini `error.message`, else the last earlier `error` line's `message`, else the line's `status`; Codex the last earlier error message.
  - `usd`: Claude's `total_cost_usd`; None for the others.
  - `model`: Gemini's only key of `stats.models` when exactly one, else None; None for the others.
- Codex `turn.completed` with `input_tokens` but no `cached_input_tokens` sets `input_uncached` to `input_tokens` (cached counts as 0) instead of None, so `Parsed.input_tokens` stays the old total; with no `input_tokens` it stays None. The one assertion in `tests/unit/test_evidence_codex.py` that expects None for `missing_cache` changes to 100.
- `tests/unit/test_qwen_adapter.py::test_parse_recorded_stream`: give its `tool_use` block a `name` and an `input`. `tests/unit/test_preflight_parallel.py` and `tests/unit/test_preflight_latest_lookup.py`: add a `turn.completed` line (with `usage` input and output counts) after the `agent_message` in each fake Codex stream, with the expected probe results unchanged.
- Codex's `turn.failed` and `error` events and Gemini's `error` events get `text_blob` of the error message (`error.message` for `turn.failed`, `message` otherwise), so a stream with no closing event still names its failure. The normalizers keep one event per line and every other mapping unchanged; `NORMALIZER_ID` values stay.
- `clutch/providers.py`:
  - A new module-level `parsed_from_events(events, read_blob) -> Parsed`, where `read_blob(id) -> bytes`. It raises `ValueError` when no closing event exists (message `no terminal result event in the stream`, preceded by the last `error` event's text when one exists), when the closing `status` is `error` (message `<status>: <text>`), or when a `success` closing event has no `text_blob`. Otherwise `Parsed.text` is the blob text, `input_tokens` is the sum of the non-None `input_uncached`, `input_cache_read` and `input_cache_write` of the closing event's `tokens` (the `usage` event of the same line for Claude, whose tokens sit on the `usage` event just before `result`), None when all are None, `output_tokens` is `output_total`, and `usd` and `model` come from the closing event or Claude's `usage`/`result` pair.
  - Each adapter class gains a class attribute `normalizer` naming its module's `normalize`: Claude and Qwen the Claude normalizer, Codex the Codex one, Gemini the Gemini one. `CliAdapter.parse` normalizes `out` with `normalizer`, `times_ns=None`, and an in-memory blob dict as `put_blob`, then returns `parsed_from_events`. An exception from the normalizer (`KeyError`, `TypeError`, `AttributeError`, or pydantic `ValidationError`) is raised as `ValueError("stream could not be normalized: ...")`.
  - The `parse` overrides of `ClaudeAdapter`, `CodexAdapter` and `GeminiAdapter` are deleted. `_events`, `_forward` and `_scrub_event` stay (the model-served lookup in `invoke` and the live consumer path use them until `one-parser-per-provider-meter`).
- `docs/how-clutch-works.md`: the `parsed` bullet of the end record (section 10.4) and the normalizers paragraph that says no engine code calls a normalizer. Say `CliAdapter.parse` calls the adapter's normalizer, list the new `Event` fields and the closing-event rule, and keep the rest.

Scope out: `CallMeter`, `EventConsumer` and `live_call` (`one-parser-per-provider-meter` and `one-parser-per-provider-live`); writing a `normalized/` view into a call record; `evidence` verbs; qwen's `unverified` flag; the `model.served` lookup in the end record; `parsed_failure` and `classify_failure` behavior beyond reading the new message text. `docs/how-clutch-works.md` is also fenced by the in-flight `training-export-trajectory`, which edits other sections (training export); either merge order is safe because the two edits touch different sections.

## Scope fence
- clutch/providers.py
- clutch/evidence/schema.py
- clutch/evidence/claude.py
- clutch/evidence/codex.py
- clutch/evidence/gemini.py
- tests/unit/test_provider_parsed_events.py
- tests/integration/test_provider_parsed_fixtures.py
- tests/unit/test_evidence_claude.py
- tests/unit/test_evidence_codex.py
- tests/unit/test_evidence_gemini.py
- tests/unit/test_qwen_adapter.py
- tests/unit/test_preflight_parallel.py
- tests/unit/test_preflight_latest_lookup.py
- docs/how-clutch-works.md

## Acceptance criteria
1. A Claude `result` line with `subtype` `success`, `result` `"hi"`, `total_cost_usd` 0.5 yields a `result` event with `status` `success`, `usd` 0.5 and `text_blob` equal to the id `put_blob` returned for `hi`; with `is_error` true it yields `status` `error`, not `success`; `./dev.py test tests/unit/test_provider_parsed_events.py` asserts both.
2. A Codex stream of `agent_message` "a", `agent_message` "b", `turn.completed` yields a `usage` event with `status` `success` and `text_blob` for `b` (not `a`); the same stream with a `turn.failed` line first yields `status` `error`; a stream with no `agent_message` yields `text_blob` None, not an empty blob; `./dev.py test tests/unit/test_provider_parsed_events.py` asserts all three.
3. A Gemini stream with assistant chunks `"DO"`, `"NE"` and a `result` of `status` `success` yields `text_blob` for `DONE` (one blob, not two) and `model` equal to the single `stats.models` key, None when two keys exist; a `result` with `status` `error` and `error.message` `bad` yields `status` `error` and `text_blob` for `bad`; `./dev.py test tests/unit/test_provider_parsed_events.py` asserts these.
4. Every event the three normalizers return, including those with the new fields, passes `Event.model_validate`, and the three golden fixtures still normalize with zero `unknown` events; `./dev.py test tests/unit/test_evidence_claude.py tests/unit/test_evidence_codex.py tests/unit/test_evidence_gemini.py tests/integration/test_evidence_claude_fixture.py tests/integration/test_evidence_codex_fixture.py tests/integration/test_evidence_gemini_fixture.py` exits 0.
5. `CliAdapter.parse` returns, for each fixture stream under `tests/fixtures/evidence/<provider>/`, `input_tokens` equal to the raw line's total input (Claude `input_tokens` + `cache_creation_input_tokens` + `cache_read_input_tokens`; Codex `input_tokens`; Gemini `stats.input_tokens`), `output_tokens` equal to the raw line's output count, and non-empty `text`; `./dev.py test tests/integration/test_provider_parsed_fixtures.py` asserts all three, with the expected numbers read from the raw fixture line, never from `parse`.
6. `ClaudeAdapter`, `CodexAdapter` and `GeminiAdapter` define no `parse` in their class bodies, and `CliAdapter.parse` is concrete: `./dev.py test tests/unit/test_provider_parsed_events.py` asserts `"parse" not in vars(cls)` for the three and that `CliAdapter.parse` does not raise `NotImplementedError`.
7. The existing parse and classifier tests pass: `./dev.py test tests/unit/test_gemini_adapter.py tests/unit/test_qwen_adapter.py tests/integration/test_providers.py tests/unit/test_preflight_parallel.py tests/unit/test_preflight_latest_lookup.py tests/unit/test_evidence_envelope.py` exits 0, the first and third unedited. In particular a Gemini `result` of `status` `error` still raises `ValueError` matching `Invalid stream`, an empty stream still raises `ValueError` matching `no terminal result event`, Claude `is_error` and Codex `turn.failed` carrying `usage limit reached` still classify as `quota_exhausted`, and a successful stream whose text holds `not logged in` is not classified as a failure.
8. A Codex `turn.completed` with `usage` `{input_tokens: 37, output_tokens: 5}` and no `cached_input_tokens` gives `Parsed.input_tokens` 37, not None, and one with `usage` `{}` gives None; a Codex stream with an `agent_message` and no `turn.completed` raises `ValueError` matching `no terminal result event`; `./dev.py test tests/unit/test_provider_parsed_events.py` asserts all three.
9. A Codex `item.started` line of type `command_execution` with no `id` makes `CliAdapter.parse` raise `ValueError` matching `could not be normalized`, not `KeyError`; `./dev.py test tests/unit/test_provider_parsed_events.py` asserts it.
10. A Codex stream with `turn.failed` then `turn.completed` raises `ValueError` (the old parser failed on any `turn.failed`), and a Gemini stream with an `error` line before a `success` `result` does not raise (the old parser ignored it); `./dev.py test tests/unit/test_provider_parsed_events.py` asserts both.
11. `clutch/providers.py` and each `clutch/evidence/*.py` file stay at or above their `test-gate.toml` floors, measured by `./dev.py test tests/unit`.

## Verification
```
./dev.py test tests/unit/test_provider_parsed_events.py tests/integration/test_provider_parsed_fixtures.py tests/unit/test_evidence_claude.py tests/unit/test_evidence_codex.py tests/unit/test_evidence_gemini.py tests/unit/test_gemini_adapter.py tests/unit/test_qwen_adapter.py tests/unit/test_preflight_parallel.py tests/unit/test_preflight_latest_lookup.py tests/unit/test_evidence_envelope.py tests/integration/test_providers.py tests/integration/test_evidence_claude_fixture.py tests/integration/test_evidence_codex_fixture.py tests/integration/test_evidence_gemini_fixture.py
```

## Definition of rejected
A provider `parse` override remains, or a second parser for the same stream shape is added beside the normalizers. `Parsed` values or failure classes differ from the old parser on any existing test stream other than the two named exceptions. The change edits `CallMeter`, `live_call` or any file outside the fence, or writes a `normalized/` view.

## Time budget
- expected: 30m
- stuck: 60m
- reason: three normalizers get the same four additions and one function replaces three parsers; one shared closing-event rule makes the parts untestable apart, and the meter and live parts are already their own tickets.
