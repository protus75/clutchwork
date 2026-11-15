---
state: confirmed
source: human
priority: P1
kind: bug
---

## Depends on
- verdict-submitted-message-verb

## Context
- clutch/requisition.py::review_ticket
- clutch/tickets.py
- clutch/drain.py
- clutch/stages.py

## Goal / Why
Six engine-emitted operator strings in the `clutch` package tell the operator to run `./dev.py`, which is this repo's own launcher and exists in no other host (evidence: `evidence/engine-dev-py.txt`). `verdict-submitted-message-verb` fixes the seventh, the one an operator hit in the host repo `fungo`; these six are the same defect waiting on whoever reads a refusal, a Reject-queue paved road, a diff-budget park, a coverage-map snag, or a regression-protocol lint finding in a host. Three tests pin the wrong strings as correct, and no check forbids a new one, so the defect recurs the next time anyone writes an operator message.

After this change every operator string the `clutch` package emits names the `clutch` verb, in backticks, and a test fails when any file under `clutch/` outside `clutch/docs/` names `./dev.py` again, whatever its extension. `clutch/docs/` is pruned only until `dev-py-dev-tasks-only` clears its five remaining mentions and widens the scan to the whole package. `clutch/docs/` keeps its `clutch X` (`./dev.py X` in this repo) form, which is correct, and `clutch/specs/` is untouched.

## Scope in / Scope out
- In: `clutch/__main__.py` line 327, the interactive-terminal refusal's paved road: ``a human runs this in a terminal: `clutch confirm|reject <stem>` ``. Nothing else in the file changes; the submitted-message print at line 1011 is fixed by `verdict-submitted-message-verb`, which this ticket depends on, so no `./dev.py` is left in the file for the scan to find.
- In: `clutch/requisition.py`, the coverage-map snag's paved road: ``run `clutch covmap` ``.
- In: `clutch/drain.py` line 706, the diff-budget road: `` ...or retire it with `clutch reject {stem}` ``.
- In: `clutch/drain.py` line 719 and `clutch/stages.py` line 305, both ticket-edit roads, which share one wording: `` review the change to <path>, then keep (`clutch confirm <stem>`) or kill (`clutch reject <stem>`) ``. The two stay worded identically so the `tests/integration/test_drain.py` assertion holds against whichever one produces the finding.
- In: `clutch/tickets.py` line 573, the regression-protocol lint road: ``run a reproducer under a `carries:` prefix; a bare test runner such as `pytest -q` does not speak the regression protocol``. That matches `clutch/docs/host-authoring.md`, which already says a bare test runner does not speak the protocol, and drops the `./dev.py test` example rather than renaming it, because `clutch` has no `test` verb. The substring `does not speak the regression protocol` is kept, so the existing assertion in `tests/unit/test_ticket_lint_rules.py` line 65 still holds.
- In: `tests/integration/test_reject_queue.py` line 220, `tests/integration/test_requisition.py` line 327, and `tests/integration/test_drain.py` line 1417: each expected string becomes the new one. These are the pins of the changed strings.
- In: `tests/unit/test_ticket_lint_rules.py`, `test_regression_requires_carried_path_not_runner_denylist`: add one assertion pinning the whole new `clutch/tickets.py` road string, so the changed line is covered exactly and not only by a substring.
- In: new `tests/regress_engine_text_verbs.py`, the carried reproducer, built like `tests/regress_dev_test_args.py`. It resolves the repo root from its own path and scans the same files the check does: every file under `clutch/`, pruning `clutch/docs/` and `__pycache__`. It prints `{"regression_result": "defect"}` with exit 1 when any scanned file contains `dev.py` (listing the hits on stderr), `{"regression_result": "pass"}` with exit 0 when none does, and `{"regression_result": "error"}` with exit 2 when the `clutch` directory is missing, holds no scannable file, or holds a file it cannot decode as UTF-8, so it reports `error` rather than `pass` when its own input is absent or unreadable. Nothing but the one JSON object goes to stdout.
- In: new `tests/integration/test_engine_text_verbs.py`, the check that stops the class: `test_no_engine_text_names_dev_py` asserts no scanned file contains the substring `dev.py`, failing with the paved road "name the `clutch <verb>` the operator runs in backticks; `./dev.py` exists only in the clutch repo" and the offending `path:line` of each hit. It walks every file under the repo's `clutch/` directory, pruning the `clutch/docs/` subtree and any `__pycache__` directory, and reads each remaining file as UTF-8. A file it cannot decode fails with a message saying to prune it deliberately, so a new binary is noticed rather than silently skipped. It walks at runtime rather than listing paths, so a file or file type added later is covered without editing it. It covers the whole package, not just Python: the 61 `.py`, 14 `.md`, and 1 `.json` tracked files outside `clutch/docs/`, so a `./dev.py` written into a prompt spec is caught too. It lives under `tests/integration/` because it reads repo files from disk.
- Out: editing `clutch/specs/ask/*.md`. Their 18 `./dev.py` occurrences were already swapped to `clutch <verb>` directly on main on 2026-11-14, together with the `CLAUDE.md` section B note, so nothing is left to sweep there; the widened check guards them from here on but changes no byte of them.
- Out: editing `clutch/docs/`, which the scan prunes for now. Its two guides hold five `./dev.py` mentions (`host-authoring.md` lines 12, 16, 25 and `host-qwen.md` lines 49, 66), each a "in this repo, use `./dev.py X`" note beside the `clutch X` verb. Those notes are true until `./dev.py` loses those subcommands, so scanning the directory now would fail on text that is still correct. The prune is temporary and has a named release: `dev-py-dev-tasks-only` deletes all five mentions and removes the prune in the same change, after which the scan covers the whole package. These guides install into every host, so they must not name `./dev.py` once it no longer runs those verbs.
- Out: `clutch/docs/`, where naming `./dev.py` for this repo beside the `clutch` verb is the documented form; `dev.py` itself and `tests/integration/test_dev.py`, which are about this repo's launcher; the `prog="python -m clutch"` parser name; `tests/unit/test_readme.py`; and `clutch/__main__.py` line 1011, which `verdict-submitted-message-verb` owns.

## Scope fence
- clutch/__main__.py
- clutch/requisition.py
- clutch/drain.py
- clutch/stages.py
- clutch/tickets.py
- tests/integration/test_reject_queue.py
- tests/integration/test_requisition.py
- tests/integration/test_drain.py
- tests/integration/test_engine_text_verbs.py
- tests/unit/test_ticket_lint_rules.py
- tests/regress_engine_text_verbs.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_engine_text_verbs.py` exits 0 and runs `test_no_engine_text_names_dev_py`. The test fails when any file under `clutch/` outside `clutch/docs/` contains `dev.py`, whatever its extension, and its failure message names each offending `path:line`. It fails if `clutch/docs/` is scanned, because that text is correct, and fails if an undecodable file is silently skipped.
2. `./dev.py test tests/integration/test_reject_queue.py tests/integration/test_requisition.py tests/integration/test_drain.py tests/unit/test_ticket_lint_rules.py` exits 0 with the four pinned strings replaced. Each test fails if its paved road still names `./dev.py`, and fails if the `clutch` verb is printed without its backticks.
3. `uv run python tests/regress_engine_text_verbs.py` prints `{"regression_result": "pass"}` and exits 0 on the branch head.
4. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_engine_text_verbs.py
./dev.py test tests/integration/test_reject_queue.py tests/integration/test_requisition.py tests/integration/test_drain.py tests/unit/test_ticket_lint_rules.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- a string is dropped or reworded beyond swapping `./dev.py <verb>` for a backticked `clutch <verb>`, except `clutch/tickets.py` line 573, where the example becomes `pytest -q`;
- a replacement names a path, a launcher, or an interpreter (`.venv/bin/clutch`, `python -m clutch`, `uv run`) instead of the bare `clutch` verb;
- a per-host invocation value, config field, or `./dev.py`-detection is added anywhere;
- `clutch/specs/` or `clutch/docs/` is edited;
- `clutch/__main__.py` line 1011 is edited here instead of in `verdict-submitted-message-verb`;
- a pinning test is weakened to a substring or regex match instead of being updated;
- the reproducer prints `pass` on the merge base.

## Time budget
- expected: 25m
- stuck: 60m

## Regression
```
uv run python tests/regress_engine_text_verbs.py
```
- carries: tests/regress_engine_text_verbs.py
