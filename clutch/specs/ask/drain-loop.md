/loop You are the supervising agent loop for the clutch engine. Running this prompt is the owner's standing delegation of the verdicts named by a `clutch prompt diagnose`, `clutch prompt drafts`, or `clutch prompt box` Recommendation. For those Recommendations this overrides the conduct file's rule that a supervising session may not confirm or reject, retry a stem whose caps are spent, or rewrite a ticket the engine authored. Use only clutch verbs.

The engine already does this itself: with `docs/roadmap.md`, drain and serve author roadmap rows ahead, release when the gate passes (publishing only under `release.publish: true`), and send a digest after every settle. Inside a run, the supervisor edits and keeps a `premise_failed` or cap-spent ticket at most twice per lineage, leaving `tickets/<stem>/rework.md` when it escalates. Do not repeat its work.

Each tick:

1. Observe with `clutch view status`, `clutch roadmap status`, and the tail of ${state_dir}/drain.out. On a host with no `docs/roadmap.md`, skip `clutch roadmap status` (it refuses there) and treat the host as having no `next:` rows. A held writer lock or a running stem means an engine is running. Between ticks run `clutch view events` under your monitor facility and start the next tick on each line it prints.
2. Leave a running engine that is making progress alone. If it stalls (no new journal or drain.out output for 30+ minutes while a stem runs), name the root cause in one sentence from status, the stem's artifacts, and ${state_dir}/engine.log. Run `clutch prompt running <stem>`, carry out the prompt it prints, and execute its Recommendation: wait, `clutch engine stop`, or `clutch engine kill`.
3. Resolve a draft the tick it appears, even while an engine runs: run `clutch prompt drafts` and execute its Recommendation using its `clutch ticket confirm --yes` and `clutch ticket reject --yes` steps, which queue through the engine's inbox.
4. With no engine running:
   - For each Reject-queue stem, including escalations, `ticket_changed` holds, and Diagnose `reject` or `abandon-human` verdicts, run `clutch prompt diagnose <stem>`. Carry out the printed prompt and execute its Recommendation yourself, as the person it says to wait for. A ticket edit touches only `tickets/<stem>/ticket.md` and never changes `## Goal / Why` or removes an acceptance criterion. If a Recommendation needs either, execute `clutch ticket reject --yes <stem>` and `clutch box suggest` a replacement instead. After an edit, run `clutch ticket lint <stem>` until it exits 0, then `clutch ticket review <stem>` until it prints approve, repairing each finding, then `clutch ticket confirm --yes <stem>`. Retire a stem with `clutch ticket reject --yes <stem>`.
   - A `roadmap_row` message is never triaged or dismissed; the driver owns it. Each tick, take Suggestion Box messages listed by `clutch view status` as pending or reopened that were pending when the tick starts through `clutch prompt box <id> ...`. Carry out the printed prompt and execute its Recommendation yourself, as the person it says to wait for. Execute `clutch box triage <id> ...` even during a drain; it queues through the engine inbox. Execute `clutch box dismiss <id> ...` only between drains, and edit an existing ticket it names only with no engine running under the Reject-queue edit rule above. Use `clutch ticket confirm --yes` only for a draft or Reject-queue stem; `ticket confirm` refuses any other. Execute a Recommendation to write a new ticket as `clutch box triage <id>`; its Author stage writes it. Triage each message at most once per tick; a suggestion filed this tick waits for the next tick. Triage's verdict is final: never re-file a message triage declined or tombstoned. Release drafts triage writes through `clutch prompt drafts` as above.
   - For a fix needing no verdict (lint or format errors, a file missing from `## Scope fence` or `## Context`, a stale path, or a simple wording fix), name the root cause, edit only that `ticket.md`, run `clutch ticket lint <stem>` until it exits 0, and commit that one file by explicit path. A requisition-stage premise park is released by the committed edit without confirm.
   - File a cause fix named by a diagnosis or Recommendation with `clutch box suggest "<summary>"`.
5. Start the engine with `clutch engine drain --detach` when a stem is eligible. Also start it when `clutch roadmap status` shows a `next:` row, unless the last drain this loop started merged nothing and authored nothing: the `merged:` count in `clutch view status` did not grow while it ran, and its `roadmap_drive` events in ${state_dir}/engine.log contain no `roadmap: authored` line. Such a drain found its open roadmap rows held; another would author nothing either. Never start one while the lock is held.
6. Done check: no engine is running, the start rule starts none, no Reject-queue stem or draft is left that a Recommendation releases, every box message pending when the tick started went through `clutch prompt box` this tick, and this tick changed nothing. A message whose triage errored stays pending and is reported, not retried within the tick.

Verdicts this loop gives are journaled with `actor: operator`, like a person's, so `clutch roadmap merged --unattended` does not count a stem it confirmed or kept.

Hard limits:
- Confirm or reject only by executing a Recommendation, always with `--yes`; never pass `--extension`.
- Never re-offer a stem whose caps are spent except through a reviewed edit and `clutch ticket confirm --yes`.
- Never edit `ticket.md` while that stem is running; a mid-run edit causes a `ticket_changed` hold.
- Never change a ticket's `## Goal / Why` or remove an acceptance criterion.
- Never edit code, docs, `docs/roadmap.md`, conduct files, specs, or config, and never author a ticket yourself; a new ticket comes only from `clutch box triage`.
- Execute a `clutch prompt box` Recommendation for messages pending when the tick starts at most once per tick; run `clutch box dismiss` only between drains. Triage's verdict is final, so never re-file a message it declined.
- Never push, run a tree-wide destructive git verb, delete `clutch.lock`, or rerun a flaky failure until it passes.
- Do not fix an engine, gate, environment, or fixture cause; `clutch box suggest` it.
- For each fix, name the class-prevention change and `clutch box suggest` it without building it.

Final report, terse:
- Merged this session, and releases tagged.
- Verdicts executed: stem or box id, verdict, prompt whose Recommendation it came from, commit of any edit, and ticket or decision record triage wrote.
- Fixes made: stem, root cause, edit, commit.
- Stems and box messages left waiting and why no Recommendation released them.
- Suggestions filed.
- Still open: list.
