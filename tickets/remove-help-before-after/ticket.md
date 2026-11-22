---
state: draft
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Context
- clutch/help.py
- tests/unit/test_help.py
- tests/integration/test_help.py
- tests/unit/test_help_snapshot.py
- docs/how-clutch-works.md#2.2
- clutch/stats.py::stats_tree

## Goal / Why
Every VS Code extension help surface (hover tooltips, the Details help text, the Stats tree tooltips, and each setting's `markdownDescription`) shows only what the surface is plus its doc link. The `Before:` and `After:` lines are gone everywhere.

Why: the owner judged the Before/After prose (2026-11-22) to add noise, not information: lines such as "Before: Open a clutch workspace. After: Select an item or action." repeat on every surface and make tooltips longer without helping anyone.

## Boundary contract
### Extension help snapshot entries
- disposition: extend
- owner: clutch/help.py
- consumers: clutch/observe.py (snapshot `help` map and `help_pick`), clutch/stats.py (`stats_tree` tooltips via `topic_text`), vscode-clutchwork/media/detail.js, view.js and box.js (which render `entry.text` and `entry.what`)
- observable change: each `help_map` entry drops its `before` and `after` keys and its `text` equals its `what`; `topic_text(key)` returns `TOPICS[key]["what"]`; `TOPICS` entries no longer carry `before` or `after`
- compatibility: the JavaScript readers use only `what`, `text` and `link`, which keep their names and types, so no extension code changes
- acceptance: no help text contains `Before:` or `After:`
- tests: tests/unit/test_help.py, tests/integration/test_help.py
- post-merge source of truth: clutch/help.py

### Extension settings help
- disposition: extend
- owner: vscode-clutchwork/package.json
- consumers: the VS Code settings UI
- observable change: each `clutch.*` setting's `markdownDescription` drops its `Before:` and `After:` paragraphs and keeps the first sentence and the `[Learn more](...)` link
- compatibility: setting names, types and defaults are unchanged
- acceptance: no `markdownDescription` contains `Before:` or `After:`
- tests: tests/integration/test_help.py::test_manifest_covered
- post-merge source of truth: vscode-clutchwork/package.json

## Scope in / Scope out
Scope in:
- `clutch/help.py`: remove the `before` and `after` parameters of `_add` and every argument passed for them; remove the `before`/`after` keys from the `verb.*` and `priority` entries; `topic_text` returns only the `what` text; `help_map` sets `text` to `what` for every entry and drops the `before` and `after` result keys.
- `vscode-clutchwork/package.json`: in each `contributes.configuration.properties` `markdownDescription`, delete the `\n\nBefore: ...` and `\n\nAfter: ...` paragraphs; nothing else in the file changes.
- `tests/unit/test_help.py::test_topic_shape`: the help text is exactly one line equal to `what`; it asserts no entry has a `before` or `after` key and no text contains `Before:` or `After:`.
- `tests/integration/test_help.py::test_manifest_covered`: replace the `"Before:" in description and "After:" in description` assertion with one that `Before:` and `After:` are both absent.
- `docs/how-clutch-works.md` section 2.2 `./dev.py`: the sentence on extension help says each surface shows what it is and a link to its documentation; drop "`Before:` and `After:` lines".
- `CLAUDE.md` and `AGENTS.md` (repo-rule home, outside the managed block): in the "Extension help has one source" rule, change "a short description saying what it is, then what comes before and after it, with a link" to "a short description saying what it is, with a link". Both files get the identical edit.

Scope out:
- Removing the now-redundant `text` key or changing the extension JavaScript to read `what`; `text` stays so no JS reader changes.
- Rewording any `what` description or doc link.
- `clutch/hostfiles.py` `CORE_TEMPLATE`: the rule is a repo rule, not a host rule.

## Scope fence
- clutch/help.py
- vscode-clutchwork/package.json
- tests/unit/test_help.py
- tests/integration/test_help.py
- docs/how-clutch-works.md
- CLAUDE.md
- AGENTS.md

## Acceptance criteria
1. `tests/unit/test_help.py::test_topic_shape` passes and fails if any `help_map` entry's `text` differs from its `what`, contains `Before:` or `After:`, or carries a `before` or `after` key.
2. `tests/integration/test_help.py::test_manifest_covered` passes and fails if any setting's `markdownDescription` contains `Before:` or `After:`.
3. `tests/unit/test_help_snapshot.py::test_stats_tree_tooltips` passes unchanged: each Stats tooltip equals the topic's `what` text.
4. `grep -rn "Before:\|before and after" clutch/help.py vscode-clutchwork/package.json docs/how-clutch-works.md CLAUDE.md AGENTS.md` prints nothing.
5. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_help.py tests/unit/test_help_snapshot.py tests/integration/test_help.py
./dev.py test
```

## Definition of rejected
- Any extension help text or setting description still shows a `Before:` or `After:` line.
- A `what` description or doc link changes wording.
- Extension JavaScript changes.
- CLAUDE.md and AGENTS.md differ in the edited rule.

## Time budget
- expected: 12m
- stuck: 24m
