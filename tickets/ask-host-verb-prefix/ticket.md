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
- chupa/ask.py
- chupa/specs/ask/drain-loop.md
- chupa/specs/ask/running.md
- chupa/specs/ask/review.md
- chupa/specs/ask/diagnose.md
- chupa/specs/ask/box.md
- chupa/specs/ask/drafts.md
- tests/integration/test_ask_drafts.py
- tests/integration/test_ask.py

## Goal / Why
`chupa ask` renders operator prompts from the six templates in `chupa/specs/ask/`, and they hard-code `./dev.py <verb>` (status, stop, kill, lint, drain, suggest, confirm, reject, and so on). `dev.py` exists only in the chupa repo. In any other host, which is the case once chupa is installed from PyPI, the rendered prompt sends the supervising agent to commands that do not exist, so it fails or invents its own argv. After this change a prompt rendered for a repo with no `dev.py` names plain `chupa <verb>` commands, and a prompt rendered for the chupa repo (which has `dev.py`) still names `./dev.py <verb>`, as the repo's command-surface rule requires.

## Scope in / Scope out
In: in each of the six templates under `chupa/specs/ask/`, replace every literal `./dev.py` with a `${verb_cmd}` placeholder. In `chupa/ask.py::render`, pass `verb_cmd` to every `Template.substitute` call (all four branches). Its value is `./dev.py` when `(root / "dev.py").is_file()` is true for the resolved repo root, otherwise `chupa`. Call `is_file()` directly, matching the raw `Path.read_text` template reads already in `ask.py`; add no seam method. Add a unit test file `tests/unit/test_ask_host_verbs.py` that renders against `tmp_path` repos and reads the real templates from disk; it runs the changed lines of `chupa/ask.py`, which has a unit coverage floor. In `tests/integration/test_ask_drafts.py`, line 13 asserts the literal `./dev.py confirm --yes` and `./dev.py reject --yes`. If that test renders against a repo with no `dev.py`, change only those two expectations to match the rendered prefix; otherwise leave the file alone.
Out: the `./dev.py` strings in engine messages (`chupa/stages.py`, `chupa/drain.py`, `chupa/__main__.py`, `chupa/requisition.py`, `chupa/tickets.py`). `CORE_TEMPLATE`. Any new config key. Any wording change in the templates other than the prefix.

## Scope fence
- chupa/ask.py
- chupa/specs/ask
- tests/unit/test_ask_host_verbs.py
- tests/integration/test_ask_drafts.py

## Acceptance criteria
1. `tests/unit/test_ask_host_verbs.py` renders each of the six kinds (`diagnose`, `running`, `review`, `box`, `drafts`, `drain-loop`) against a `tmp_path` repo with no `dev.py`. Each output contains no `./dev.py` and no unsubstituted `${verb_cmd}`. `drain-loop` output contains the backticked forms `` `chupa status` ``, `` `chupa drain` `` and `` `chupa suggest` ``.
2. The same test renders each of the six kinds against a `tmp_path` repo containing a `dev.py` file. Each output contains `./dev.py`, and the backticked forms `` `chupa status` `` and `` `chupa drain` `` are not in any output (the wrong result is a plain `chupa` prefix in the chupa repo). `drain-loop` output contains `` `./dev.py status` `` and `` `./dev.py drain` ``. The test does not match bare `chupa drain`, because the template prose says "the chupa drain".
3. The same test reads each template file under `chupa/specs/ask` and asserts `"./dev.py" not in text`, and `"${verb_cmd}" in text` for the kinds that named verbs before.
4. `./dev.py test tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/unit/test_ask_drain_loop.py tests/unit/test_ask_drafts.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_ask_host_verbs.py tests/integration/test_ask.py tests/integration/test_ask_drafts.py tests/integration/test_ask_drain_loop.py tests/unit/test_ask_drain_loop.py tests/unit/test_ask_drafts.py
```

## Definition of rejected
A rendered prompt for a repo without `dev.py` still contains `./dev.py`, or a rendered prompt for the chupa repo loses `./dev.py`. A new config key or a second render path is added. Engine message strings outside `chupa/ask.py` and the templates are edited.

## Time budget
- expected: 25m
- stuck: 60m
