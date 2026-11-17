---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- README.md
- tests/unit/test_readme.py
- clutch/docs/host-contract.md#Install
- clutch/docs/host-contract.md#Onboarding a host
- clutch/docs/host-running.md

## Goal / Why
Roadmap row 141, an owner request of 2026-11-17. `README.md` is the PyPI page (`pyproject.toml` `readme = "README.md"`) and the first thing a host reads, but at HEAD:
- its `## Developing clutch` section lists host actions (`uv run clutch new`, `lint`, `review`, `drain`, `status`, `confirm`, `reject`, `kill`) as if they were work on clutch itself, and ends with a pointer to the verb table in `docs/how-clutch-works.md`;
- its `## Docs` section links the guides on GitHub but never says they ship inside the installed package, where `uv run clutch docs` prints their local paths, and it leaves out the two shipped provider guides `clutch/docs/host-qwen.md` and `clutch/docs/host-gemini.md`;
- its `## Set up a host` section skips `uv run clutch probe`, which step 5 of `clutch/docs/host-contract.md` "Onboarding a host" runs beside `doctor`.

When this ticket is done, `README.md` is written host-first in this order: what clutch is (the existing intro), install, set up a host, author and run tickets, observe and decide, the VS Code extension, and where the shipped guides are (`uv run clutch docs`). `## Developing clutch` comes last and covers only work on clutch's own repository: the `./dev.py` tasks, the `uv run clutch` prefix, and the note that `CLUTCH_PLAN.md` is frozen. A host reading the PyPI page no longer takes host actions for clutch development, and an agent learns that its guides are on disk.

## Scope in / Scope out
In: rewrite `README.md` only. Keep every existing fact unless this list drops it; move content, do not reword it beyond what the move needs. Top to bottom:
- Title, tagline, the intro paragraph, and the `[GitHub repository](https://github.com/protus75/clutchwork)` link: unchanged.
- `## Install`: unchanged (`uv add --dev clutchwork`, `uv sync`, `uv run clutch install claude codex`, `uv run clutch init-config --write`, the copyable configuration link).
- `## Set up a host`: the current paragraph, with `uv run clutch probe` run beside `uv run clutch doctor` before `uv run clutch core`. Below it, a `sh` code block holding the `# Setup` lines of today's `## Commands` block plus `uv run clutch probe   # probe declared providers and models`.
- `## Author and run tickets`: steps 1-4 of today's "The working loop" (open a chat agent, plan, turn the plan into tickets with `clutch new`, `clutch lint` and `clutch review`, drain or serve); the paragraph "One unattended drain ran about 30 tickets in about 4 hours ..."; a `sh` code block holding the `# Authoring` and `# Running` lines of today's `## Commands` block; then the sentence "Stop `serve` before `drain` or `run` ..." with its host run guide link.
- `## Observe and decide`: steps 5-7 of today's "The working loop" (supervise with `clutch status` and `clutch watch`, the Suggestion Box and Reject queue, the `clutch confirm` and `clutch reject` judgment calls); the paragraph with the measured Suggestion Box figures ("32 of 389 ..."); the three "For example, ask your chat agent" lines; and a `sh` code block holding the `# Observing` and `# Decisions` lines of today's `## Commands` block. The `## Commands` and `## The working loop` headings go away.
- `## VS Code extension`: unchanged.
- `## Guides` (replaces `## Docs`): one sentence that the host guides ship inside the installed package and `uv run clutch docs` prints each one's local path, so agents read the copy that matches the installed version. Then the link list: the existing three host guide links, a link to `https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-qwen.md` (local qwen provider setup), a link to `https://github.com/protus75/clutchwork/blob/main/clutch/docs/host-gemini.md` (gemini provider setup), and the existing "How clutch works" link.
- `## Developing clutch`, last: one sentence that the section is for working on clutch's own repository, where every clutch verb runs from the checkout as `uv run clutch <verb>`, as in a host; an indented block of the four `./dev.py` tasks from the `dev.py` docstring with their comments (`./dev.py` the full suite, `./dev.py test [args]` the suite or the named tests, `./dev.py vscode` package and install the vscode-clutchwork extension, `./dev.py vscode-package` build a VSIX for Marketplace upload); and the existing sentence that the bootstrap plan is a frozen record. The list of `uv run clutch` verb lines and the closing "Every clutch verb is listed in how clutch works, section 2" line are removed; the host run guide link in `## Author and run tickets` and the "How clutch works" link in `## Guides` already cover them.

Every link stays an absolute `https://` URL, and every `./dev.py` mention stays inside `## Developing clutch`, as `tests/unit/test_readme.py` requires. Commands keep their names at the base commit. Roadmap rows 130-140 rename commands into groups later and update `README.md` themselves. If one of them has merged before this ticket runs, write that command's new name; `test_clutch_verbs_exist` checks every `uv run clutch` word against the parser.

Out: the shipped host guides `clutch/docs/host-authoring.md`, `host-contract.md`, `host-running.md`, `host-qwen.md`, `host-gemini.md` and `vscode-clutchwork/README.md`, checked at authoring on 2026-11-17 and dropped. None of them mentions `./dev.py` or presents a host action as clutch development. `host-contract.md` "Install" gives the same steps as `README.md` `## Install` (`uv add --dev clutchwork`, `uv sync`, `uv run clutch install`, `uv run clutch init-config --write`). The extension README links to that section rather than repeating it. Every command they name is a verb of `clutch/__main__.py` at HEAD. Because this ticket keeps the README's install steps and command names, they still agree after it. Also out: `tests/unit/test_readme.py` and every other test (no new test of document wording), `docs/how-clutch-works.md`, `CLUTCH_PLAN.md`, `dev.py`, and all code.

## Scope fence
- README.md

## Acceptance criteria
1. `grep -n '^## ' README.md` prints exactly these headings in this order: `## Install`, `## Set up a host`, `## Author and run tickets`, `## Observe and decide`, `## VS Code extension`, `## Guides`, `## Developing clutch`. Ruled out: a leftover `## Commands`, `## The working loop` or `## Docs` heading, and `## Developing clutch` anywhere but last.
2. `sed -n '/^## Developing clutch/,$p' README.md | grep -o 'uv run clutch [^ `]*' | sort -u` prints only `uv run clutch <verb>`, and the same section contains `./dev.py test`, `./dev.py vscode`, `./dev.py vscode-package` and `CLUTCH_PLAN.md`. Ruled out: any host action (`new`, `lint`, `review`, `drain`, `status`, `confirm`, `reject`, `kill`) still listed as clutch development.
3. `grep -o 'uv run clutch [a-z-]*' README.md | sort -u` includes every verb of today's `## Commands` block plus `probe` and `docs`, each under its name at the base commit: `init-config`, `install`, `update-config`, `doctor`, `probe`, `core`, `new`, `lint`, `review`, `order`, `suggest`, `issue`, `drain`, `serve`, `run`, `stop`, `kill`, `pause`, `resume`, `status`, `watch`, `stats`, `confirm`, `reject`, `docs`. Ruled out: a command dropped from the host sections while it was moved out of `## Developing clutch`.
4. `sed -n '/^## Guides/,/^## Developing clutch/p' README.md` contains `uv run clutch docs` and links to all five of `clutch/docs/host-running.md`, `host-authoring.md`, `host-contract.md`, `host-qwen.md` and `host-gemini.md`. Ruled out: a guides section that names only GitHub copies, or one that misses a shipped guide.
5. `sed -n '/^## Install/,/^## Set up a host/p' README.md` still holds `uv add --dev clutchwork`, `uv sync`, `uv run clutch install claude codex` and `uv run clutch init-config --write`, and `uv run python tests/regress_install_docs_name.py` prints `{"regression_result": "pass"}` and exits 0. Ruled out: install steps that drift from `clutch/docs/host-contract.md` "Install".
6. `grep -n 'about 30 tickets in about 4 hours' README.md` and `grep -n '32 of 389' README.md` each print one line. Ruled out: the measured figures, which `docs/roadmap-driver-plan.md` cites from `README.md`, lost in the move.
7. `./dev.py test tests/unit/test_readme.py` exits 0 with that file unchanged. Ruled out: a relative link, a `./dev.py` mention before `## Developing clutch`, or a `uv run clutch` word the parser does not know.

## Verification
```
./dev.py test tests/unit/test_readme.py
uv run python tests/regress_install_docs_name.py
```

## Definition of rejected
The branch is rejected if it changes any file other than `README.md`, adds or edits a test, drops a fact this ticket says to keep (an install step, a command line, the measured figures, the example asks, the extension section) instead of moving it, or leaves a `uv run clutch` verb other than the `<verb>` placeholder in `## Developing clutch`, even if the tests pass.

## Time budget
- expected: 8m
- stuck: 16m
