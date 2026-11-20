---
state: draft
source: human
priority: P3
kind: chore
---

## Depends on
- one-parser-per-provider

## Context
- clutch/watchdog.py::CallMeter
- clutch/providers.py::ADAPTERS
- clutch/evidence/claude.py
- clutch/evidence/schema.py::Event
- tests/unit/test_watchdog_gemini.py

## Goal / Why
`CallMeter` (`clutch/watchdog.py`) reads each stream event through the provider's normalizer instead of branching on Claude, Codex and Gemini event shapes itself (roadmap decision 13, evidence plan row 8, part 2 of `one-parser-per-provider`). After this ticket `CallMeter._consume` has no provider-specific event names: it reads `Event.kind`, `Event.tool`, `Event.tokens` and `Event.usd` from the normalized event, so a provider whose normalizer is correct is metered correctly with no watchdog change.

The adapter keeps forwarding the scrubbed raw event dict to the consumer, so `EventConsumer`, `_forward`, `_scrub_event` and the consumer tests that assert raw dicts are untouched. `CallMeter` converts each dict it receives by calling its adapter's `normalizer` (added by `one-parser-per-provider`) on that one event, with `times_ns=None`.

The Claude normalizer emits no event for a mid-call assistant message's token usage, which `CallMeter` meters live today (`message.usage` keyed by `message.id`), so this ticket makes it emit one.

## Boundary contract
### Call metering
- disposition: replace
- owner: clutch/watchdog.py
- consumers: `Detector` (`tokens`, `spend`, `total_usd`, `bases`, the spiral and stuck decisions), `ProviderLLM.admitted_call`
- observable change: `CallMeter._consume` reads normalized events. `CallMeter.usage` is keyed by message id (or `terminal`) and holds the normalizer's bucket names (`input_uncached`, `input_cache_read`, `input_cache_write`, `output_total`), not the raw `input_tokens`-style names. `CallMeter.tools` holds the `tool.id` of every `tool_call` event, so a Codex `file_change`, `mcp_tool_call` and `web_search` item that is not a `tool_call` event is no longer added (nothing outside tests reads `tools`).
- compatibility: `Detector.tokens`, `spend`, `total_usd` and `bases` take the same values for the same Claude, Codex, Gemini and Qwen streams as before: tokens are the sum of the buckets, max-merged per bucket within one message id, and the terminal snapshot replaces the per-message sum when larger; cost is `usd` of a Claude `result` event. An event the normalizer rejects (`KeyError`, `TypeError`, `AttributeError`, pydantic `ValidationError`) still counts as progress and adds no tokens, tools or cost.
- acceptance: the criteria below
- tests: `tests/unit/test_callmeter_events.py`, `tests/integration/test_watchdog.py`, `tests/unit/test_watchdog_gemini.py`
- post-merge source of truth: `clutch/watchdog.py` for metering; `clutch/evidence/<provider>.py` for what each stream's events carry

### Claude normalizer assistant usage
- disposition: extend
- owner: clutch/evidence/claude.py
- consumers: `CallMeter`
- observable change: an `assistant` line whose `message.usage` is a dict also yields one `usage` event, `native_type` `assistant/usage`, with `tokens` buckets from that usage dict and `tokens["message_id"]` equal to `message.id`; it carries no `status`.
- compatibility: additive; the closing-event rule of `one-parser-per-provider` (the last `result`/`usage` event with a `status`) is unaffected because this event has no `status`; existing event order and indexes for lines without `message.usage` are unchanged.
- acceptance: criterion 3
- tests: `tests/unit/test_evidence_claude.py`, `tests/unit/test_callmeter_events.py`
- post-merge source of truth: `clutch/evidence/claude.py`

## Scope in / Scope out
Scope in:
- `CallMeter.__init__` takes the normalizer from `ADAPTERS[served.provider.name].normalizer`. `_consume` first calls `d.observe_progress()` as today, then normalizes the dict (`json.dumps` to bytes, `times_ns=None`, a throwaway blob function), then reads each event: a `tool_call` adds its `tool.id` to `tools`; an event with `tokens` updates `usage[key]` where key is `tokens["message_id"]` when present, else `terminal`, taking the max per bucket over non-None integer buckets, and recomputes `d.tokens` with the existing max(terminal sum, per-message sums) rule only when some bucket is non-zero; a `result` event with `usd` not None updates cost exactly as the `total_cost_usd` branch does today; `d.decide()` runs at the end. The same delta rules for `metered`, `estimate`, `spend` and `total_usd` stay.
- `clutch/evidence/claude.py` emits the assistant usage event described above. The `NORMALIZER_ID` stays.
- `tests/integration/test_watchdog.py`: update only the expectations that read the old bucket names (`call.usage["msg-1"]`) and the junk-event case whose `tool_use` block has an id but no `name` (the normalizer needs `name`, so give it one; the test's meaning is unchanged).
- `docs/how-clutch-works.md`: the normalizers paragraph of section 10.4, one sentence saying Claude `assistant` lines with usage also yield an `assistant/usage` event, and that `CallMeter` reads normalized events.

Scope out: `EventConsumer`, `_forward`, `_scrub_event`, `Detector`, `WatchedLLM`, the Codex and Gemini normalizers, `Parsed` and `live_call`. No stateful per-stream normalization (a Gemini `tool_result` seen alone gets tool class `other`, which `CallMeter` does not read). `docs/how-clutch-works.md` is also fenced by `one-parser-per-provider` (merged first, which this ticket depends on) and the in-flight `training-export-trajectory` (other sections); either order is safe.

## Scope fence
- clutch/watchdog.py
- clutch/evidence/claude.py
- tests/unit/test_callmeter_events.py
- tests/unit/test_evidence_claude.py
- tests/integration/test_watchdog.py
- tests/unit/test_watchdog_gemini.py
- docs/how-clutch-works.md

## Acceptance criteria
1. Feeding `CallMeter` the old raw Claude events of `tests/integration/test_watchdog.py` (an assistant message with `usage` input 10 and output 7 twice, then a `result` with `total_cost_usd` 2 and usage 10/7) leaves `Detector.tokens` and `spend` at the values that file asserts, and a repeated identical assistant line does not add tokens twice; `./dev.py test tests/integration/test_watchdog.py` asserts it.
2. A Codex `item.started` of type `command_execution` with id `tool-1` puts `tool-1` in `CallMeter.tools`; a Codex `turn.completed` with `input_tokens` 100 and `output_tokens` 3 sets `Detector.tokens` to 103 once, not 206 when the identical event arrives twice; `./dev.py test tests/unit/test_callmeter_events.py` asserts both.
3. A Claude `assistant` line with `message.id` `m1` and `usage` `{input_tokens: 10, output_tokens: 7}` normalizes to a `usage` event with `tokens["message_id"]` `m1`, `input_uncached` 10, `output_total` 7 and `status` None, and a line without `message.usage` yields no extra event; `./dev.py test tests/unit/test_evidence_claude.py` asserts both.
4. The Gemini `T17` stream fed event by event gives `Detector.tokens` 22168 and `spend` 0.5, as `tests/unit/test_watchdog_gemini.py` asserts today; `./dev.py test tests/unit/test_watchdog_gemini.py` exits 0.
5. An event the normalizer rejects (a Claude `assistant` line whose `message` is `False`, a Codex `item.started` with no `id`) still advances `Detector.progress_epoch` when the scope snapshot changed and leaves `tokens`, `tools` and cost as they were, and does not raise; `./dev.py test tests/unit/test_callmeter_events.py` asserts it.
6. `clutch/watchdog.py` names no provider event type: its source contains none of the strings `turn.completed`, `item.started`, `tool_use`, `total_cost_usd` or `cache_creation_input_tokens`; `./dev.py test tests/unit/test_callmeter_events.py` asserts it by reading the module source through `inspect`.
7. The raw-dict consumer tests still pass unchanged: `./dev.py test tests/integration/test_providers.py tests/integration/test_watchdog_activation.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_callmeter_events.py tests/unit/test_evidence_claude.py tests/unit/test_watchdog_gemini.py tests/integration/test_watchdog.py tests/integration/test_providers.py tests/integration/test_watchdog_activation.py
```

## Definition of rejected
`CallMeter` still branches on a provider's event names, or a second per-provider event reader is added. `Detector.tokens`, `spend` or `bases` differ from the old values on any existing test stream. The consumer interface or `_forward` changes, or any file outside the fence is edited.

## Time budget
- expected: 30m
- stuck: 60m
- reason: one meter rewrite and one normalizer addition share the bucket names; splitting them leaves the meter without its mid-call tokens.
