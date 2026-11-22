---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- host-prompts

## Context
- clutch/observe.py::extension_fields
- clutch/observe.py::snapshot
- clutch/help.py
- vscode-clutchwork/extension.js
- tests/integration/test_help.py
- docs/how-clutch-works.md#2.2

## On-demand
- vscode-clutchwork/package.json

## Goal / Why
The Tickets view's More Actions menu gets an "Ask Claude: prompt…" item. It opens a single-choice picker listing every named operator prompt, engine-owned and host-owned (from `host-prompts`), each with its description. Choosing one opens a Claude Code chat with that prompt's rendered text.

Today the extension offers only five fixed prompt actions, each wired by hand: drain loop, diagnose, review, drafts, and box. Nothing shows the rest of the engine prompts or any host prompt. The picker reads its entries from the snapshot, which builds them from `ask.catalog`, so a new engine or host prompt appears in the picker with no extension change.

Behavior:
- The snapshot carries `promptPick`, built in Python from `ask.catalog(config, root)`. Each entry has `label` (the argv after `prompt`, for example `diagnose` or `host triage-notes`), `detail` (the description), `argv`, and `takes`.
- Each invalid host prompt file from the catalog's problems becomes an entry with `label` set to the file path, `detail` set to the problem message, and no `argv`. Choosing it shows the message as an error and opens nothing.
- The snapshot carries `promptArgs`: `stem` holds every ticket stem in snapshot `rows`, in row order, and `box` holds every box message id, in snapshot `box` order.
- In the extension:
  - `takes: none` opens the prompt directly.
  - `takes: stem` shows a single-choice pick of `promptArgs.stem`, then opens the prompt with that stem.
  - `takes: box` shows a multi-choice pick of `promptArgs.box`, then opens the prompt with those ids.
  - Cancelling any pick opens nothing.

## Boundary contract
### Snapshot `promptPick` and `promptArgs`
- disposition: extend
- owner: clutch/observe.py
- consumers: vscode-clutchwork/extension.js
- observable change: two new top-level snapshot keys, `promptPick` (a list of `{label, detail, argv?, takes?}`) and `promptArgs` (`{stem: [...], box: [...]}`)
- compatibility: all existing snapshot keys unchanged
- acceptance: every `ask.catalog` entry appears once, in catalog order, followed by one argv-less entry per problem; each `argv` parses with the clutch CLI parser
- tests: tests/unit/test_observe_prompt_pick.py
- post-merge source of truth: clutch/observe.py, built from clutch/ask.py `catalog`

### Extension command `clutch.askPrompt`
- disposition: create
- owner: vscode-clutchwork/extension.js and vscode-clutchwork/package.json
- consumers: operators using the Tickets view More Actions menu
- observable change: new "Ask Claude: prompt…" item in the Tickets view title overflow (group `clutch@7`), hidden from the command palette like the other view actions
- compatibility: existing prompt actions (`clutch.askDrainLoop`, ticket and box context actions) are unchanged
- acceptance: the command exists in `package.json` and has a `clutch/help.py` entry, so `tests/integration/test_help.py` stays green
- tests: tests/integration/test_help.py and tests/unit/test_observe_prompt_pick.py
- post-merge source of truth: vscode-clutchwork/package.json and clutch/help.py
- closest existing: `clutch.engine` (a single-choice pick over snapshot `engineVerbs`) and `clutch.askDrainLoop` (`openClaude` with a fixed argv)
- earning reason: `clutch.engine` runs verbs in a terminal and its entries are fixed engine verbs; `clutch.askDrainLoop` opens one fixed prompt. Neither can offer a host-defined prompt or ask for that prompt's arguments.

## Scope in / Scope out
Scope in:
- `clutch/observe.py`: add `prompt_pick(config, root, stems, box_ids)`, returning `{"promptPick": [...], "promptArgs": {...}}`, and merge its result into the `snapshot` return. It is a separate function so the unit test can drive it under `tmp_path` without building a whole snapshot. `snapshot` loads config with `load_config(ctx.config, cwd=ctx.root)`, as it already does for caps.
- `clutch/help.py`: add `"clutch.askPrompt": "Open a prompt chosen from every engine and host prompt."` to `_commands`.
- `vscode-clutchwork/package.json`: declare `clutch.askPrompt` titled `Ask Claude: prompt…`, category `clutch`. Add it to `view/title` for `view == clutch.tickets` in group `clutch@7`, and to `commandPalette` with `when: false`.
- `vscode-clutchwork/extension.js`: register `clutch.askPrompt`. JavaScript only maps snapshot fields to `showQuickPick` items and calls the existing `openClaude(root, argv)`. It never filters, sorts or builds argv beyond appending the picked stem or ids.
- `docs/how-clutch-works.md`: in the section 2 extension paragraph that lists the More Actions items, add Ask Claude: prompt… and say it lists every engine and host prompt.
- New `tests/unit/test_observe_prompt_pick.py`.

Scope out:
- Removing or changing `clutch.askDrainLoop` or any ticket or box context-menu ask action.
- Any change to `ask.catalog`, `clutch prompt`, or host prompt files (`host-prompts`).
- Filtering the stem list by ticket state.

## Scope fence
- clutch/observe.py
- clutch/help.py
- vscode-clutchwork/extension.js
- vscode-clutchwork/package.json
- docs/how-clutch-works.md
- tests/unit/test_observe_prompt_pick.py

## Acceptance criteria
1. With a `tmp_path` config whose `prompts_dir` holds one valid `takes: stem` prompt `notes` and one invalid file `bad.md`, `prompt_pick(...)["promptPick"]` holds every `ask.KINDS` label in `KINDS` order, then `host notes` with `argv == ["prompt", "host", "notes"]` and `takes == "stem"`, then one entry for `bad.md` with no `argv` key. It is not missing the host entry and does not hide the problem (`tests/unit/test_observe_prompt_pick.py`).
2. For every `promptPick` entry with an `argv`, the test appends the literal placeholder argument `example` when `takes` is `stem` or `box`, and the result parses with the clutch CLI parser without `SystemExit` (`tests/unit/test_observe_prompt_pick.py`).
3. `prompt_pick(config, root, ["a", "b"], ["box-1"])["promptArgs"] == {"stem": ["a", "b"], "box": ["box-1"]}`, keeping input order, not sorted (`tests/unit/test_observe_prompt_pick.py`).
4. Each `promptPick` `detail` for an engine kind equals `ask.DESCRIPTIONS[kind]`, not a copied string (`tests/unit/test_observe_prompt_pick.py`).
5. `package.json` declares `clutch.askPrompt` and `clutch/help.py` has its entry (`tests/integration/test_help.py`).

## Verification
```
./dev.py test tests/unit/test_observe_prompt_pick.py tests/integration/test_help.py tests/unit/test_observe_extension_fields.py
./dev.py test
```

## Definition of rejected
- `extension.js` filters, sorts, or derives prompt entries or stems, or hardcodes a prompt name or description.
- An invalid host prompt makes the snapshot fail or vanishes from the picker without an entry.
- Any existing extension prompt action changes behavior.

## Time budget
- expected: 25m
- stuck: 50m
