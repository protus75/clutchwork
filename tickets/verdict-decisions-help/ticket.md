---
state: draft
source: box:suggestion
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/help.py
- clutch/observe.py::snapshot
- vscode-clutchwork/media/view.js
- docs/how-clutch-works.md#7.3 Control
- tests/unit/test_help.py
- tests/integration/test_help.py
- tests/integration/test_status.py

## Goal / Why
The verdict-decisions rows that the tickets view prepends (a `stale` or `rejected` `control_decision` for a confirm or reject whose stem is still unresolved) have no help entry. Nothing on screen or in the docs says what such a row is or what to do about it. CLAUDE.md section A requires every extension surface a person sees to carry help from `clutch/help.py`, linked to the doc section that owns the fact. This surface is the only place the extension shows a failed confirm or reject, so a row with no next step also breaks the fail-closed rule.

After this change:
- `docs/how-clutch-works.md` section 7.3 explains verdict decisions: the engine decides a published confirm or reject later, `stale` and `rejected` mean it was not applied, the row's reason says why, and the way forward is to fix that cause and run `confirm` or `reject` again for the stem. It also says the row disappears once the stem is resolved.
- `clutch/help.py` has a topic `verdict.decisions` whose link points at that section.
- The snapshot names that topic in a new key `verdictDecisionsHelp`, and `view.js` shows the topic text as each decision row's tooltip.

## Scope in / Scope out
In:
- `docs/how-clutch-works.md`: add a short paragraph under `### 7.3 Control` (the heading stays unchanged, so existing links keep working).
- `clutch/help.py`: add one topic through `_add` with kind `verdict`, name `decisions`, heading `7.3 Control`, doc `docs/how-clutch-works.md`. Its `what` is a sentence ending in a period, and `before` and `after` are non-empty.
- `clutch/observe.py`: add `"verdictDecisionsHelp": "verdict.decisions"` to the dict that `snapshot` returns, next to `verdictDecisions`.
- `vscode-clutchwork/media/view.js`: set `title` on each decision row from `snap.help[snap.verdictDecisionsHelp].text`. This is a lookup of a snapshot-supplied topic, with no logic.
- `tests/unit/test_help.py`: add `"verdict": {"decisions"}` to the `expected` set in `test_vocabularies_covered`, and add a test `test_verdict_decisions_link` that asserts `build(documents())["verdict.decisions"]["link"]["url"].endswith("/blob/main/docs/how-clutch-works.md#73-control")`.
- `tests/integration/test_status.py`: extend the existing verdictDecisions assertion near line 288 to check the new key.

Out:
- No new verbs and no change to how decisions are projected or retired (`clutch/status.py`).
- No change to the decision row text.
- `tests/integration/test_help.py` is unchanged: `test_links_resolve` already loops over every topic in `TOPICS`.

## Scope fence
- docs/how-clutch-works.md
- clutch/help.py
- clutch/observe.py
- vscode-clutchwork/media/view.js
- tests/unit/test_help.py
- tests/integration/test_status.py

## Acceptance criteria
1. `help_map` returns the key `verdict.decisions`, and `tests/unit/test_help.py::test_verdict_decisions_link` asserts its `link` `url` ends in `/blob/main/docs/how-clutch-works.md#73-control`. The test fails with a `KeyError` if the topic is missing and fails if the url points at another section. `./dev.py test tests/integration/test_help.py::test_links_resolve` also passes with the topic present.
2. `tests/unit/test_help.py::test_vocabularies_covered` lists `verdict.decisions` as expected and fails when `verdict.decisions` is absent from `TOPICS`.
3. `snapshot(ctx)["verdictDecisionsHelp"] == "verdict.decisions"` and that key is in `snapshot(ctx)["help"]`, checked in `tests/integration/test_status.py`. A snapshot without the key, or one naming a topic missing from `help`, fails.
4. `grep -n "verdictDecisionsHelp" vscode-clutchwork/media/view.js` finds the decision-row tooltip line, and that line contains no condition, filter, or copied text.
5. `docs/how-clutch-works.md` section 7.3 contains the words `stale`, `rejected`, and `confirm` or `reject` again, so a reader finds the way to resubmit. `grep -c "verdict decision" docs/how-clutch-works.md` is at least 1.

## Verification
```
./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_status.py
```

## Definition of rejected
The branch adds help text to `vscode-clutchwork/` or `observe.py` instead of `clutch/help.py`, adds JavaScript that decides or filters rows, changes the verdict projection, or leaves the new topic without a doc section that explains how to resubmit.

## Time budget
- expected: 25m
- stuck: 60m
