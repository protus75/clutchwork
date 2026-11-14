---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
none

## Runs before
- dev-py-dev-tasks-only

## Context
- chupa/__main__.py::_parser
- chupa/__main__.py::main

## Goal / Why
`chupa confirm`, `chupa reject`, and `chupa review` each take exactly one stem: `_parser` declares `add_argument("stem")` for all three. `dev.py` is the only way to act on several, because its `confirm`/`reject`/`review` branch loops over `args.stems` and calls the engine once per stem. That is a capability living in this repo's launcher, so a host operator cannot confirm two tickets in one command, and `dev-py-dev-tasks-only` cannot delete the launcher's engine pass-throughs without losing it.

After this change the three verbs each accept one or more stems and process them in order, so `chupa confirm a b` does what `./dev.py confirm a b` does today, in every host.

## Scope in / Scope out
- In: `chupa/__main__.py` `_parser`: the `confirm` and `reject` subparsers and the `review` subparser each replace `add_argument("stem")` with `add_argument("stems", nargs="+")`. The `--yes` and `--extension` flags on the verdict verbs are unchanged.
- In: `chupa/__main__.py` `main`, the dispatch at lines 613-616: each verb loops over `args.stems` in the given order, running the existing single-stem call (`_verdict` for a verdict, `_review` for review) once per stem. It stops at the first stem whose call returns non-zero or raises, and returns that stem's exit code; with every stem successful it returns 0. A `runner.Refusal` keeps propagating to the existing handler, so a refused stem stops the rest, which is what `dev.py`'s `run()` does today when a child exits non-zero. The per-stem functions `_verdict` and `_review` keep their single-stem signatures and are not touched.
- In: `chupa/__main__.py` line 324, the interactive-terminal check for `confirm`/`reject`: it still runs once before any stem, because it tests the terminal, not a stem.
- In: `tests/integration/test_control_cli.py`: one new test asserting that `main(["confirm", first, second], ...)` with a terminal answering `y` acts on both stems in order, and that when the first stem refuses, the second is never reached. It rules out the wrong results "only the first stem acted on" and "the second stem acted on after the first refused".
- In: `tests/unit/test_verdict_extension.py`: `test_request_actor_and_parser` line 34 asserts `args.stem == "sample"`; it becomes `args.stems == ["sample"]`. Add `test_verdict_and_review_loop_over_stems`, which must live in `tests/unit/` because `chupa/__main__.py` has a unit coverage floor of 13 in `test-gate.toml` and the hard covgate measures `tests/unit` only, so the two new loops have to run there. It monkeypatches `entry.load_config`, `entry.Journal`, `entry.Git`, `entry.CommitLock`, and `entry.SubprocessExec` so nothing touches disk, and monkeypatches `entry._verdict` and `entry._review` with recording fakes. It then calls `entry.main(["confirm", "a", "b", "--yes"])` and `entry.main(["review", "a", "b"])` and asserts each fake received `"a"` then `"b"`; with the first fake returning a non-zero code it asserts `main` returns that code and the fake was never called for `"b"`. It also asserts `_parser().parse_args(["confirm", "a", "b"]).stems == ["a", "b"]`, which raises `SystemExit` on the current single-stem parser.
- Out: `dev.py`, which keeps its own loop until `dev-py-dev-tasks-only` deletes the branch; the two launchers behave identically in the meantime. Out: every other verb's arity, including `run`, `order`, `new`, and `prompt` (`prompt` already takes `stems` and sets `args.stem = args.stems[0]` at line 529; it is not changed here). Out: making a verdict atomic across stems, a summary line, or a `--continue-on-error` flag; nothing has asked for them.

## Scope fence
- chupa/__main__.py
- tests/integration/test_control_cli.py
- tests/unit/test_verdict_extension.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_verdict_extension.py` exits 0 and runs `test_verdict_and_review_loop_over_stems`. It fails if `_parser().parse_args(["confirm", "a", "b"])` raises `SystemExit` or yields `stems == ["a"]`, if either loop acts on only the first stem, or if `"b"` is acted on after `"a"` returned non-zero. Because it drives `entry.main`, both new dispatch loops run under the unit suite that the coverage gate measures.
2. `./dev.py test tests/integration/test_control_cli.py` exits 0. The new multi-stem test fails if only the first stem is acted on, and fails if a stem after a refusing one is acted on.
3. `./dev.py test tests/integration/test_reject_queue.py tests/integration/test_cli.py` exits 0, so existing single-stem `main(["confirm", stem])` and `main(["review", stem])` callers still work unchanged.
4. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_verdict_extension.py
./dev.py test tests/integration/test_control_cli.py
./dev.py test tests/integration/test_reject_queue.py tests/integration/test_cli.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- `_verdict` or `_review` is changed to take a list of stems instead of being called once per stem;
- a stem after a refused or failing stem is still acted on;
- a single-stem invocation changes its exit code, output, or journal writes;
- a flag, summary line, or config knob is added beyond the `nargs="+"` change and the loop;
- `dev.py` is edited here.

## Time budget
- expected: 20m
- stuck: 50m
