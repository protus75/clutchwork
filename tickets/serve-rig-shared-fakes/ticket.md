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
- tests/integration/serve_rig.py::until
- tests/integration/serve_rig.py::retro_scenario
- tests/fakes.py
- tests/integration/test_scheduler.py::turn

## Goal / Why
`tests/integration/serve_rig.py` keeps its own copy of the zero-wall-clock `turn` (imported from `tests/integration/test_scheduler.py`) and its own `until` loop. After this ticket the rig drives both through `tests/fakes.py`: `serve_rig.until(rig, predicate)` awaits `fakes.until(predicate, rig.time, serve.SERVE_POLL_S)` and `retro_scenario` awaits `fakes.turn`. There is then one `until` and one `turn` implementation, so a pacing fix lands in one place. Every serve test keeps its pacing (one clock advance on the first poll, then one every 20th turn, 60 s wall-clock timeout) and its result.

The rig's clock, exec and filesystem are not defined in `serve_rig.py`. They come from `CoreRig` in `tests/integration/test_daemon_composition.py` through `repository` in `tests/integration/test_restart_timers.py`. `CoreRig`'s clock has `sleep` and `waits`, which `FakeClock` lacks. Moving them is `CoreRig`'s own change, so they stay as they are here.

## Scope in / Scope out
Scope in:
- In `tests/integration/serve_rig.py`, the body of `until(rig, predicate)` awaits `fakes.until(predicate, rig.time, serve.SERVE_POLL_S)` inside `try`, and `except AssertionError as exc` raises `AssertionError("production graph did not reach the scripted boundary") from exc`. The loop is removed. Keep the `(rig, predicate)` signature so no caller changes.
- In `serve_rig.py`, replace the `turn` import from `tests.integration.test_scheduler` with `turn` from `tests.fakes`, and import `tests.fakes` as `fakes`. Nothing else in the file changes. Drop the `time` import, since nothing else in the file uses it once the loop is gone. `text` is still imported from `test_scheduler`.
- Add `tests/integration/test_serve_rig_fakes.py`, which pins the delegation, the pacing and the timeout message.

Scope out:
- `CoreRig`, `ScriptFS`, `ScriptExec`, `Time` and `repository`: they live in hot files and belong to the module-migration rows (119, 120).
- Any serve test module and `tests/fakes.py`.

## Scope fence
- tests/integration/serve_rig.py
- tests/integration/test_serve_rig_fakes.py

## Acceptance criteria
1. `serve_rig.turn is fakes.turn` holds, and `inspect.getsource(serve_rig.until)` contains `fakes.until` and no `while`. Checked by `./dev.py test tests/integration/test_serve_rig_fakes.py`.
2. Pacing is unchanged. With a stand-in rig whose `time` is a `FakeClock` and a predicate that turns true on the 42nd poll, `serve_rig.until` advances the clock by exactly `serve.SERVE_POLL_S` three times (polls 1, 21 and 41), not once and not once per poll. Checked by `./dev.py test tests/integration/test_serve_rig_fakes.py`.
3. A predicate that never turns true raises `AssertionError` containing `production graph did not reach the scripted boundary` and not `predicate did not become true before timeout`. Checked by `./dev.py test tests/integration/test_serve_rig_fakes.py`. The test monkeypatches `tests.fakes.time.monotonic` to a fake counter that passes the 60 s deadline, so it does not wait 60 s.
4. Every serve test passes with the same results. Checked by `./dev.py test tests/integration -k serve`.

## Verification
```
./dev.py test tests/integration/test_serve_rig_fakes.py
./dev.py test tests/integration -k serve
```

## Definition of rejected
The branch is rejected if any serve test changes its expected values or timeout, if `serve_rig.until` changes its `(rig, predicate)` signature, or if the diff touches `CoreRig`, `tests/fakes.py` or a file outside the fence.

## Time budget
- expected: 20m
- stuck: 40m
