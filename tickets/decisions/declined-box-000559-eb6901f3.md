---
id: declined-box-000559-eb6901f3
kind: declined
link: box-000559-eb6901f3
reopen_after_days: 30
---
Author could not produce a ticket.

Evidence: - until_pacing_not_preserved: Scope in says `fakes.until` 'keeps serve_rig's current pacing' with `await asyncio.sleep(0)`, and that 'the fake serve clock moves as often as it does today'. Merged serve_rig.until (serve_rig.py:27-36) yields with `test_scheduler.turn()` (test_scheduler.py:41-45), which awaits a future that `call_soon` resolves. Each turn therefore takes two loop iterations: one to set the result and one for the task wakeup. A bare `asyncio.sleep(0)` takes one. Advancing every 20th turn would then move rig.time by SERVE_POLL_S every 20 loop iterations instead of every 40. The fake clock would run about twice as fast relative to the serve graph's work, and fake budgets (stuck budgets, heartbeats, cooldowns) would expire in half the loop progress. That threatens criteria 5 and 6 on the more than 100 unedited `until(rig, ...)` call sites outside the fence. The ticket's two statements cannot both hold. (do instead: In Scope in, criterion 1 and Definition of rejected, replace `await asyncio.sleep(0)` with the existing zero-wall-clock callback yield. That is the body of test_scheduler.turn: create a future, resolve it with `loop.call_soon(future.set_result, None)`, then await it. Move that body into `tests/fakes.py` as the single yield `fakes.until` uses. Alternatively, drop the claim that pacing is preserved and state the 2x change explicitly, with evidence that the serve tests tolerate it. The first option is the minimal repair.)
