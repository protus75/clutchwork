---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- vscode-help-catalog
- vscode-help-snapshot
- vscode-help-surfaces

## Context
- vscode-clutchwork/package.json
- vscode-clutchwork/extension.js
- clutch/observe.py::snapshot
- clutch/hostfiles.py::CORE_TEMPLATE

## On-demand
- CLAUDE.md
- AGENTS.md
- docs/how-clutch-works.md
- clutch/docs/host-contract.md
- vscode-clutchwork/README.md

## Goal / Why
`vscode-help-catalog`, `vscode-help-snapshot` and `vscode-help-surfaces` give every extension surface help from one Python source, `clutch/help.py`, drawn by the extension. This ticket documents that help and adds a clutch-only rule to `CLAUDE.md` and `AGENTS.md` that keeps help text current, so help does not drift from the code and docs it describes.

## Scope in / Scope out
Scope in:
- `vscode-clutchwork/README.md` gains a `## Help` section. It says where help appears (hover, Details `Next`, the Help command, settings) and that the error-state "Open setup help" link opens this README.
- `docs/how-clutch-works.md` section 2.2's extension paragraph says that the extension's help comes from `clutch/help.py` through the snapshot, that each surface shows what it is plus `Before:` and `After:` lines and a doc link, and that `clutch.help` lists every topic. It also gains one sentence each for `clutch.refreshSeconds` and `clutch.unavailableMenuItems`, so every setting's link has a documented target. No heading in this file is renamed.
- `clutch/docs/host-contract.md` `## VS Code extension` gains one sentence naming the Help command and hover help. No heading in this file is renamed.
- `CLAUDE.md` section A and `AGENTS.md` gain this rule, placed right after the "extension is a thin wrapper" rule and outside the `clutch:core` managed block. Its home is this repo, not `CORE_TEMPLATE`, because it governs clutch's own extension and does not apply to hosts:

  ```
  - **Extension help has one source.** Every extension surface a person sees (view, command, setting, header indicator, and each snapshot vocabulary value) shows help: a short description saying what it is, then what comes before and after it, with a link to the doc section that owns the fact. Help comes from `clutch/help.py`, which reuses a code- or doc-owned string (a status reason, a `clutch/docs/host-running.md` verb row) where one exists and writes text only where none does; settings carry theirs in `package.json` `markdownDescription`. A change that adds an extension surface or vocabulary value, or changes behavior a help entry or its linked section describes, updates that entry in the same change. `tests/unit/test_help.py` and `tests/integration/test_help.py` fail on a missing entry or a dead link; keeping the text true is this rule's job.
    Why: help copied into the extension drifts from the code and docs it describes; the snapshot already carried hand-copied verb descriptions (`engineVerbs`) that restated the run guide (2026-11-13).
  ```

Scope out:
- Code, manifest, and test changes belong to `vscode-help-catalog`, `vscode-help-snapshot` and `vscode-help-surfaces`.
- `clutch/hostfiles.py` `CORE_TEMPLATE` and the `clutch:core` managed block stay as they are.
- `clutch/docs/host-running.md` stays as it is.

## Scope fence
- CLAUDE.md
- AGENTS.md
- docs/how-clutch-works.md
- clutch/docs/host-contract.md
- vscode-clutchwork/README.md

## Acceptance criteria
1. `CLAUDE.md` and `AGENTS.md` each contain the `**Extension help has one source.**` rule exactly as quoted in Scope in, after the `<!-- clutch:core end -->` line in `CLAUDE.md`. This is checked by the first `uv run python -c` command in `## Verification`.
2. The docs name the help: `docs/how-clutch-works.md` names `clutch/help.py`, `Before:`, `After:`, `clutch.help`, `clutch.refreshSeconds`, and `clutch.unavailableMenuItems`; `clutch/docs/host-contract.md` names the Help command; `vscode-clutchwork/README.md` has a `## Help` section. This is checked by the second `uv run python -c` command in `## Verification`.
3. `./dev.py test tests/integration/test_help.py` still passes, so no linked heading was renamed.
4. `./dev.py test` exits 0.

## Verification
```
uv run python -c "import pathlib; c = pathlib.Path('CLAUDE.md').read_text(); a = pathlib.Path('AGENTS.md').read_text(); r = '**Extension help has one source.**'; assert c.index(r) > c.index('<!-- clutch:core end -->') and r in a"
uv run python -c "import pathlib; h = pathlib.Path('docs/how-clutch-works.md').read_text(); assert all(s in h for s in ('clutch/help.py', 'Before:', 'After:', 'clutch.help', 'clutch.refreshSeconds', 'clutch.unavailableMenuItems')); assert 'Help' in pathlib.Path('clutch/docs/host-contract.md').read_text(); assert '## Help' in pathlib.Path('vscode-clutchwork/README.md').read_text()"
./dev.py test tests/integration/test_help.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- the new rule is placed inside the `clutch:core` managed block or in `clutch/hostfiles.py` `CORE_TEMPLATE`;
- the rule text differs from the quoted block;
- a heading in `docs/how-clutch-works.md` or `clutch/docs/host-contract.md` is renamed;
- any code, manifest, or test file changes.

## Time budget
- expected: 30m
- stuck: 60m
