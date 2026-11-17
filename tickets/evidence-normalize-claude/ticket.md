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
- clutch/evidence/codex.py
- docs/evidence-trail-plan.md

## Goal / Why
A pure Claude normalizer turns the raw stdout of one `claude --output-format stream-json --verbose` call into a list of `clutch.evidence.events/1.0` events, id `claude-stream/1`. A golden fixture holds one redacted real Claude stream. qwen's adapter subclasses Claude's and is expected to emit the same shape, but no qwen stream has been observed, so qwen reuses this normalizer and is flagged `unverified` until a qwen fixture exists. The `usage` event reports Claude's token buckets on the same basis as the Codex normalizer, so the two can be compared.

## Scope in / Scope out
Scope in:
- New module `clutch/evidence/claude.py` with `NORMALIZER_ID = "claude-stream/1"`, `VERIFIED_PROVIDERS = frozenset({"claude"})` and `normalize(stdout: bytes, times_ns: list[int] | None, put_blob: Callable[[bytes], str]) -> list[Event]`, mirroring the signature and no-I/O rule of `clutch/evidence/codex.py`. qwen is deliberately absent from `VERIFIED_PROVIDERS`: a later reader treats a provider outside that set as `unverified`. Large text (assistant text, thinking text, tool output) goes through the injected `put_blob`, which returns a `sha256:` id; events carry only that id.
- Mapping, in input order. `t_ms` is `times_ns[i] // 1_000_000` for the 0-based stdout line index `i` the event came from, or 0 when `times_ns` is None. `seq` is the 0-based index in the output list. One stdout line can yield several events (one per content block):
  - `system` with subtype `init` -> `session_start`.
  - `system` with subtype `thinking_tokens` -> `reasoning` with visibility `count_only` and `tokens` the integer count.
  - `system` with subtype `permission_denied` -> `permission_denied`.
  - `assistant` content block `text` -> `message`, role `assistant`, `text_blob`.
  - `assistant` content block `thinking` -> `reasoning`, visibility `text`, `text_blob`.
  - `assistant` content block `tool_use` -> `tool_call` with tool id equal to the block id, tool `native` equal to the tool name, and `args` equal to the block input. Tool class from a closed table: `Read` read; `Grep` search; `Glob` list; `Edit`, `MultiEdit`, `NotebookEdit` edit; `Write` write; `Bash` shell; `WebFetch` web_fetch; `WebSearch` web_search; `Task` subagent; `TodoWrite` plan; a name starting `mcp__` mcp; any other name other.
  - `user` content block `tool_result` -> `tool_result` with tool id equal to `tool_use_id`, `status` `error` when `is_error` is true else `ok`, and `output_blob` for the output text (a string, or the joined text blocks of a list).
  - `rate_limit_event` -> `rate_limit`.
  - `result` -> a `usage` event followed by a `result` event.
  - Any other line, block type, or non-JSON line -> `unknown` with the original content in `native` (a non-JSON line as `{"line": <text>}`). Nothing is dropped.
- The `usage` `tokens` dict has keys `input_uncached` (`input_tokens`), `input_cache_read` (`cache_read_input_tokens`), `input_cache_write` (`cache_creation_input_tokens`), `output_total` (`output_tokens`), `output_reasoning` (from `output_tokens_details`, when it carries a reasoning count) and `tokenizer` (`anthropic`). A key whose source field is absent is `None`, never 0.
- Golden fixture: one real Claude stream copied from the untracked provider captures in the main checkout's state dir (`<state_dir>/spools/providers/`, reachable from the worktree as `../../spools/providers/` under the default `worktree_root`), any `claude-*/events.jsonl` that contains `tool_use`, `tool_result`, `thinking` and `result` blocks. Redact secrets and host-private paths. Store it at `tests/fixtures/evidence/claude/stream.jsonl` with `tests/fixtures/evidence/claude/README.md` naming the CLI version it covers (`claude_code_version` from its `system/init` line) and stating that qwen is unverified. Read the fixture for the real field names before writing the mapping.

Scope out: `Parsed`, the journal, `CallMeter`, the adapters, the envelope writer, `evidence` verbs, renormalize, coverage reporting, and docs are unchanged. The `unverified` flag is only the `VERIFIED_PROVIDERS` constant here; nothing reads it yet. No qwen fixture.

## Scope fence
- clutch/evidence/claude.py
- tests/unit/test_evidence_claude.py
- tests/integration/test_evidence_claude_fixture.py
- tests/fixtures/evidence/claude

## Acceptance criteria
1. A `system`/`init` line yields kind `session_start`, never `unknown`; an `assistant` message with one `text`, one `thinking` and one `tool_use` block yields three events of kind `message`, `reasoning` (visibility `text`) and `tool_call` with `seq` 0, 1, 2; asserted by `./dev.py test tests/unit/test_evidence_claude.py`.
2. A `tool_use` named `Bash` has tool class `shell`, `Read` has `read`, `mcp__x__y` has `mcp`, and an unlisted name has `other`, not `shell`; the tool id equals the block id and `args` equals the block input; asserted by `./dev.py test tests/unit/test_evidence_claude.py`.
3. A `user` `tool_result` block with `is_error` true yields status `error` and one with it absent yields `ok`; `output_blob` is the id returned by the injected `put_blob`, not the output text; asserted by `./dev.py test tests/unit/test_evidence_claude.py`.
4. A `result` line with `input_tokens` 10, `cache_read_input_tokens` 90, `output_tokens` 5 and no `cache_creation_input_tokens` yields a `usage` event with `input_uncached` 10, `input_cache_read` 90, `input_cache_write` `None` (not 0), `output_total` 5, `output_reasoning` `None`, followed by a `result` event; asserted by `./dev.py test tests/unit/test_evidence_claude.py`.
5. A `rate_limit_event`, a `system`/`permission_denied` line and a `system`/`thinking_tokens` line map to `rate_limit`, `permission_denied` and `reasoning` with visibility `count_only`; an unmapped line type and a non-JSON line each yield one `unknown` event keeping the content in `native`; asserted by `./dev.py test tests/unit/test_evidence_claude.py`.
6. `times_ns=[0, 5_000_000]` gives `t_ms` 0 and 5 for events from lines 0 and 1, `times_ns=None` gives 0 on every event, every event passes `Event.model_validate`, and `"qwen"` is not in `VERIFIED_PROVIDERS` while `"claude"` is; asserted by `./dev.py test tests/unit/test_evidence_claude.py`.
7. The golden fixture normalizes with zero `unknown` events caused by a line or block type listed in the mapping, produces at least one `tool_call`, `tool_result`, `reasoning` and `usage` event, and every `tool_call` id has a matching `tool_result` id; asserted by `./dev.py test tests/integration/test_evidence_claude_fixture.py`.
8. `clutch/evidence/claude.py` meets the default unit coverage floor from `test-gate.toml`, measured by `./dev.py test tests/unit/test_evidence_claude.py`.

## Verification
```
./dev.py test tests/unit/test_evidence_claude.py tests/integration/test_evidence_claude_fixture.py
```

## Definition of rejected
The fixture is synthetic or hand-written rather than a redacted real Claude stream. A mapped line or block type falls through to `unknown`. The normalizer performs I/O, edits `Parsed`, the adapters or the journal, or lists qwen as verified.

## Time budget
- expected: 45m
- stuck: 90m
- reason: one module, one fixture and one test pair share a single mapping table and cannot be split without a dangling half-normalizer.
