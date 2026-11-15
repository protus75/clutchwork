---
id: declined-box-000456-99370dbf
kind: declined
link: box-000456-99370dbf
reopen_after_days: 60
---
Some forward-looking plan documents still say to add `./dev.py` launcher twins for engine verbs that are not built yet. Examples are `./dev.py training-export` in docs/training-data-plan.md and `./dev.py release` in docs/roadmap-driver-plan.md. The merged dev-py-dev-tasks-only rule now forbids launcher twins of engine verbs, so the plans contradict it.

This is a wording mismatch in design documents for features that do not exist yet. No code reads these plan docs, and no verb, gate or prompt behaves wrongly because of them. The mismatch can only matter when someone writes a ticket from one of these plans. At that point the command-surface rule in CLAUDE.md and AGENTS.md, plus requisition review, already apply, and that ticket can fix its own plan text. Reopen if a ticket written from one of these plans adds a `./dev.py` twin of an engine verb, or if a run fails or is bounced because it followed the plan's dev.py wording.

- docs/training-data-plan.md:127 lists `./dev.py training-export` and `training-eval` next to the CLI verbs
- docs/training-data-plan.md:139 names `./dev.py training-export` in the training-export row
- docs/roadmap-driver-plan.md:79 calls `chupa release` the engine verb behind `release-verb`'s `./dev.py release`
- The verbs described are not built, and no engine code or prompt spec reads these plan docs
- Merged ticket dev-py-dev-tasks-only and the CLAUDE.md command-surface rule already govern any ticket written from these plans

Message: box-000456-99370dbf
