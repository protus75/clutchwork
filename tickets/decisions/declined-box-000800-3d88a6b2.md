---
id: declined-box-000800-3d88a6b2
kind: declined
link: box-000800-3d88a6b2
reopen_after_days: 30
---
The suggestion is a narrow prevention rule. When a ticket makes a read-only verb such as `view snapshot` or `prompt` start writing a file (for example a cache), Author or requisition review would grep `tests/` and `docs/` for statements that the verb writes no state and add those files to the fence. The trigger was one premise_failed bounce on snapshot-from-duckdb-cache.

There is one incident and it is already resolved: snapshot-from-duckdb-cache merged, and the leftover doc wording was declined as minor in declined-box-000798. Nothing shows the problem recurring or causing harm beyond one premise bounce. The fence rules in `clutch/specs/requisition_review.md` (lines 22-26) already trace references, recorded values and set membership. This proposal would add one more special case, a 'behavior property claim' closure, for a single trigger. The registry has declined the same kind of single-incident fence-closure addendum before: declined-box-000619 (grep for removed journal records), declined-box-000773 (STEP_KINDS consumers) and declined-box-000778 (model-call-in-open-stage). Reopen if a second ticket that turns a read-only verb or path into a writer is bounced or rejected because a test or doc claiming 'no state written' was left outside its fence. At that point, propose one general rule that traces tests and docs asserting the changed behavior, not a rule limited to writes.

- clutch/specs/requisition_review.md:22-26 already requires reference, recorded-value and set-membership fence closure; there is no rule for prose or test claims about side effects
- snapshot-from-duckdb-cache is in the merged set; its one premise_failed did not stop it landing
- declined-box-000798-7dfd22ee already handled the host-running.md 'without writing state' wording as minor
- Precedent: declined-box-000619-29321b17, declined-box-000773-2d21b8d4 and declined-box-000778-c63fa661 declined comparable single-incident fence-closure rule additions

Message: box-000800-3d88a6b2
