---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- watch-tests-fixture-repo

## Context
- tests/conftest.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_changelog_url.py
- tests/integration/test_intake_keeps_draft.py
- tests/integration/test_evidence_claude_fixture.py
- tests/integration/test_extension_argv.py
- tests/integration/test_reject_reason_both_paths.py
- tests/integration/test_scheduler_seam_source.py
- tests/integration/test_roadmap_table.py
- tests/harness/daemon_soak.py::produce
- tests/harness/shakeout/run.py::produce
- tests/harness/reliability_battery.py::produce
- CLAUDE.md#A. Engine conduct

## Goal / Why
Integration tests could read the live checkout through the process working directory, and nothing stopped them. Three `test_watch.py` tests snapshotted the whole live repo (757 tickets) and took ~27 s each, and the runtime grew with every ticket filed (fixed by `watch-tests-fixture-repo`). No rule or check prevents the next such test. When done, every integration test runs with an empty temporary working directory, so a path resolved against the working directory finds nothing and the test fails at once. Tests read tracked source and docs only through a path anchored on `Path(__file__)`, never the checkout's operational state (`tickets/`, `.clutch/`, the journal, `evidence/`). The rule lives in this repo's conduct files as a one-line gated rule. A 2026-11-19 prototype of this guard on `c407fcd6` failed exactly 16 tests: 4 in `test_watch.py` (owned by the dependency), 4 harness-driven tests whose `produce()` stamps `git rev-parse HEAD` of `Path.cwd()`, and 8 that read tracked files by relative path.

## Boundary contract
none
- reason: tests encoding an existing contract; the guard and the edited tests and harness change only where test code finds the repo root, and every test keeps its assertions. No `clutch/` production code, output, or format changes.

## Scope in / Scope out
Scope in:
- Create `tests/integration/conftest.py` with one autouse fixture that `monkeypatch.chdir`s each integration test into a fresh empty directory from `tmp_path_factory`. Its docstring is the paved road: build a temporary fixture repo and pass it explicitly (for example `main([...], cwd=repo)` or `tests/integration/watch_fixture_repo.py`), or anchor a tracked-file read on `Path(__file__).resolve().parents[2]`.
- In the eight files fenced below, replace each working-directory-relative read of a tracked file (`Path("clutch/...")`, `Path("docs/...")`, `Path("pyproject.toml")`, `Path("tests/fixtures/...")`, `Path("vscode-clutchwork/...")`) with the same path under a module-level `ROOT = Path(__file__).resolve().parents[2]`. Assertions stay unchanged.
- In `tests/harness/daemon_soak.py`, `tests/harness/shakeout/run.py` and `tests/harness/reliability_battery.py`, have `produce()` stamp `rev_parse` of the code checkout anchored on the module's own `__file__`, not of `Path.cwd()`. In `tests/integration/test_daemon_soak_runner.py::test_daemon_soak_is_rederivable`, replace `Path.cwd()` with that same anchored root.
- Add one gated rule line to section A of `CLAUDE.md` and the matching place in `AGENTS.md`, outside the managed block: integration tests run in an empty working directory (`tests/integration/conftest.py`), and read tracked files only through a `Path(__file__)` anchor, never the checkout's `tickets/`, `.clutch/` or journal. Rule home: this is a repo rule about this repo's tests, so it goes in `CLAUDE.md` and `AGENTS.md`, not `CORE_TEMPLATE`.

Scope out: the three `test_watch.py` snapshot tests and its `vscode-clutchwork/package.json` read (`watch-tests-fixture-repo`), unit tests (`clutch.testguard` already governs them), and any `clutch/` production code.

## Scope fence
- tests/integration/conftest.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_changelog_url.py
- tests/integration/test_intake_keeps_draft.py
- tests/integration/test_evidence_claude_fixture.py
- tests/integration/test_extension_argv.py
- tests/integration/test_reject_reason_both_paths.py
- tests/integration/test_scheduler_seam_source.py
- tests/integration/test_roadmap_table.py
- tests/integration/test_daemon_soak_runner.py
- tests/harness/daemon_soak.py
- tests/harness/shakeout/run.py
- tests/harness/reliability_battery.py
- CLAUDE.md
- AGENTS.md

## Acceptance criteria
1. `./dev.py test tests/integration` passes with the new `tests/integration/conftest.py` in place.
2. A test that reads `Path("config.yaml")` or calls `main(["view", "snapshot"])` without `cwd=` fails under the guard with `FileNotFoundError` or a not-a-git-repository error, not by reading the live checkout. Show this with a one-off run of such a test, reported in the Implement reply's `surprises` or `predicted_vs_actual` field (the engine writes it into run.md), then delete that test. No standing test pins it.
3. `grep -rnE 'Path\("[^"]+"\)\.(read_text|read_bytes|open)\(|Path\.cwd\(\)' tests/integration tests/harness` prints only `tests/integration/test_notify.py:93` and `tests/integration/test_handoff_replace.py:13`, child-process scripts that report their own working directory. It no longer prints the 18 hits it shows on `c407fcd6` in the files fenced here.
4. `CLAUDE.md` and `AGENTS.md` each carry the one-line integration-isolation rule outside the managed block, checked by `grep -n "tests/integration/conftest.py" CLAUDE.md AGENTS.md`.

## Verification
```
./dev.py test tests/integration
```

## Definition of rejected
Reject if the guard is a denylist of specific paths instead of an empty working directory, if any test is skipped, marked or exempted to pass, if an assertion is weakened, if `clutch/` production code changes, or if the rule goes only into the managed block or `CORE_TEMPLATE`.

## Time budget
- expected: 20m
- stuck: 40m
