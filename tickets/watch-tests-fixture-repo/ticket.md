---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- tests/integration/test_watch.py::config_fixture
- tests/integration/test_watch.py::snapshot_inputs
- tests/integration/test_watch.py::test_snapshot_verb_reads_config_state_dir
- tests/integration/test_watch.py::test_observe_verbs_take_no_lock_and_write_nothing
- tests/integration/test_watch.py::test_snapshot_watch_uses_configured_state
- tests/integration/test_watch.py::test_snapshot_display_fields
- tests/integration/test_config.py::VALID
- clutch/__main__.py::_observe_context
- tests/regress_dev_test_args.py

## Goal / Why
Three integration tests in `tests/integration/test_watch.py` run `clutch view snapshot` against the live clutch checkout instead of a fixture. They read the repo's real `config.yaml` with `Path("config.yaml")`, and `main` takes the repo from `Path.cwd()`, so each snapshot projects every ticket and the whole journal of whatever checkout pytest runs in. On 2026-11-19 at `c407fcd6`, with 757 ticket directories, each took 27-28 s (attached evidence), making them three of the four slowest integration tests and stretching every Check stage. Their runtime grows with every ticket filed, and their results depend on live repo state. When done, the three tests build a small temporary git repo, pass it to `main` through its existing `cwd=` parameter, never read a path relative to the process working directory, and each finishes in a few seconds regardless of the live checkout's size.

## Boundary contract
none
- reason: tests encoding an existing contract; the three tests keep asserting the same snapshot and observe-verb behavior, and only their input repo changes from the live checkout to a temporary fixture. No production code changes.

## Scope in / Scope out
Scope in: add a new helper module `tests/integration/watch_fixture_repo.py` that creates a minimal git repo under a given `tmp_path` (`git init`, one commit, a `config.yaml` built from `tests.integration.test_config.VALID` with the test's chosen `state_dir`, and an empty `tickets/` directory) and returns its path. In the three snapshot tests `test_snapshot_verb_reads_config_state_dir`, `test_observe_verbs_take_no_lock_and_write_nothing` and `test_snapshot_watch_uses_configured_state`, replace `Path("config.yaml").read_text()` with the fixture's config text, call `main([...], cwd=<fixture repo>)`, and change the expected `base` in `test_snapshot_watch_uses_configured_state` from `Path.cwd()` to the fixture repo path. `VALID` uses `state_dir: .clutch`, so replace that string, not `.clutch/state`. In `test_snapshot_display_fields`, read both tracked files it opens (the extension's package manifest and the host run guide) through a path anchored on `Path(__file__).resolve().parents[2]` instead of the working directory, so `integration-test-repo-isolation`'s empty-working-directory guard needs no edit to this hot file. Keep every existing assertion's meaning. The forced edit to the hot file `tests/integration/test_watch.py` is limited to these four tests and the helper import; no new test goes there. Add the carried reproducer `tests/regress_watch_tests_fixture_repo.py`.
Scope out: other tests in `test_watch.py`, the empty-working-directory guard and the other integration files that read the live checkout (`integration-test-repo-isolation` owns them and the enforcement), and snapshot performance (`snapshot-duckdb-under-one-second`).

## Scope fence
- tests/integration/test_watch.py
- tests/integration/watch_fixture_repo.py
- tests/regress_watch_tests_fixture_repo.py

## Acceptance criteria
1. `tests/regress_watch_tests_fixture_repo.py` runs `tests/integration/test_watch.py::test_snapshot_verb_reads_config_state_dir`, `::test_observe_verbs_take_no_lock_and_write_nothing` and `::test_snapshot_watch_uses_configured_state`, given as absolute paths, in a pytest subprocess (`-n 0 -p no:cacheprovider`, explicit `--rootdir` and `-c` pointing at the repo). The subprocess's working directory is an empty temporary directory with no `config.yaml` or `tickets/`. When all three pass, it prints only `{"regression_result": "pass"}` and exits 0. When any fails, as all three do at base with `FileNotFoundError` on `config.yaml`, it prints `{"regression_result": "defect"}` and exits nonzero. When the three IDs are not all collected, it prints `{"regression_result": "error"}` and exits nonzero. Diagnostics go to stderr.
2. `./dev.py test tests/integration/test_watch.py` passes, and `grep -nE 'Path\("(config\.yaml|vscode-clutchwork|clutch/)|Path\.cwd\(\)' tests/integration/test_watch.py` prints nothing.
3. Each of the three tests takes under 5 s in `./dev.py test tests/integration/test_watch.py --durations=10` on the real checkout, not ~27 s; report the three measured durations in the Implement reply's `predicted_vs_actual` field, which the engine writes into run.md.

## Verification
```
./dev.py test tests/integration/test_watch.py
```

## Definition of rejected
Reject if any of the four edited tests still reads a file through the process working directory, drops or weakens an assertion, mocks out `observe.snapshot` instead of running it on a fixture repo, or adds a new test to `tests/integration/test_watch.py`.

## Time budget
- expected: 12m
- stuck: 24m

## Regression
```
python tests/regress_watch_tests_fixture_repo.py
```
- carries: tests/regress_watch_tests_fixture_repo.py
- carries: tests/integration/watch_fixture_repo.py
