---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
none

## Runs before
- engine-text-names-clutch-verbs

## Context
- clutch/__main__.py::_verdict
- tests/unit/test_verdict_extension.py
- tests/regress_dev_test_args.py

## Goal / Why
After a `confirm` or `reject` submitted to a running engine, `clutch/__main__.py::_verdict` prints `<verb> submitted: <id> -- ./dev.py status shows the outcome`. `./dev.py` is this repo's own launcher and does not exist in any other host, so in the host repo `fungo` the operator was told to run a file that is not there (evidence: `evidence/confirm-submitted.txt`). The same clause also runs the command and the prose together as one unpunctuated phrase, so the operator cannot see where the command ends.

After this change the clause names the `clutch status` verb, which every host has, and sets the command off in backticks from the prose around it:

```
confirm submitted: d8cdcd906b374c46bc7b46cc9f9978a3 -- `clutch status` shows the outcome
```

## Scope in / Scope out
- In: `clutch/__main__.py`, the `print` at the end of `_verdict`: the trailing clause becomes `` -- `clutch status` shows the outcome ``. The `<verb> submitted: <request_id>` prefix, the return value, and everything else `_verdict` does are unchanged. Nothing else in the file changes.
- In: `tests/unit/test_verdict_submitted_message.py`: new `test_verdict_submitted_names_the_clutch_verb`. It calls `clutch.__main__._verdict` directly with a stub checkout (`repo` a `tmp_path`, `journal.read()` returning `[]`, `config.state_dir` under `tmp_path`, `git` and `fs` unused), with `runner.verdict` raising `LockHeld(path, {"verb": "drain"})`, `runner.ticket_pending` returning `False`, `control.read_active` returning `("life-1", None)`, `control.publish_request` a no-op, and `uuid4` returning a fixed hex. It asserts the captured stdout's last line is exactly ``confirm submitted: <fixed hex> -- `clutch status` shows the outcome``, which rules out the wrong results `-- ./dev.py status shows the outcome` and an unbackticked `-- clutch status shows the outcome`.
- In: new `tests/regress_verdict_submitted_message.py`, the carried reproducer, built like `tests/regress_dev_test_args.py`. It puts the repo root on `sys.path`, imports `clutch.__main__`, drives `_verdict` through the same stubs as the unit test under `contextlib.redirect_stdout`, and decides on the captured line:
  - last line exactly ``confirm submitted: <fixed hex> -- `clutch status` shows the outcome``: prints `{"regression_result": "pass"}` and exits 0.
  - any other submitted line, including the `./dev.py` form: prints `{"regression_result": "defect"}` and exits 1.
  - anything else, including an import or stub failure, or no submitted line at all: the traceback goes to stderr, and it prints `{"regression_result": "error"}` and exits 2.
  - Nothing but the one JSON object goes to stdout; `_verdict` prints to stdout, so the reproducer redirects stdout around the call and prints the result after.
- Out: the six other `./dev.py` strings in engine code (`clutch/__main__.py` line 327, `clutch/drain.py`, `clutch/stages.py`, `clutch/requisition.py`, `clutch/tickets.py`) and the `./dev.py` strings in `clutch/specs/ask/`; `engine-text-names-clutch-verbs` fixes those and adds the check that keeps them out. Out: the `prog="python -m clutch"` parser name, the `<stem>: <preview>` line, the `[y/N]` prompt, and `clutch/docs/`, where naming `./dev.py` for this repo beside the `clutch` verb is correct.

## Scope fence
- clutch/__main__.py
- tests/unit/test_verdict_submitted_message.py
- tests/regress_verdict_submitted_message.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_verdict_submitted_message.py` exits 0 and runs `test_verdict_submitted_names_the_clutch_verb`. The test fails if the clause still names `./dev.py`, or if `clutch status` is printed without its backticks.
2. `uv run python tests/regress_verdict_submitted_message.py` prints `{"regression_result": "pass"}` and exits 0 on the branch head.
3. `./dev.py test tests/integration/test_control_cli.py` exits 0, so the existing `"<verb> submitted:"` assertions still hold.
4. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_verdict_submitted_message.py
./dev.py test tests/integration/test_control_cli.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- anything in `_verdict` other than the trailing clause of that one `print` changes;
- the clause names a path, a launcher, or an interpreter instead of the `clutch status` verb;
- another `./dev.py` string in engine code is edited here instead of in `engine-text-names-clutch-verbs`;
- the reproducer prints `pass` on the merge base.

## Time budget
- expected: 15m
- stuck: 45m

## Regression
```
uv run python tests/regress_verdict_submitted_message.py
```
- carries: tests/regress_verdict_submitted_message.py
