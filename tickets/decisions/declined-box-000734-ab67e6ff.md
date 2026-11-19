---
id: declined-box-000734-ab67e6ff
kind: declined
link: box-000734-ab67e6ff
reopen_after_days: 30
---
CliAdapter.invoke in clutch/providers.py splits the LLM effect key into six names to build the evidence start record. It does not use clutch/llmeffect.py, which builds the key with llm_key and scoped_seq. The suggestion is to give the key one owner, either by passing the key parts to CallCapture or by adding an inverse of llm_key, and to test one call per key form through ProviderLLM.admitted_call. It names the seven-segment review key planned in docs/stage-panels-plan.md as a shape the current parse would reject.

No current runtime failure is shown. The instance fix has merged: providers.py line 418 keeps a scoped run_seq such as `sup-3` as a string when it is not decimal. Every key the engine builds today has six parts, because llm_key always joins six. The scoped forms from scoped_seq only change the run_seq slot, and attempt and call are always integers. So `capture.key.split('/')` and the int() calls succeed for every key that reaches CliAdapter.invoke today. The only failing key is the seven-segment `.../m<k>` form, which exists only in a planning document. This is hardening against a future key shape, not a fix for reachable wrong behavior. Several projections (stats.py, scorecard.py, author.py, acceptance.py) make the same six-part assumption, so any new key shape will need its own ticket in any case. That ticket can give the key one owner and add the round-trip test. Reopen if llm_key or any key builder starts producing a key that is not six parts or has a non-integer attempt or call slot, or once a stage-panels ticket that adds the seven-segment key is drafted.

- clutch/providers.py:405 unpacks capture.key.split('/') into six names; line 418 keeps a non-decimal run_seq as a string (instance fix evidence-scoped-call-key is merged)
- clutch/llmeffect.py:25 llm_key always joins exactly six segments; scoped_seq changes only the run_seq slot, to `<scope>-<n>`
- Every scoped caller (driver.py:282, requisition.py:277, rework.py:139, supervise_idle.py:41 key_scope='sup') passes an integer attempt and call_seq
- The seven-segment key llm/<stem>/<run_seq>/review/<attempt>/<call>/m<k> appears only in docs/stage-panels-plan.md, and no open ticket builds it
- Registry record declined-box-000730-3d73e66b: the paired instance message was dismissed by the operator

Message: box-000734-ab67e6ff
