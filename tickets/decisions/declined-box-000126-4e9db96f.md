---
id: declined-box-000126-4e9db96f
kind: declined
link: box-000126-4e9db96f
reopen_after_days: 90
---
A bootstrap note said the run's non-ok terminal transition was written through the Driver's own Journal handle while `run_ticket` wrote `running` through the checkout's handle, giving two writer handles over one state dir. It proposed passing the checkout's journal into the Driver. Current code already does this: `runner.bind` and the run path set `driver.journal = checkout.journal` and build `driver.effects` from it, so `ctx.driver.journal` and `checkout.journal` are the same object.

The gap is already closed. `bind` (clutch/runner.py:131-134) and the run path (clutch/runner.py:468-469) replace the Driver's journal with the checkout's and build Effects on it. `drive` journals its terminal through `ctx.driver.journal`, which is the checkout's handle, so the run has one writer. Triage (clutch/triage.py:109,132) and the CLI path (clutch/__main__.py:548) do the same. The extra `Journal(...)` that `Driver.from_config` builds (clutch/driver.py:169) is replaced before anything appends to it. No harmful behavior can be reached today.

- clutch/runner.py:133-134 `driver.journal = checkout.journal`; `driver.effects = Effects(checkout.journal)` in `bind`
- clutch/runner.py:468-469 same assignment on the run path before `checkout.journal.append(... 'running' ...)` at :502
- clutch/runner.py:414 terminal appended via `ctx.driver.journal`, the same object as the checkout's journal
- clutch/triage.py:109,132 and clutch/__main__.py:548 apply the same rebinding

Message: box-000126-4e9db96f
