---
id: declined-box-000533-3ff8c951
kind: declined
link: box-000533-3ff8c951
reopen_after_days: 30
---
While implementing release-publish, the agent found roadmap and plan documents outside its scope fence that still describe `./dev.py publish` as an existing task that bumps the patch version before uploading. Once release-publish lands, those statements will be out of date.

This is a mismatch in the wording of forward-looking planning documents. It is not a runtime behavior gap. No engine code, gate, prompt spec or host guide reads these roadmap documents as authority for how a release is published. The publish path an operator actually follows is the verb and run guide that release-publish itself changes. The registry has already declined the same kind of out-of-fence plan-doc staleness three times: declined-box-000456-99370dbf (plans proposing `./dev.py` launcher twins), declined-box-000526-6842d927 and declined-box-000530-c9630ad6 (roadmap-driver-plan wording made stale by a merged ticket). The message also names no specific document or line, and gives no proposed paths, so there is no bounded ticket with a measurable result. Reopen if a stale publish statement is found in an operator-facing guide or engine-rendered text (`clutch/docs/`, README, a spec or ask template) and sends an operator or agent to a removed or wrong publish command.

- Message class suggestion, origin release-publish, stage implement, outcome incomplete; proposed_paths and proposed_spec_paths are empty
- Open ticket release-publish owns the change to the `./dev.py publish` road; the stale text is in documents outside its fence
- Precedent declines for out-of-fence plan-doc wording drift: declined-box-000456-99370dbf, declined-box-000526-6842d927, declined-box-000530-c9630ad6
- Triage bar: a plan-wording mismatch is declined unless it is tied to reachable incorrect runtime behavior

Message: box-000533-3ff8c951
