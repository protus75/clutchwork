---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- tests/integration/test_scheduler.py::turn
- tests/integration/serve_rig.py::until
- clutch/seams.py::FileSystem
- clutch/seams.py::ProcessExec
- clutch/journal.py::Journal

## Goal / Why
Today every test module hand-rolls its own clock, exec, filesystem, journal and git fake, and `until` exists in several copies. After this ticket `tests/fakes.py` holds one of each plus one `until`, and `tests/conftest.py` exposes them as pytest fixtures. Rows 118-120 of `docs/roadmap.md` migrate the existing users, so this ticket only adds the shared modules. `fakes.until` yields with the zero-wall-clock callback turn (a future resolved by `loop.call_soon`, the body of `tests/integration/test_scheduler.py::turn`), so a fake clock advances at the pacing `serve_rig.until` has today: one advance on the first poll and then one every 20th turn (declined-box-000559).

## Scope in / Scope out
In:
- New `tests/fakes.py` with `FakeClock` (callable returning a `datetime`, with `advance(seconds)`), `FakeExec` (records argv calls, returns a scripted `(rc, out, err)`), `FakeFileSystem` (in-memory implementation of every `clutch.seams.FileSystem` method), `FakeJournal` (in-memory `append` and `read` with the `clutch.journal.Journal` signatures), `FakeGit` (records each call by method name and arguments and returns scripted values), `turn()` (the `test_scheduler.py::turn` body, moved here as a copy), and `until(predicate, clock, step, *, timeout=60)`.
- `until` checks the predicate, calls `clock.advance(step)` on turn counts 0, 20, 40 and so on, awaits `turn()`, and raises `AssertionError` when the timeout passes.
- New `tests/conftest.py` with one fixture per fake: `fake_clock`, `fake_exec`, `fake_fs`, `fake_journal`, `fake_git`.
- New `tests/unit/test_shared_fakes.py` covering the fakes and `until`.

Out: no existing test, helper, rig or harness is edited or migrated. `tests/integration/test_scheduler.py` and `tests/integration/serve_rig.py` keep their own `turn` and `until` until rows 118-120. No engine code under `clutch/` changes.

## Scope fence
- tests/fakes.py
- tests/conftest.py
- tests/unit/test_shared_fakes.py

## Acceptance criteria
1. With a `FakeClock` and a predicate that turns true after 45 turns, `until` has advanced the clock exactly 3 times (turn counts 0, 20, 40), not 0 times and not 45 times; checked by `./dev.py test tests/unit/test_shared_fakes.py`.
2. `until` with a predicate that never becomes true and `timeout=0.05` raises `AssertionError`, not a hang and not a silent return; checked by `./dev.py test tests/unit/test_shared_fakes.py`.
3. `until` completes 100 turns with no `asyncio.sleep` and no timer: the test patches `asyncio.sleep` to raise and the call still returns; checked by `./dev.py test tests/unit/test_shared_fakes.py`.
4. `FakeFileSystem` round-trips `write` then `read_bytes` and `size`, and `entries` lists the written name, not `[]`; checked by `./dev.py test tests/unit/test_shared_fakes.py`.
5. `FakeJournal.append` followed by `read` returns the appended event, not an empty list; `FakeExec.run` returns its scripted result and records the argv; `FakeGit` records a call and returns the scripted value; checked by `./dev.py test tests/unit/test_shared_fakes.py`.
6. Each of the five fixtures named in Scope in resolves in a test and yields an instance of the matching `tests/fakes.py` class, not `None`; checked by `./dev.py test tests/unit/test_shared_fakes.py`.
7. `git diff --name-only` against the base lists only the three fenced paths, so no existing file changed; checked by `./dev.py test`, which still exits 0 for the whole suite.

## Verification
```
./dev.py test tests/unit/test_shared_fakes.py
./dev.py test
```

## Definition of rejected
Any existing test module, rig or harness is edited or migrated to the new fakes. `until` sleeps on the wall clock or a timer, or advances the clock at a pace other than turn counts 0, 20, 40. Any file under `clutch/` changes.

## Time budget
- expected: 25m
- stuck: 50m
