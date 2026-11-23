---
id: declined-box-000990-1de662e4
kind: declined
link: box-000990-1de662e4
reopen_after_days: 30
---
After plan-prompts-priority-order merged, an Implement run noted that the planning document docs/roadmap-driver-plan.md still says a supervising session may edit a dependency ticket only when a Recommendation names the edit. The new prompt rule from that change overrides this. The run could not update the plan because the file was outside its scope fence.

This is a mismatch between a planning document and the code, with no wrong runtime behavior behind it. The engine and the supervising loop take their rules from the shipped prompts and CORE_TEMPLATE, not from docs/roadmap-driver-plan.md. Registry records 000526, 000530, 000627, 000646 and 000814 declined the same kind of stale-wording note for this plan document. Reopen if a supervising session or an engine stage is shown acting on the stale plan wording and getting a wrong result, for example refusing or misapplying a dependency ticket edit.

- origin plan-prompts-priority-order is merged; the outcome was ok
- the message names only the wording of a planning document and reports no runtime failure
- declined-box-000526-6842d927, declined-box-000530-c9630ad6, declined-box-000627-7999f5b8, declined-box-000646-618509dc and declined-box-000814-434c57c7 declined stale-wording notes about docs/roadmap-driver-plan.md
- neighbors index was unavailable, which is not used as grounds

Message: box-000990-1de662e4
