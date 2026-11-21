---
id: declined-box-000886-cb8293a1
kind: declined
link: box-000886-cb8293a1
reopen_after_days: 30
---
The shipped host guide `clutch/docs/host-contract.md` says every engine gate code is hard at merge, in the line 56 config comment and the line 383 paragraph. Since meta-drift-lint, `clutch/gates.py` makes `meta_drift` soft by default through `SOFT_GATE_DEFAULTS`, so both statements are out of date. The meta-drift-lint ticket left this correction to later work.

This is a documentation mismatch only. The engine behaves as intended: `DEFAULT_GATE_SEVERITY` makes `meta_drift` soft and every other engine code hard, and `merge_severity` applies host overrides on top. Nothing in the message or the evidence shows a run that failed, blocked, merged wrongly or spent caps because an operator or agent trusted the stale sentence. The one recorded reference, `tickets/context-suggest-author-block/diagnosis.json`, cites `SOFT_GATE_DEFAULTS` correctly. Earlier doc-drift reports with no runtime harm were also declined (000380, 000403). Reopen if an operator, author, implementer or reviewer is shown acting on the 'all hard' wording in a way that costs a run: for example, treating meta_drift as merge-blocking and spending a retry or premise bounce, or setting a host `gate_severity` override based on the wrong default. A sweep that already fences `clutch/docs/host-contract.md` can also fix the two lines as part of that change.

- clutch/docs/host-contract.md:56 comment says 'engine defaults are all hard'
- clutch/docs/host-contract.md:383 says 'all engine codes hard at merge unless' overridden
- clutch/gates.py:33 SOFT_GATE_DEFAULTS = {"meta_drift"}
- clutch/gates.py:34 DEFAULT_GATE_SEVERITY maps meta_drift to soft and every other ENGINE_GATE_CODES member to hard
- tickets/context-suggest-author-block/diagnosis.json cites SOFT_GATE_DEFAULTS correctly; no run is recorded as misled by the doc
- Message origin meta-drift-lint ended ok; no failure is reported

Message: box-000886-cb8293a1
