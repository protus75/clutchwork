---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
none

## Context
- clutch/__main__.py::_parser
- clutch/__main__.py::_new
- dev.py
- docs/host-authoring.md
- docs/host-running.md
- tests/unit/test_host_running.py
- tests/integration/test_tickets.py::test_new_prints_bug_evidence_finding
- tests/integration/test_dev.py::test_suggest_forwards_summary

## On-demand
- docs/host-contract.md
- docs/how-clutch-works.md
- tests/integration/test_host_contract.py

## Goal / Why
The host guides (`docs/host-authoring.md`, `docs/host-running.md`, `docs/host-contract.md`) are not in the wheel, which ships only the `clutch` package. A host that installs clutch has no local copy; the only pointers are GitHub links in the README. Agents in a host cannot read them, so they write tickets and run clutch from memory. When this ticket is done, the three guides live inside the installed package (as `clutch/specs/*.md` already do), `clutch docs` prints each one's absolute installed path, and `clutch new` prints the authoring guide's path when the agent needs it. Agents read the guides from the local install, never from a URL. `core-authoring-first` then tells every session to run `clutch docs`.

## Scope in / Scope out
- In: `git mv` the three guides from `docs/` to `clutch/docs/`. Their relative links to each other keep working. Replace each link from a moved guide to `how-clutch-works.md` with plain text, since that file is not shipped.
- In: new verb `clutch docs`, no lock, no arguments, dispatched in `main` before any config or checkout is read, like `migrate-config`. It prints one line per guide: `<absolute path>  <one-line purpose>`, in the order authoring, running, contract. Paths resolve from the `clutch` package directory (`Path(clutch.__file__).parent / "docs"`), never from the repo or cwd. Add the row to the verb table in `clutch/docs/host-running.md` and to `docs/how-clutch-works.md` section 2.1.
- In: create `tests/unit/test_docs_verb.py` with the two unit tests in criterion 5.
- In: `./dev.py docs` forwards to `clutch docs`, like `suggest`; add it to `docs/how-clutch-works.md` section 2.2.
- In: `_new` prints `read the ticket authoring guide before filling sections: <path>` after `authored <rel>`. The refusal for an existing ticket names the same path in its paved road: `read <path>, then edit it in place, or pick a new stem`.
- In: update every other reference to the old paths: `README.md` and `vscode-clutchwork/README.md` links (same GitHub form, new path), the `_parser` description in `clutch/__main__.py` (name `clutch docs`), the `config.yaml` first-line comment, `docs/how-clutch-works.md`, `CLAUDE.md` and `AGENTS.md` outside the `clutch:core` markers if they name a moved file, and the tests that read the guides by path.
- Out: the guides' content beyond the link changes above; `docs/how-clutch-works.md` stays in `docs/`; `CORE_TEMPLATE`; `CLUTCH_PLAN.md`.

## Scope fence
- docs/host-authoring.md
- docs/host-running.md
- docs/host-contract.md
- clutch/docs
- clutch/__main__.py
- dev.py
- docs/how-clutch-works.md
- README.md
- vscode-clutchwork/README.md
- config.yaml
- CLAUDE.md
- AGENTS.md
- tests/unit/test_host_running.py
- tests/integration/test_host_contract.py
- tests/integration/test_tickets.py
- tests/integration/test_cli.py
- tests/integration/test_dev.py
- tests/unit/test_docs_verb.py

## Acceptance criteria
1. The three guides exist under `clutch/docs/` and not under `docs/`, checked by `./dev.py test tests/unit/test_host_running.py tests/unit/test_docs_verb.py tests/integration/test_host_contract.py` reading them at the new paths.
2. A test in `tests/integration/test_cli.py` runs `clutch docs` and asserts three lines, each path absolute, existing, and under `Path(clutch.__file__).parent`, not under the test's repo root, and not a URL.
3. A test in `tests/integration/test_tickets.py` asserts `_new` prints the authoring guide's installed path, and that the already-exists refusal's paved road contains the same path.
4. `tests/integration/test_dev.py` asserts `./dev.py docs` forwards to `["uv", "run", "python", "-m", "clutch", "docs"]`.
5. New `tests/unit/test_docs_verb.py` calls `clutch.__main__.main` with `["docs"]` under `capsys` and asserts three lines in the order authoring, running, contract, each path starting with `str(Path(clutch.__file__).parent / "docs")`. It touches no disk and makes no existence checks, and runs with no `config.yaml` and no state directory, which shows `docs` reads no config and takes no lock. A second test in the same file runs `_new` without disk: it monkeypatches `clutch.__main__.LocalFileSystem`, `template`, `validate_ticket` and `evidence_findings`, and the ticket-exists check. It asserts the printed `read the ticket authoring guide before filling sections: <path>` line and the already-exists refusal's paved road both name the authoring guide's path under `Path(clutch.__file__).parent / "docs"`. These two unit tests run every new `clutch/__main__.py` line, which `clutch/specs/requisition_review.md` requires for a file with a floor in `test-gate.toml`.
6. `git grep -nP "(?<!clutch/)docs/host-(authoring|running|contract)\.md" -- ':!tickets' ':!CLUTCH_PLAN.md'` returns nothing; references to the new `clutch/docs/` paths do not match.

## Verification
```
./dev.py test tests/unit/test_host_running.py tests/unit/test_docs_verb.py tests/integration/test_host_contract.py tests/integration/test_cli.py tests/integration/test_tickets.py tests/integration/test_dev.py
```

## Definition of rejected
A guide's content changes beyond the link changes named above, a printed path is a URL or resolves from the repo or cwd, or `CLUTCH_PLAN.md` is edited.

## Time budget
- expected: 30m
- stuck: 75m
