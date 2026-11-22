---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Runs before
- regression-command-program-lint

## Context
- clutch/providers.py::CliAdapter.invoke
- clutch/providers.py::ClaudeAdapter
- clutch/llm.py::LLMRequest
- tests/unit/test_update_config_verb.py

## Goal / Why
Every `claude` process clutch starts (Implement, Review, Diagnose, Rework, Retro, Triage, preflight probes and the rest) saves a session under the same project as the owner's own chats. The VS Code Claude panel's Past Conversations list then shows hundreds of engine sessions beside the owner's chats with model-generated titles ("Single word reply", "Retry keeps prior branch"), and the owner cannot tell their chats from clutch's. On 2026-11-22, 151 of the last 200 sessions for this repo carried the VS Code entrypoint, and most of those were clutch runs, because clutch inherits the editor's environment.

The `claude` CLI takes `-n/--name <name>`, which sets the session's display name in the resume picker and history list. When this ticket is done, every `claude` argv clutch builds carries `--name` with a name that starts with `Clutch `, then the stage, then the ticket stem when the call has one:

- `ClaudeAdapter` calls through `CliAdapter.invoke` get `--name "Clutch <Surface> <stem>"`, where `<Surface>` is `LLMRequest.surface` with each `_` replaced by a space and each word capitalized (`implement` -> `Implement`, `requisition_review` -> `Requisition Review`, `review_visual` -> `Review Visual`), and `<stem>` is `LLMRequest.ticket`. When `ticket` is `None` the name is `Clutch <Surface>` with no trailing space.
- `ClaudeAdapter.list_models` probe calls get `--name "Clutch Preflight <alias>"` (for example `Clutch Preflight sonnet`).

Other adapters (codex, qwen, gemini) do not change: their CLIs have no such flag.

## Boundary contract
### Claude CLI argv
- disposition: extend
- owner: clutch/providers.py
- consumers: the `claude` CLI process clutch starts for every Claude-routed surface and the model-listing probe; tests that pin that argv
- observable change: the argv gains the two elements `--name` and the session name described in Goal / Why; every element present today stays, in the same order, before them
- compatibility: no other flag, the stdin prompt, cwd, env, timeout, or the parsing of the stream changes; codex, qwen and gemini argv are unchanged
- acceptance: an Implement call for stem `abc` carries `--name` followed by `Clutch Implement abc` as the last two argv elements; a call with `ticket=None` ends with `Clutch <Surface>`; a probe ends with `Clutch Preflight <alias>`
- tests: tests/unit/test_claude_session_name.py, tests/unit/test_update_config_verb.py, tests/integration/test_providers.py
- post-merge source of truth: clutch/providers.py

## Scope in / Scope out
Scope in:
- `clutch/providers.py`: in `CliAdapter.invoke`, after `argv` is built and any `--max-budget-usd` is added, append `--name` and the session name for `ClaudeAdapter` only; in `ClaudeAdapter.list_models`, append `--name` and `Clutch Preflight <alias>` to the probe argv. The session-name rule from Goal / Why lives in one place in `clutch/providers.py`.
- `tests/unit/test_claude_session_name.py` (new): drive `CliAdapter.invoke` for a `ClaudeAdapter` with `tests/fakes.py::FakeExec`-style recorded argv (no process starts) for `implement` with ticket `abc`, `requisition_review` with ticket `abc`, and `retro` with `ticket=None`; and assert a `CodexAdapter` call carries no `--name`.
- `tests/unit/test_update_config_verb.py`: the pinned probe argv in `test_claude_listing` gains `"--name", f"Clutch Preflight {alias}"` at the end. Nothing else in that file changes.
- `tests/integration/test_providers.py`: the exact argv pinned in `test_claude_implement_gets_the_write_grant_in_the_worktree` gains the two `--name` elements at the end, and the `[-7:]` slice in `test_claude_read_only_surface_gets_the_read_tool_allowlist_and_no_grant` becomes a check that the read-only grant elements appear in order before `--name`. Nothing else in that file changes. The file stays skipped.

Scope out:
- Turning off session persistence, changing the entrypoint environment, or deleting saved sessions.
- Codex, qwen and gemini adapters.
- Any change to which surfaces exist or how they are routed.

## Scope fence
- clutch/providers.py
- tests/unit/test_claude_session_name.py
- tests/unit/test_update_config_verb.py
- tests/integration/test_providers.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_claude_session_name.py` passes and asserts the Implement argv for stem `abc` ends with `["--name", "Clutch Implement abc"]` (not `implement`, not without the stem), the `requisition_review` argv ends with `["--name", "Clutch Requisition Review abc"]` (not `Requisition_review`), the `ticket=None` argv ends with `["--name", "Clutch Retro"]` (no trailing space, no `None`), and a `CodexAdapter` argv contains no `--name`.
2. `./dev.py test tests/unit/test_update_config_verb.py` passes with each probe argv ending `["--name", "Clutch Preflight <alias>"]` for its own alias, not one shared name.
3. `./dev.py test tests/unit` exits 0.

## Verification
```
./dev.py test tests/unit/test_claude_session_name.py
./dev.py test tests/unit/test_update_config_verb.py
./dev.py test tests/unit
```

## Definition of rejected
- Any argv element that exists today is removed or reordered, or a non-Claude adapter's argv changes.
- The session name omits the `Clutch ` prefix, the surface, or the stem when the request has one.
- A test starts a real `claude` process.

## Time budget
- expected: 15m
- stuck: 30m
