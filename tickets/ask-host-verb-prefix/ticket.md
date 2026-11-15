---
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: rejected
---

## Depends on
none

## Context
- clutch/ask.py
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/running.md
- clutch/specs/ask/review.md
- clutch/specs/ask/diagnose.md
- clutch/specs/ask/box.md
- clutch/specs/ask/drafts.md
- tests/integration/test_ask_drafts.py
- tests/integration/test_ask.py

## Goal / Why
`clutch ask` renders operator prompts from the six templates in `clutch/specs/ask/`, and they hard-code `./dev.py <verb>` (status, stop, kill, lint, drain, suggest, confirm, reject, and so on). `dev.py` exists only in the clutch repo. In any other host, which is the case once clutch is installed from PyPI, the rendered prompt sends the supervising agent to commands that do not exist, so it fails or invents its own argv. After this change a prompt rendered for a repo with no `dev.py` names plain `clutch <verb>` commands, and a prompt rendered for the clutch repo (which has `dev.py`) still names `./dev.py <verb>`, as the repo's command-surface rule requires.

## Scope in / Scope out
In: in each of the six templates under `clutch/specs/ask/`, replace every literal `./dev.py` with a `${verb_cmd}` placeholder. In `clutch/ask.py::render`, pass `verb_cmd` to every `Template.substitute` call (all four branches). Its value is `./dev.py` when `(root / "dev.py").is_file()` is true for the resolved repo root, otherwise `clutch`. Call `is_file()` directly, matching the raw `Path.read_text` template reads already in `ask.py`; add no seam method. Add a unit test file `tests/unit/test_ask_host_verbs.py` that renders against `tmp_path` repos and reads the real templates from disk; it runs the changed lines of `clutch/ask.py`, which has a unit coverage floor. In `tests/integration/test_ask_drafts.py`, line 13 asserts the literal `./dev.py confirm --yes` and `./dev.py reject --yes`. If that test renders against a repo with no `dev.py`, change only those two expectations to match the rendered prefix; otherwise leave the file alone.
Out: the `./dev.py` strings in engine messages (`clutch/stages.py`, `clutch/drain.py`, `clutch/__main__.py`, `clutch/requisition.py`, `clutch/tickets.py`). `CORE_TEMPLATE`. Any new config key. Any wording change in the templates other than the prefix.

## Scope fence
- clutch/ask.py
- clutch/specs/ask
- tests/unit/test_ask_host_verbs.py
- tests/integration/test_ask_drafts.py

## Acceptance criteria
1. `tests/unit/test_ask_host_verbs.py` renders each of the six kinds (`diagnose`, `running`, `review`, `box`, `drafts`, `drain-loop`) against a `tmp_path` repo with no `dev.py`. Each output contains no `./dev.py` and no unsubstituted `${verb_cmd}`. `drain-loop` output contains the backticked forms `` `clutch status` ``, `` `clutch drain` `` and `` `clutch suggest` ``.
2. The same test renders each of the six kinds against a `tmp_path` repo containing a `dev.py` file. Each output contains `./dev.py`, and the backticked forms `` `clutch status` `` and `` `clutch drain` `` are not in any output (the wrong result is a plain `clutch` prefix in the clutch repo). `drain-loop` output contains `` `./dev.py status` `` and `` `./dev.py drain` ``. The test does not match bare `clutch drain`, because the template prose says "the clutch drain".
3. The same test reads each template file under `clutch/specs/ask` and asserts `"./dev.py" not in text`, and `"${verb_cmd}" in text` for the kinds that named verbs before.
4. `./dev.py test tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/unit/test_ask_drain_loop.py tests/unit/test_ask_drafts.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_ask_host_verbs.py tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/unit/test_ask_drain_loop.py tests/unit/test_ask_drafts.py
```

## Definition of rejected
A rendered prompt for a repo without `dev.py` still contains `./dev.py`, or a rendered prompt for the clutch repo loses `./dev.py`. A new config key or a second render path is added. Engine message strings outside `clutch/ask.py` and the templates are edited.

## Time budget
- expected: 25m
- stuck: 60m
