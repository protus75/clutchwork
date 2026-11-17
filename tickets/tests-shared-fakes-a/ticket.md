---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
- shared-test-fakes

## Context
- tests/fakes.py
- tests/integration/test_drain.py::Clock
- tests/integration/test_cli.py::Clock
- tests/integration/test_tickets.py::Clock
- tests/integration/test_driver.py::FakeClock
- tests/integration/test_effects.py::FakeExec
- tests/integration/test_merge.py::repo
- tests/integration/test_stages.py::CONFIG

## Goal / Why
Five test modules each define their own clock or exec fake that `tests/fakes.py` already provides: `tests/integration/test_drain.py` (`Clock`), `tests/integration/test_cli.py` (`Clock`), `tests/integration/test_tickets.py` (`Clock`), `tests/integration/test_driver.py` (`FakeClock`) and `tests/integration/test_effects.py` (`FakeExec`). After this ticket each uses the shared class, so a fix to a fake lands in one place. Separately, the `repo` fixture in `tests/integration/test_merge.py` builds `config.yaml` by reading `tests/integration/test_stages.py` as text and splitting it on `CONFIG = """`. After this ticket it imports `CONFIG` from `tests.integration.test_stages` and writes that, so it no longer depends on how another file is laid out.

These five were chosen because their fakes are drop-in replacements. Other large modules (`tests/integration/test_daemon_composition.py`, `tests/integration/test_git.py`, `tests/integration/test_providers.py`) carry scripted behavior the shared fakes lack, and are out of scope here.

Many modules import `Clock` from `tests.integration.test_drain` and `tests.integration.test_cli`. Those imports must keep working with no change to the importers. So each module binds the shared class under its old name (`from tests.fakes import FakeClock as Clock`), and `Clock` is then the shared class itself.

## Scope in / Scope out
Scope in:
- `test_drain.py`: delete `class Clock`; add `from tests.fakes import FakeClock as Clock`. `START` stays, and the `Clock()` call sites that rely on it pass `START` where they relied on the old default (the shared default is `datetime(2026, 1, 1, tzinfo=UTC)`, equal to `START`). Do not change anything else in the file.
- `test_cli.py`: delete `class Clock`; add `from tests.fakes import FakeClock as Clock`. The old class returned a fixed 2026-01-01 and the shared default is the same instant. Nothing else changes.
- `test_tickets.py`: same replacement as `test_cli.py`.
- `test_driver.py`: delete `class FakeClock`; import `FakeClock` from `tests.fakes`. Its old fixed instant was `datetime(2026, 10, 5, tzinfo=UTC)`, so each `FakeClock()` call site passes that instant (a module constant is allowed). `FakeSleep` stays: the shared module has no equivalent.
- `test_effects.py`: delete `class FakeExec`; import `FakeExec` from `tests.fakes`. The old default result was `(0, "ok\n", "")` and the shared default is `(0, "", "")`, so each `FakeExec()` call site passes `result=(0, "ok\n", "")` (a module constant is allowed). `FakeClock` and `FakeFS` in this file stay: the clock advances one second per call and the filesystem records writes, neither of which the shared classes do. The `git_push(exec_: FakeExec)` annotation keeps working with the imported name.
- `test_merge.py`: remove the `Path(__file__).parent / "test_stages.py"` read-and-split in the `repo` fixture. Add `CONFIG` to the existing `from tests.integration.test_stages import ...` line, and write `CONFIG` to `config.yaml`. The `Path` import stays if still used.
- Add `tests/integration/test_shared_fakes_adoption.py`, which pins the identities and the absence of the source parse.

Scope out:
- `tests/fakes.py`, every module that imports `Clock` from the files above, and every other test file.
- The second-batch modules (roadmap row 120).
- `CoreRig`, `ScriptFS`, `ScriptExec` and `FakeLock`/`FakeExec` in `tests/integration/test_git.py`.

## Scope fence
- tests/integration/test_drain.py
- tests/integration/test_cli.py
- tests/integration/test_tickets.py
- tests/integration/test_driver.py
- tests/integration/test_effects.py
- tests/integration/test_merge.py
- tests/integration/test_shared_fakes_adoption.py

## Acceptance criteria
1. `tests.integration.test_drain.Clock`, `tests.integration.test_cli.Clock`, `tests.integration.test_tickets.Clock` and `tests.integration.test_driver.FakeClock` are each `tests.fakes.FakeClock` itself (`is`), not a local class of the same name; `tests.integration.test_effects.FakeExec is tests.fakes.FakeExec`. Checked by `./dev.py test tests/integration/test_shared_fakes_adoption.py`.
2. `tests.integration.test_merge.CONFIG is tests.integration.test_stages.CONFIG`, and the text of `tests/integration/test_merge.py` contains neither `test_stages.py` nor `split('CONFIG` (the old source-parse is gone, not merely unused). Checked by `./dev.py test tests/integration/test_shared_fakes_adoption.py`.
3. A `Clock()` from `test_drain` returns `datetime(2026, 1, 1, tzinfo=UTC)` and advances by exactly the seconds passed to `advance`, not by zero; `test_driver.FakeClock`-based drivers still read 2026-10-05 (the driver tests keep their results). Checked by `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_driver.py`.
4. Every changed module passes with its prior results, and every module that imports `Clock` from `test_drain` or `test_cli` still imports and passes. Checked by `./dev.py test tests/integration`.

## Verification
```
./dev.py test tests/integration/test_shared_fakes_adoption.py
./dev.py test tests/integration/test_drain.py tests/integration/test_cli.py tests/integration/test_tickets.py tests/integration/test_driver.py tests/integration/test_effects.py tests/integration/test_merge.py
./dev.py test tests/integration
```

## Definition of rejected
The branch is rejected if any importer of `Clock` outside the fence changes, if `tests/fakes.py` changes, if a test's expected value or timestamp changes to make it pass, or if a local clock or exec class of the replaced names remains in the five modules.

## Time budget
- expected: 30m
- stuck: 60m
