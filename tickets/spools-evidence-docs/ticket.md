---
state: draft
source: human
priority: P3
kind: chore
---

## Depends on
- spools-onto-evidence-store-r2

## Context
- tests/integration/test_evidence_envelope.py
- tests/unit/test_spool_store_switch.py

## On-demand
- clutch/specs/ask/diagnose.md
- clutch/specs/ask/running.md
- docs/how-clutch-works.md
- clutch/docs/host-contract.md
- clutch/redact.py
- CLAUDE.md
- AGENTS.md

## Goal / Why
Roadmap row 186 (`spools-evidence-docs`). After `spools-onto-evidence-store-r2` every per-attempt capture lives in the evidence store, read with `clutch evidence captures <stem>`, and nothing writes under `<state_dir>/spools/`. Eight places still name `spools/` or "attempt spools" as live: the two ask specs `clutch/specs/ask/diagnose.md` and `clutch/specs/ask/running.md` send an operator to `${state_dir}/spools/${stem}/`, which no longer exists; `docs/how-clutch-works.md` has the `spools/` row of the state-dir table, the sentence in the driver section saying each call is spooled under `state_dir/spools/`, and the redaction bullet in section 8.5; `clutch/docs/host-contract.md` and the `clutch/redact.py` docstring describe attempt spools; and the `spools/` line in `CLAUDE.md` and `AGENTS.md` (the journal rule). An operator following them looks in an empty directory.

After this ticket each of those places names the evidence store and `clutch evidence captures`, and nothing names `spools/` as a live path.

## Boundary contract
none
- reason: documentation and prompt-text corrections to match behavior that already shipped; no code, config or interface changes, and the `Spool` class and its callers are untouched.

## Scope in / Scope out
Scope in, one edit per place, wording limited to what is false:
- `clutch/specs/ask/diagnose.md` and `clutch/specs/ask/running.md`: replace the `${state_dir}/spools/${stem}/` path with `clutch evidence captures ${stem}` (list a ticket's captures; `--attempt` and `--name` print one). Change nothing else in either file.
- `docs/how-clutch-works.md`: the driver-section sentence "each call is spooled under `state_dir/spools/`" names the evidence store; the `spools/` row of the state-dir table is removed (the `evidence/` row already describes the store; extend it by one clause only if it does not say per-attempt prompts, outputs and command output are captures); the section 8.5 bullet says "in captures" instead of "in spools". Then `uv run clutch meta refresh docs/how-clutch-works.md`, changing nothing else in its header.
- `clutch/docs/host-contract.md`: "attempt spools" in the state-dir description (two places) becomes "evidence captures"; the `check/host-NN.txt` and `merge/host-NN.txt` sentence stays as written (they are capture names). Then `uv run clutch meta refresh clutch/docs/host-contract.md`.
- `clutch/redact.py`: the docstring writer-site line for `Spool` says it writes to the evidence store. No code changes; `tests/unit/test_harvest_redaction.py` is fenced only because `redact.py` has a coverage floor and is run unedited.
- `CLAUDE.md` and `AGENTS.md`: "attempt spools" in the journal rule becomes "captures"; both files change in the same way, as the rule requires. These are rule-text edits and each rule's home does not change.
- `tests/integration/test_evidence_envelope.py`: the one assertion near line 52 that pins the exact row `| `spools/` | Per-attempt prompts, outputs, and command output. |` changes to assert no row starts with `` | `spools/` | ``; every other assertion stays.

Scope out: any code change, the roadmap and the training-data plan (`box-000964`), `clutch/help.py`, the `Spool` class name, and every other mention of "spool" as a word for the capture writer.

## Scope fence
- clutch/specs/ask/diagnose.md
- clutch/specs/ask/running.md
- docs/how-clutch-works.md
- clutch/docs/host-contract.md
- clutch/redact.py
- CLAUDE.md
- AGENTS.md
- tests/integration/test_evidence_envelope.py
- tests/unit/test_harvest_redaction.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_evidence_envelope.py` passes and asserts no row of `docs/how-clutch-works.md` starts with `` | `spools/` | ``, not that the old row text is present.
2. `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/unit/test_help.py tests/unit/test_harvest_redaction.py` passes, showing both ask specs still render and every verb they name exists.
3. `uv run clutch meta check docs/how-clutch-works.md clutch/docs/host-contract.md` exits 0.
4. `git diff main --stat` lists only the fenced files, and `clutch/specs/ask/diagnose.md` and `clutch/specs/ask/running.md` each contain `clutch evidence captures` and neither contains `/spools/`.

## Verification
```
./dev.py test tests/integration/test_evidence_envelope.py tests/integration/test_ask_plan_drain.py tests/integration/test_ask_plan_serve.py tests/unit/test_help.py tests/unit/test_harvest_redaction.py
uv run clutch meta check docs/how-clutch-works.md clutch/docs/host-contract.md
```

## Definition of rejected
Any code or config change; a docs edit outside the places named in Scope in; an edit to `tests/unit/test_harvest_redaction.py`; `CLAUDE.md` and `AGENTS.md` changed differently from each other; the evidence-envelope test weakened beyond the one assertion; a mention of `spools/` left as a live path in any of the eight files.

## Time budget
- expected: 12m
- stuck: 24m
