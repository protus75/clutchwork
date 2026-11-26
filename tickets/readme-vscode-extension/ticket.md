---
state: rejected
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Context
- README.md#VS Code extension
- vscode-clutchwork/README.md
- vscode-clutchwork/package.json
- clutch/docs/host-contract.md#VS Code extension
- docs/how-clutch-works.md#2.2
- tests/unit/test_readme.py

## Goal / Why
Expand the `## VS Code extension` section of `README.md` so host users have clear, self-contained instructions for installing, configuring, and using the ClutchWork VS Code extension (`chunkydragon.vscode-clutchwork`). Today `README.md` devotes only two sentences to the extension, leaving out installation methods, prerequisites, view usage, actions, settings, and troubleshooting that users otherwise have to find in `vscode-clutchwork/README.md` or `docs/how-clutch-works.md`.

## Boundary contract
none
- reason: documentation-only expansion of the existing `## VS Code extension` section in `README.md` with no code, CLI, or extension behavior change

## Scope in / Scope out
Scope in:
- Expand only the `## VS Code extension` section of `README.md` to cover:
  - Prerequisites: a workspace containing `tickets/` and an installed `clutch` CLI, plus the note that under WSL or Remote-SSH the extension runs on the remote side where the repo and `clutch` live.
  - Installation: VS Code Marketplace (`chunkydragon.vscode-clutchwork`, including `code --install-extension chunkydragon.vscode-clutchwork`) and Install from VSIX for Cursor and VSCodium. Keep every Markdown link an absolute `https://` URL and keep `./dev.py` commands out of this section.
  - Usage: opening the ClutchWork Activity Bar icon; the five views (`Tickets` dependency graph, `Details`, `Recent Steps`, `Suggestion Box`, `Stats`); starting and stopping the engine with the play/stop button and `Engine…` picker; ticket context-menu actions (open, review, lint, run, confirm/reject, priority, run before) and Suggestion Box actions (triage, dismiss); built-in help (hover help, the `Help` command, and `Ticket lifecycle` diagram); and troubleshooting (missing command -> set `clutch.command`; `cannot draw the clutch snapshot` -> update the extension and reload the window).
  - Settings from `vscode-clutchwork/package.json`: `clutch.command` (default `[".venv/bin/clutch"]`, override when installed elsewhere or on native Windows), `clutch.playAction` (`drain` or `serve`), `clutch.statsWindow` (default `7d`), `clutch.refreshSeconds` (default `15`; `0` disables timed refresh), and `clutch.unavailableMenuItems` (`disable` or `hide`).
- Add `tests/integration/test_readme_vscode_extension.py` reading `README.md` via `Path(__file__)` and asserting that `## VS Code extension` documents installation, prerequisites, views, controls/actions, all five settings, and help/troubleshooting.

Scope out:
- All other sections of `README.md` (including `## Antigravity plugin` and `## Developing clutch`).
- Any files under `vscode-clutchwork/`, `clutch/`, or `docs/`.

## Scope fence
- README.md
- tests/integration/test_readme_vscode_extension.py

## Acceptance criteria
1. `README.md` under `## VS Code extension` documents prerequisites (`tickets/` workspace, installed `clutch`, WSL/Remote-SSH) and installation (`chunkydragon.vscode-clutchwork` on the VS Code Marketplace, `code --install-extension`, and VSIX for Cursor/VSCodium), verified by `./dev.py test tests/integration/test_readme_vscode_extension.py` (which fails if any of those topics are absent from the section).
2. `README.md` under `## VS Code extension` documents usage (ClutchWork Activity Bar, `Tickets`, `Details`, `Recent Steps`, `Suggestion Box`, `Stats`, play/stop and `Engine…` controls, ticket and Suggestion Box actions, hover/`Help` command, and `cannot draw the clutch snapshot` troubleshooting) and all five settings (`clutch.command`, `clutch.playAction`, `clutch.statsWindow`, `clutch.refreshSeconds`, `clutch.unavailableMenuItems`), verified by `./dev.py test tests/integration/test_readme_vscode_extension.py` (which fails if any view, setting, or troubleshooting note is missing).
3. All existing top-level README invariants (absolute `https://` links only, `./dev.py` commands restricted to `## Developing clutch`, GitHub project link, and valid `uv run clutch` verbs) continue to hold, verified by `./dev.py test tests/unit/test_readme.py`.

## Verification
```
./dev.py test tests/unit/test_readme.py tests/integration/test_readme_vscode_extension.py
```

## Definition of rejected
- Any section of `README.md` outside `## VS Code extension` is changed.
- Any relative Markdown link or `./dev.py` command is added inside `## VS Code extension`.
- Any documented setting name, default, or extension behavior contradicts `vscode-clutchwork/package.json`, `vscode-clutchwork/README.md`, or `docs/how-clutch-works.md`.

## Time budget
- expected: 5m
- stuck: 10m
