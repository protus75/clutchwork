---
id: declined-box-001121-f4083d08
kind: declined
link: box-001121-f4083d08
reopen_after_days: 30
---
Since the merged serve-no-roadmap change, the reason given at clutch/docs/host-authoring.md lines 149-150 may be partly out of date. It says 'the driver and `roadmap accept` rewrite roadmap rows' as the reason tickets must not pin roadmap or plan text in standing tests. The rule itself is unaffected.

This is a stale explanatory clause in a shipped guide. It causes no wrong runtime behavior. The rule it supports (verify roadmap and plan edits in review, never add a standing test that pins current text, allow only a parse and gate-validity check) is still correct whoever edits roadmap rows, because `roadmap accept` and the owner still edit them. An author who follows the guide as written still writes a correct ticket. Earlier records 000886 and 000798 declined similar slightly-stale wording in shipped host guides. Reopen if this wording leads an author or reviewer to a wrong ticket, for example a standing roadmap-text test that breaks main, or a requisition review finding that cites this sentence. It can also be fixed as part of the next ticket that already edits this section of host-authoring.md.

- clutch/docs/host-authoring.md:147-152: the rule bans standing tests that pin roadmap or plan text. The stale clause is only the reason given for it.
- serve-no-roadmap is in the merged set. The reporting Implement run ended premise_failed and filed this as a note about a file outside its scope fence.
- Registry precedents declined-box-000886-cb8293a1 and declined-box-000798-3d88a6b2 declined slightly-stale statements in shipped host guides when no run was harmed.
- Neighbor index unavailable (index_unreadable). That is not grounds to decline.

Message: box-001121-f4083d08
