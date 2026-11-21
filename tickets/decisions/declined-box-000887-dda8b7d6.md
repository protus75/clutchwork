---
id: declined-box-000887-dda8b7d6
kind: declined
link: box-000887-dda8b7d6
reopen_after_days: 30
---
The note asks the Author spec, the host authoring guide and the requisition review spec to require that any new table column, schema field or stored value a ticket adds be defined. The definition would come either from its owner in a canonical document or from a worked example in the ticket, covering what one value is, its order, duplicates, and null or empty values. The trigger was index-build-r2 attempt 0, which stopped at Implement with premise_failed on 2026-11-21. Its Goal added a `files.imports` column without defining what an entry is, and the plan's files table in docs/annotations-index-plan.md section 5 does not list that column. Two ticket reviews and one independent prompt-review audit had approved the ticket.

The evidence is one premise_failed bounce on one ticket, and index-build-r2 has since merged. That means the bounce cost one cycle and did not leave incorrect runtime behavior. The proposal is a new authoring and review rule that guards against a possible future case, which is speculative hardening, not a fix for a current, materially harmful behavior gap. The registry has declined the same kind of narrow single-incident prevention rule before: 000800 (one premise_failed bounce leading to a fence rule), 000435 (criteria should name the exact stored form of a value), 000376 and 000778. It also declined both related messages this note cites, 000879 and 000882. Reopen if undefined stored-value contracts in tickets cause premise_failed or Review rejections on at least three distinct tickets within one retro window, or if an undefined column contract merges and produces wrong stored data that a consumer misreads.

- index-build-r2 is in the merged set, so the reported premise_failed at attempt 0 was a single bounce that the ticket recovered from
- The message reports one incident and no recurrence across other tickets
- Prior decisions declined similar single-incident authoring and review rule proposals: declined-box-000800-3d88a6b2, declined-box-000435-b106dd5f, declined-box-000376-a635ab89, declined-box-000778-c63fa661
- The related messages box-000879 and box-000882 were both declined (declined-box-000879-9f900b70, declined-box-000882-aa53ccee)

Message: box-000887-dda8b7d6
