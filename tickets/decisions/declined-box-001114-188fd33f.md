---
id: declined-box-001114-188fd33f
kind: declined
link: box-001114-188fd33f
reopen_after_days: 30
---
While a stop request or an operator-requested retro is pending, `Serve.select` admits no new tickets. That is the same admission gate that held tickets during the engine upgrade. Unlike the upgrade hold, which `serve-upgrade-hold-visible` now journals and shows as `upgrade_hold`, these two holds have no status key in the snapshot, in `view watch` or in `view events`. Queued tickets keep showing `ready` until the request is served.

The gap is real: `clutch/observe.py` has no status key for these two holds, and `view watch`, `view events` and `view status` never read `retro_id` or `stop_requested`. Nothing shows it has done harm, though. The ticket that filed this put it in Scope out by analogy and cited no incident. Unlike the upgrade hold, which serve sets by itself after a merge with nothing to tell the operator, both of these holds start from the operator's own command. `stop_requested` comes from a stop the operator submitted, and `retro_id` from an operator retro request (due retros run at idle points and do not set `retro_pending`). The operator therefore already knows why admission stopped. Nothing shows a supervising loop or operator misreading either hold or losing time to it. Reopen if a run record, session or retro shows an operator or supervising loop misdiagnosing idle serve because of a pending stop or retro request (for example `ready` rows not dispatching for minutes with no visible reason), or if a machine path starts setting either flag without an operator command.

- tickets/serve-upgrade-hold-visible/ticket.md:80 puts retro-pending and stop-requested holds in Scope out by analogy and cites no incident
- clutch/serve.py:255-257 select() refuses non-running stems while `projection.stop_requested` or `self.retro_pending()` is true
- clutch/serve.py:367-369 retro_pending() is true only for a control-inbox retro request id not yet served, so it starts from an operator
- No match for retro_id or stop_requested in clutch/observe.py, status.py, events.py or help.py
- observe.py STATUS_KEYS has `upgrade_hold` (line 103) but no key for a stop or retro hold

Message: box-001114-188fd33f
