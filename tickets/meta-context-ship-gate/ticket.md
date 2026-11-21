---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
- meta-docs-tests-clean

## Context
- clutch/__main__.py::_run_context_suggest
- clutch/__main__.py::_parser
- tests/unit/test_context_suggest_verb.py::test_outcomes
- tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks
- docs/roadmap.md#0.5.0
- docs/how-clutch-works.md#14. Project index

## Goal / Why
Roadmap row 207 (`meta-context-ship-gate`), part 2 of 2. The roadmap section 1 0.5.0 ship clause says this repo's docs and tests carry filled meta blocks and `context suggest` returns selectors for a real ticket, and its gate block (docs/roadmap.md#0.5.0) has no command for either, so `clutch roadmap gate 0.5.0` can pass with both false. After this ticket the block checks both.

Meta: the block gains `uv run clutch meta check docs clutch/docs tests` (exit 0 when no file has a `missing`, `empty_purpose` or `drifted` finding, exit 1 otherwise; read from `clutch/meta.py::check` and the verb's help). This is the gate, not a ticket Verification, so it is the one place a multi-root check belongs.

Context suggest: `clutch context suggest <stem>` exits 0 for both "suggested" and "none", and 2 for `no_index`, so as it stands no gate command can fail on empty output. Smallest change that can: a boolean flag `--require` on `context suggest` that makes the "none" outcome exit 1 (still printing `context suggest: none`); every other outcome and exit code stays. Existing behavior has no other way to fail on empty output, and a wrapper verb would add a second command for one condition. The block runs `uv run clutch index build` first (the index is `<state_dir>/index.duckdb`; without it the verb exits 2 with no_index), then `uv run clutch context suggest context-suggest --require`, naming the merged ticket `context-suggest` as the real ticket (stable: its Goal and Scope fence are fixed). The implementer proves on this checkout that this exact command prints `context suggest: suggested` and exits 0; if it prints none, choose another merged stem whose command does and say so in the run record.

New 0.5.0 gate order: `roadmap merged --release 0.5.0`, `meta check`, `index build`, `context suggest ... --require`, `./dev.py test`, `roadmap accept 0.5.0` (the test requires `./dev.py test` second to last and `accept` last).

## Boundary contract
### context suggest verb
- disposition: extend
- owner: clutch/__main__.py (`_run_context_suggest`, the `context suggest` parser)
- consumers: the 0.5.0 gate block; people and Author running the verb (default behavior unchanged)
- observable change: new optional flag `--require`; with it, an empty result prints `context suggest: none` and exits 1; without it, exit 0 as before
- compatibility: every existing invocation, output line and exit code (0 suggested or none, 2 refused, no_index, index_unreadable) is unchanged
- acceptance: the new unit test and the existing `tests/unit/test_context_suggest_verb.py` both pass
- tests: new tests/unit/test_context_suggest_require.py
- post-merge source of truth: clutch/__main__.py

### 0.5.0 gate block
- disposition: extend
- owner: docs/roadmap.md (0.5.0 `gate` block), parsed by `clutch/roadmap.py::gates`
- consumers: `clutch roadmap gate 0.5.0`, the roadmap driver, `roadmap status`
- observable change: the block lists four more argv commands between `roadmap merged` and `./dev.py test`
- compatibility: `gates` still parses the block; first, second-to-last and last commands unchanged; other releases' blocks unchanged
- acceptance: `tests/integration/test_roadmap_gate.py` passes with the block parsed and every `uv run clutch` command accepted by the real parser
- tests: updated tests/integration/test_roadmap_gate.py
- post-merge source of truth: docs/roadmap.md

## Scope in / Scope out
In: add `--require` to the `context suggest` parser and `_run_context_suggest` (new keyword `require=False`, passed from the single caller in `clutch/__main__.py`), update the verb's `exits` help text and add an example with `--require`; add the four commands to the 0.5.0 gate block and rewrite the sentence just above it that says the meta and `context suggest` clauses are unchecked so it names what is now checked; in `tests/integration/test_roadmap_gate.py::test_real_roadmap_gate_blocks` change only the `if release != "0.4.0":` three-command assertion to exempt `0.5.0` as well; document `--require` in the `context suggest` paragraph of docs/how-clutch-works.md section 14 and its exit-code text, and in the `context suggest` row of clutch/docs/host-running.md (the README paragraph on this verb names no exit codes and stays). Run `uv run clutch meta refresh` on the three edited documents and on the new test file, and set the new test's `purpose` by hand.
Out: other releases' blocks, `index build`, `context.suggest`, docs/annotations-index-plan.md, any wrapper verb, `tests/unit/test_context_suggest_verb.py` and `tests/integration/test_context_suggest_cli.py` (unchanged; they must still pass).

## Scope fence
- clutch/__main__.py
- docs/roadmap.md
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/integration/test_roadmap_gate.py
- tests/unit/test_context_suggest_require.py

## Acceptance criteria
1. `uv run clutch context suggest --help` lists `--require`, and `tests/unit/test_context_suggest_require.py` asserts `_run_context_suggest(..., require=True)` returns 1, not 0, when the index yields nothing, and returns 0 with `require=True` when it yields a selector; checked by `./dev.py test tests/unit/test_context_suggest_require.py`.
2. Without `--require`, the empty result still returns 0 and the missing index still returns 2: `./dev.py test tests/unit/test_context_suggest_verb.py tests/unit/test_context_suggest_require.py`.
3. The 0.5.0 `gate` block parses to exactly the six commands in the order given in Goal / Why, and `./dev.py test tests/integration/test_roadmap_gate.py` exits 0 (the real-block test exempts 0.5.0 from the three-command rule and still pins 0.6.0 and 0.7.0 at three).
4. The edited documents and the new test have no meta finding: `uv run clutch meta check docs/roadmap.md docs/how-clutch-works.md clutch/docs/host-running.md tests/unit/test_context_suggest_require.py` exits 0.
5. On this checkout the gate's context command works: `uv run clutch context suggest context-suggest --require` prints `context suggest: suggested` and exits 0 after `uv run clutch index build`.
6. The verb's help names `--require` and its exit 1: `./dev.py test tests/unit/test_main_help.py` exits 0.

## Verification
```
./dev.py test tests/unit/test_context_suggest_require.py tests/unit/test_context_suggest_verb.py tests/integration/test_context_suggest_cli.py tests/integration/test_roadmap_gate.py tests/unit/test_main_help.py
uv run clutch meta check docs/roadmap.md docs/how-clutch-works.md clutch/docs/host-running.md tests/unit/test_context_suggest_require.py
uv run clutch index build
uv run clutch context suggest context-suggest --require
```

## Definition of rejected
A `--require` that changes any exit code without the flag, a wrapper verb, a gate that needs a manual step, a test pinning roadmap row or gate text beyond the parse and parser check, or an edit outside the fence.

## Time budget
- expected: 25m
- stuck: 50m
- reason: one flag, one gate block, three doc edits and one test; the index build and the real-ticket check add run time
