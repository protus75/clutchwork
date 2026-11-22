---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/stats.py
- clutch/llmeffect.py::_cost
- clutch/help.py
- tests/integration/test_stats.py

## Goal / Why
`clutch view stats` (and the extension's Stats view, which renders `stats_tree` of the same projection) reports LLM usage in tokens, broken down per provider, and reports no USD figure at all.

Why: the owner pays fixed monthly subscription rates, not per-token prices, so the USD `spend` figures (the stream's reported USD or the `est_cost_per_call_usd` estimate) are far from what is actually paid and are worthless to track (owner, 2026-11-22). Token counts from different providers are not the same logical unit (different tokenizers, and codex `input_tokens` includes cached tokens), so they are never summed across providers.

## Boundary contract
### Stats projection
- disposition: extend
- owner: clutch/stats.py::project_stats
- consumers: `clutch view stats` text and `--json` output, `clutch view stats --tree` and the extension Stats view through `stats_tree`
- observable change: the top-level `spend` section is replaced by a `usage` section; it has no `usd`, `usd_per_merge`, or cross-provider `tokens` total. `usage.by_provider` maps each provider name to `{"calls", "failures", "input_tokens", "output_tokens", "output_tokens_per_merge"}`; `usage.by_surface` maps each llm surface to provider name to `{"input_tokens", "output_tokens"}`. Token sums come from each effect completion's journaled `cost` (`provider`, `input_tokens`, `output_tokens`, as written by `clutch/llmeffect.py::_cost`); a null token count adds 0; a cost with no `provider` is keyed `unknown`. `calls` and `failures` come from `provider_call_outcome` signals as before. `output_tokens_per_merge` is `null` when nothing merged in the window.
- compatibility: the stats projection is a read-only view, not an authority; no stored format changes and the journal is untouched. `--json` consumers reading `spend` must read `usage`; the only in-repo consumers are `stats_tree` (generic, reads any keys) and the pinned key list in `tests/integration/test_stats.py`.
- acceptance: criteria 1-4
- tests: `tests/unit/test_stats_usage.py`, `tests/integration/test_stats.py`
- post-merge source of truth: clutch/stats.py

## Scope in / Scope out
Scope in:
- In `clutch/stats.py::project_stats`, replace the `spend` section with the `usage` section described in the Boundary contract, and drop the `total_spend` import and the `usd` computation.
- In `clutch/help.py`, replace the `stat` topic entry `"spend"` with `"usage"`, text: "Summarizes token usage and calls per provider; tokens are never summed across providers because they are not the same unit."
- In `tests/integration/test_stats.py`, change the pinned top-level key list's last entry from `"spend"` to `"usage"`; nothing else changes there.
- Add `tests/unit/test_stats_usage.py` covering the criteria with in-memory events (no repo file reads).

Scope out:
- `clutch view status` spend line, the roadmap digest `spend:` line, the scorecard `spend_usd`, `clutch/journal.py::total_spend`, and provider `est_cost_per_call_usd` config stay as they are; whether they also move to tokens is a separate owner decision.
- The extension JavaScript is untouched: it already draws `stats_tree` rows generically.

## Scope fence
- clutch/stats.py
- clutch/help.py
- tests/integration/test_stats.py
- tests/unit/test_stats_usage.py

## Acceptance criteria
1. With completions costing `{"provider": "claude", "input_tokens": 100, "output_tokens": 10, "usd": 5.0}` and `{"provider": "codex", "input_tokens": 200, "output_tokens": 20, "usd": 0.5}`, `project_stats(...)["usage"]["by_provider"]` gives claude `input_tokens` 100 / `output_tokens` 10 and codex 200 / 20, not a single summed 300 / 30; checked by `tests/unit/test_stats_usage.py`.
2. `project_stats(...)` output contains no `spend` key and no key containing `usd` anywhere in the `usage` section, not the old `usd` / `usd_per_merge` fields; checked by `tests/unit/test_stats_usage.py`.
3. `usage.by_surface` for an `llm/<stem>/1/implement/1/1` completion from claude reports `{"implement": {"claude": {"input_tokens": ..., "output_tokens": ...}}}`, a cost with no `provider` lands under `unknown`, and a `null` `output_tokens` adds 0 rather than raising; checked by `tests/unit/test_stats_usage.py`.
4. `output_tokens_per_merge` is `null` with zero merges in the window and equals the provider's output tokens divided by merged count otherwise, not divided by 1 when nothing merged; checked by `tests/unit/test_stats_usage.py`.
5. `clutch view stats --json` prints top-level keys ending in `usage`, not `spend`; checked by `tests/integration/test_stats.py`.

## Verification
```
./dev.py test tests/unit/test_stats_usage.py tests/integration/test_stats.py tests/unit/test_help.py tests/integration/test_help.py
```

## Definition of rejected
- Any USD figure remains in the stats projection.
- Tokens from different providers are summed into one number anywhere in the stats projection.
- Status, digest, scorecard, or journal spend code is changed.

## Time budget
- expected: 10m
- stuck: 20m
