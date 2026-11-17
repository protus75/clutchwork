---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- tests/integration/test_exec_seam_reap.py
- clutch/seams.py::SubprocessExec.run
- clutch/seams.py::reap_outcome
- tests/regress_context_directory.py

## Goal / Why
`tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` fails in full `./dev.py test` runs and passes alone. Six Suggestion Box messages report it (box-000706, box-000712, box-000717, box-000719, box-000724, box-000725), and implement runs spend time re-proving it is a base failure.

Cause, shown in `tickets/exec-seam-peak-memory-test/evidence/evidence.txt`: on Linux a child's `ru_maxrss` from `os.wait4` includes the peak resident memory of the process it was spawned from, because exec records the old address space's high-water mark. The test spawns its two children from the pytest worker. Late in a full run a worker holds hundreds of MB, so both children report the worker's peak and `big - small >= 100000` fails. From a parent holding 600 MB, a child running `pass` reports 619036 KB, the same as a child allocating 200 MB.

After this change the test spawns its two children from a fresh, small Python interpreter, so its result no longer depends on how large the pytest worker has grown. It still checks what it checked: each child gets its own rusage (`big` and `small` each receive one call), `big` used CPU time, and the 200 MB child's peak exceeds the idle child's by at least 100000 KB.

## Scope in / Scope out
In:
- `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` runs a short script in a new `sys.executable` process. That script awaits the same two `SubprocessExec().run` calls through `asyncio.gather` with `on_rusage` callbacks, and prints the two `Rusage` records as one JSON object on stdout. The test parses it and keeps its four assertions unchanged. Start that interpreter with the test's existing `run` helper, or with `subprocess.run`, with `cwd` the repo root so `clutch` imports.
- A new reproducer `tests/regress_peak_memory_big_worker.py`, modelled on `tests/regress_context_directory.py`, with all work inside `main()` under an `if __name__ == "__main__":` guard, as `tests/integration/test_regress_scripts_guarded.py` requires. It allocates and touches about 600 MB in its own process (`b"\x01" * 600_000_000`), then runs `pytest.main(["-n0", "-q", "tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory"])` in-process with pytest's output sent to stderr. It prints `{"regression_result": "pass"}` and exits 0 when pytest returns 0, prints `{"regression_result": "defect"}` and exits 1 when the test fails, and prints `{"regression_result": "error"}` and exits 2 on any other outcome (for example, pytest collection errors or a missing test).

Out: `clutch/seams.py` and every other engine file. That the figure the seam reports for provider calls includes the engine's own peak is a product defect with its own Suggestion Box message; this ticket changes only the test. The file's other tests stay as they are.

## Scope fence
- tests/integration/test_exec_seam_reap.py
- tests/regress_peak_memory_big_worker.py

## Acceptance criteria
1. `uv run python tests/regress_peak_memory_big_worker.py` prints `{"regression_result": "pass"}` and exits 0 on the branch, and prints `{"regression_result": "defect"}` and exits 1 at the merge base with the reproducer copied over. Ruled out: a test whose result still depends on the pytest worker's peak memory.
2. `./dev.py test tests/integration/test_exec_seam_reap.py` exits 0, and the test still asserts `len(big) == len(small) == 1`, `big[0].user_s + big[0].sys_s > 0`, `small[0].max_rss_kb > 0` and `big[0].max_rss_kb - small[0].max_rss_kb >= 100000`. Ruled out: a fix that lowers the 100000 KB threshold or drops an assertion.
3. `git diff --name-only main...HEAD` lists only the two fenced files.

## Verification
```
./dev.py test tests/integration/test_exec_seam_reap.py
uv run python tests/regress_peak_memory_big_worker.py
```

## Definition of rejected
The branch is rejected if it changes `clutch/seams.py` or any file outside the fence, lowers the 100000 KB threshold, removes an assertion, marks the test skipped, flaky or xfail, or reruns it until it passes.

## Time budget
- expected: 10m
- stuck: 20m

## Regression
```
uv run python tests/regress_peak_memory_big_worker.py
```
- carries: tests/regress_peak_memory_big_worker.py
