---
id: declined-box-000938-2a50e3c6
kind: declined
link: box-000938-2a50e3c6
reopen_after_days: 30
---
Retro/65 counted two merge conflicts in this window that reached the `rerun` rung on docs/how-clutch-works.md. Most tickets edit that one hand-written design document, so parallel tickets that change different sections still conflict and each pays for a full rerun. The finding proposes splitting the document into one file per section.

This is a cost that the design accepts, not incorrect runtime behavior. config.yaml already lists docs/how-clutch-works.md under scheduler.parallel.shared_paths. Merged ticket plan-prompts-shared-paths-exempt handles this file as a shared path that the scheduler serializes, and the conflict-rerun ladder (conflict-rerun-swap, conflict-rerun-accounting, conflict-discard-rerun-r1) is the recovery path for such conflicts. Both reruns used that path, and the finding reports no ticket that was lost, parked or wrongly merged. Splitting the document is a refactor. By the finding's own account, it would break section anchors and links in tickets, specs and CLAUDE.md, and tickets whose changes cross sections would have to fence more files. Reopen if the rerun rung on this file sends a ticket to the Reject queue, uses up a cap, or adds measurably to drain throughput loss over several retro windows, or if shared_paths serialization is shown to let two runs that both edit this file be in flight at once.

- config.yaml:40 parallel.shared_paths: [docs/how-clutch-works.md]
- merged: plan-prompts-shared-paths-exempt, conflict-rerun-swap, conflict-rerun-accounting, conflict-rerun-runs-alone, conflict-discard-rerun-r1
- the finding's overcorrection_risk names broken anchors and wider fences
- only two reruns reported, with no terminal failure or cap spend

Message: box-000938-2a50e3c6
