---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- none

## Runs before
- vscode-command-not-found

## Context
- vscode-clutchwork/package.json
- vscode-clutchwork/README.md
- .vscode/settings.json
- README.md
- docs/host-contract.md#Host contract
- docs/host-contract.md#VS Code extension
- docs/host-contract.md#Instance custody
- docs/host-running.md#Running clutch on a host
- docs/how-clutch-works.md#2. Commands

## Goal / Why
Hosts install clutch from PyPI as a dev dependency of the host project (fungo's `pyproject.toml` has `"clutch>=0.1.2"` in `[dependency-groups] dev`), so the executable is `<host>/.venv/bin/clutch`. The docs say something else in several places. `README.md`, `docs/how-clutch-works.md` section 2, `docs/host-contract.md` (`## VS Code extension`, `## Instance custody`), and `vscode-clutchwork/README.md` each say `uv tool install clutch`, and `docs/host-running.md` runs clutch from a separate checkout through `CLUTCH_CHECKOUT`. The `clutch.command` default `["clutch"]` works only when that venv is on VS Code's PATH, which a VS Code started from a desktop launcher does not have.

After this change:
- the `clutch.command` default is `[".venv/bin/clutch"]`; `execFile` and `ProcessExecution` already run with `cwd` set to the workspace root, and node resolves a relative path containing `/` against `cwd` (checked 2026-11-08: from `cwd` `/home/djp/source/fungo`, `.venv/bin/clutch --help` printed usage);
- one section, `## Install` in `docs/host-contract.md`, states the install model, and every other doc links to it instead of restating it.

Why: every doc that restated the install drifted the same wrong way, and the default fails on a native-Linux VS Code.

## Scope in / Scope out
- In: `vscode-clutchwork/package.json`: `clutch.command` `default` becomes `[".venv/bin/clutch"]`; its `description` says the default is the host's `.venv/bin/clutch`, resolved from the workspace folder.
- In: `docs/host-contract.md`: new `## Install` section directly after the intro paragraph, before `## Copyable configuration`. It says: add clutch to the host project as a dev dependency (`uv add --dev clutch`, pinned as `clutch==<version>` when a specific release is wanted), run `uv sync`, and the executable is `.venv/bin/clutch`; run verbs as `uv run clutch <verb>`. It also says the native Windows venv layout (`.venv\Scripts\clutch.exe`) needs `clutch.command` set explicitly. This is the only place in the repo that states how to install clutch.
- In: `docs/host-contract.md` `## VS Code extension`: drop the `uv tool install clutch` clause and link to `## Install`; say the `clutch.command` default is `[".venv/bin/clutch"]`, resolved relative to the workspace folder.
- In: `docs/host-contract.md` `## Instance custody`: replace `installed with \`uv tool install clutch==<version>\`` with a link to `## Install` (stable is a PyPI release pinned as a host dev dependency); "reinstalling the desired version" becomes "changing the pin, running `uv sync`".
- In: `docs/host-running.md`: the code block becomes `uv run clutch doctor` and `uv run clutch serve`; the intro sentence links to `host-contract.md#install` instead of describing `CLUTCH_CHECKOUT`; "Use the same prefix" stays true for `uv run clutch`.
- In: `README.md`: the install line links to `docs/host-contract.md#install` instead of saying `uv tool install clutch`.
- In: `docs/how-clutch-works.md` section 2: the first sentence links to `host-contract.md#install` instead of saying `uv tool install clutch`; the checkout sentence (`uv run python -m clutch <verb>`) and the `./dev.py` sentence stay.
- In: `vscode-clutchwork/README.md` `## Prerequisites`: link to the `## Install` section of the host contract (absolute GitHub URL `https://github.com/protus75/clutchwork/blob/main/docs/host-contract.md#install`, since the Marketplace page renders this README); say the default `clutch.command` is `[".venv/bin/clutch"]` and when to override it.
- In: delete `.vscode/settings.json`; its only key is `"clutch.command": ["uv", "run", "clutch"]`, which the new default makes unnecessary because this repo's `.venv/bin/clutch` exists after `uv sync`.
- Out:
  - `vscode-clutchwork/extension.js` and `vscode-clutchwork/media/`; the missing-command error message is `vscode-command-not-found`;
  - `dev.py`;
  - engine code under `clutch/`;
  - `CLUTCH_PLAN.md`;
  - bumping the extension or clutch version.

## Scope fence
- vscode-clutchwork/package.json
- vscode-clutchwork/README.md
- docs/host-contract.md
- docs/host-running.md
- docs/how-clutch-works.md
- README.md
- .vscode/settings.json

## Acceptance criteria
1. `vscode-clutchwork/package.json` `contributes.configuration.properties["clutch.command"].default` is exactly `[".venv/bin/clutch"]`, not `["clutch"]`.
2. `git grep -n "uv tool install" -- README.md docs vscode-clutchwork` prints nothing: no doc restates the old install (`CLUTCH_PLAN.md` is frozen and keeps its text).
3. `git grep -n "CLUTCH_CHECKOUT" -- docs README.md` prints nothing.
4. `docs/host-contract.md` has exactly one `## Install` heading, placed before `## Copyable configuration`, and it contains `uv add --dev clutch`, `.venv/bin/clutch`, and `uv run clutch`.
5. `README.md`, `docs/how-clutch-works.md`, `docs/host-running.md`, and `vscode-clutchwork/README.md` each contain a link whose target ends in `host-contract.md#install`.
6. `git grep -n "uv add --dev clutch" -- README.md docs vscode-clutchwork` matches only `docs/host-contract.md`.
7. `.vscode/settings.json` does not exist.
8. `./dev.py test` exits 0.

## Verification
```
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- `vscode-clutchwork/extension.js` changes;
- the default is an absolute path, or the extension resolves the path itself instead of relying on `cwd`;
- a doc other than `docs/host-contract.md` states the install steps instead of linking;
- `CLUTCH_PLAN.md` changes.

## Time budget
- expected: 20m
- stuck: 60m
