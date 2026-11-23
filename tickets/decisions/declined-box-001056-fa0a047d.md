---
id: declined-box-001056-fa0a047d
kind: declined
link: box-001056-fa0a047d
reopen_after_days: 30
---
A note from the implement-skips-full-suites run says docs/how-clutch-works.md would still describe Implement as running the hard always-trigger checks and coverage gates after the prompt change. On current main the doc already matches the change. Line 254 says Implement runs its Verification commands plus lint and format on changed files, and leaves the full suites, coverage gates and base comparisons to Check.

Nothing is left to fix. The doc wording the note expected to go stale was updated when implement-skips-full-suites merged, so the doc and the shipped Implement spec agree. Even if it were stale, it would be a wording mismatch with no wrong runtime behavior. Reopen if docs/how-clutch-works.md again says Implement runs the full suites or coverage gates while clutch/specs/implement.md says it does not.

- docs/how-clutch-works.md:254 says: 'Implement runs its Verification commands and lint and format on changed files, leaving the full suites, coverage gates and base comparisons to Check.'
- implement-skips-full-suites is in the merged set
- A grep of docs/how-clutch-works.md finds no remaining text saying Implement runs always-trigger hard checks or coverage gates

Message: box-001056-fa0a047d
