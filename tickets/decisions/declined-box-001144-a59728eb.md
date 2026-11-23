---
id: declined-box-001144-a59728eb
kind: declined
link: box-001144-a59728eb
reopen_after_days: 30
---
A session suggestion to check every clutch verb that takes a path or stem argument for one failure: an argument that matches nothing exits 0 silently when it should be refused with exit 2 and a paved road. It suggests either one shared selection helper or a CLI test that runs each such verb with a nonexistent path. The only demonstrated case is the meta verbs, which open ticket meta-path-selects-nothing already covers.

The only verbs shown to have this defect are `meta check`, `meta refresh` and `meta fill`, and open ticket meta-path-selects-nothing already fixes them. The suggestion asks for an audit and a shared helper or test sweep across every path- or stem-taking verb, but it names no other verb that skips an unmatched argument and exits 0. It cites no run harmed by such a verb, and it has no reproduction outside meta. A sweep with no second confirmed instance is speculative hardening. It cannot be bounded to one buildable ticket with a measurable result. Reopen when a second verb, not under `clutch meta`, is reproduced exiting 0 on a path or stem that matches nothing, or after meta-path-selects-nothing merges if its fix shows a reusable selection owner that other verbs should adopt.

- Message class suggestion, origin session, no stage, outcome or report attached.
- Open ticket meta-path-selects-nothing covers the only demonstrated instance (meta check/refresh/fill exit 0 on an untracked or unmatched path, evidence/meta-untracked.txt).
- The message names no other verb that has the defect and cites no incident outside meta.
- The neighbor index was unavailable, so it gives no evidence either way.

Message: box-001144-a59728eb
