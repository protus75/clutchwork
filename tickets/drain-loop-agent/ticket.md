---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- driver-loop

## Context
- clutch/specs/ask/drain-loop.md
- clutch/specs/ask/diagnose.md
- clutch/specs/ask/drafts.md
- clutch/specs/ask/box.md
- clutch/specs/ask/running.md
- clutch/drain.py::Report.render
- clutch/roadmap.py::status
- clutch/ask.py
- tests/integration/test_ask_drain_loop.py
- tests/unit/test_ask_drain_loop.py
- clutch/roadmap.py::merged
- clutch/runner.py::reject_ticket
- docs/roadmap-driver-plan.md#7. What still comes from outside
- docs/roadmap-driver-plan.md#Open decisions
- docs/roadmap.md#6. Owner decisions

## On-demand
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 93 (`driver-loop`, owning design `docs/roadmap-driver-plan.md` sections 6 and 7) asks for a rewritten `drain-loop` prompt. `clutch prompt drain-loop` must describe what the driver does by itself and what the supervising agent loop does for a held stem or an Author draft, so that no step waits on a person.

The owner delegated the verdicts a person used to give on 2026-11-15 (`docs/roadmap.md` section 6, decision 19; driver plan open decision 5). The supervising agent loop releases:
- a stem the supervisor escalates;
- a `ticket_changed` hold;
- a stem that a Diagnose `reject` or `abandon-human` verdict routes to the Reject queue;
- an Author draft.

For each, it runs `clutch prompt diagnose <stem>` or `clutch prompt drafts` and executes the Recommendation. That is either a ticket edit, then `clutch lint` until it exits 0, `clutch review` until it approves, and `clutch confirm --yes <stem>`; or `clutch reject --yes <stem>`. A cause fix the diagnosis names goes to `clutch suggest` and is never authored by the loop.

The loop also triages the Suggestion Box. The source is the owner's instruction of 2026-11-15, beside decision 19 and driver plan open decision 5: "route all cause fix tickets into suggestion box, do not directly author, that way the triage and confirmation pathway can make the decision". Triage is part of the pathway the owner delegated. With no human in the loop (owner, 2026-11-16; decision 19), a loop that never triages leaves every cause fix it files in the box forever. So between drains the loop renders `clutch prompt box <ids>` for the messages pending when the tick starts and executes its Recommendation: `clutch triage <ids>`, `clutch dismiss <ids>`, or the ticket edits it names. Both verbs take the writer lock, so they run only with no engine running. Three bounds keep the loop from feeding itself without end:
- it triages only messages pending when the tick starts, so a suggestion it files this tick waits for the next tick;
- it triages each message at most once per tick;
- triage's verdict is final, so the loop never re-files a message triage declined.

Drafts that triage writes are released through `clutch prompt drafts`, like any Author draft.

Today `clutch/specs/ask/drain-loop.md` says the opposite. Its hard limits read "Never run `confirm` or `reject`, and never pass `--yes`", and step 3 lists every Reject-queue stem and draft under "Needs a human". The CORE_TEMPLATE supervising-session rule (`clutch/hostfiles.py`) also forbids a session to confirm or reject. Triage declined box-000508, which asked to change that rule, so this prompt is the only home for the delegation. It must therefore say that running it is the owner's standing delegation of exactly the verdicts a Recommendation names. Triage also declined box-000514 (a separate journal actor for loop verdicts). So the prompt and the docs state that these verdicts are journaled with `actor: operator` like a person's, and that `clutch roadmap merged --unattended` therefore does not count a stem the loop confirmed or kept.

After this change `clutch prompt drain-loop` prints a `/loop` prompt that tells the agent:
- what the engine already does, so it does not repeat it:
  - with `docs/roadmap.md`, drain and serve author roadmap rows ahead, release when the gate passes (publishing only under `release.publish: true`), and send a digest after every settle;
  - inside a run, the supervisor edits and keeps a `premise_failed` or cap-spent ticket at most twice per lineage, leaving `tickets/<stem>/rework.md` when it escalates;
- each tick, to observe with `clutch status` and `clutch roadmap status`;
- to handle a stall through `clutch prompt running <stem>`;
- to release each Reject-queue stem and draft through `clutch prompt diagnose` or `clutch prompt drafts`, executing the Recommendation itself;
- between drains, to triage or dismiss the Suggestion Box messages pending when the tick starts through `clutch prompt box` and its Recommendation, under the three bounds above;
- to keep the supervising fixes it allows today;
- to file cause fixes with `clutch suggest`;
- to start the engine with `clutch drain --detach`, but not again for roadmap rows alone after a drain that merged and authored nothing. With both open roadmap rows held, every such drain authors nothing, so restarting it would loop forever;
- to skip `clutch roadmap status` on a host with no `docs/roadmap.md`, where it refuses. The prompt reaches every host, so its done check must not wait on that verb.

It keeps the limits that still hold: never push, never edit a running ticket, never edit code, docs, specs, config, or conduct files, never author a ticket itself (a new ticket comes only from `clutch triage`'s Author stage), and never rerun a flake until it passes.

## Scope in / Scope out
Scope in:
- `clutch/specs/ask/drain-loop.md`: rewrite the whole prompt. It keeps the `/loop ` prefix, the `${state_dir}` placeholder (in `${state_dir}/drain.out` and `${state_dir}/engine.log`), and no other `$`. These phrases appear verbatim: `standing delegation`, `Confirm or reject only by executing a Recommendation`, `never pass \`--extension\``, `actor: operator`, `Never push`, `merged nothing and authored nothing`, `no \`docs/roadmap.md\``, `only between drains`, `pending when the tick starts`, `at most once per tick`, `never re-file`. It does not contain `never triage or dismiss` or `left for the owner`. It says, in this order:
  1. The role: the supervising agent loop for the clutch engine. Running this prompt is the owner's standing delegation of the verdicts that a `clutch prompt diagnose`, `clutch prompt drafts`, or `clutch prompt box` Recommendation names. For those Recommendations it overrides the conduct file's rule that a supervising session may not confirm or reject, retry a stem whose caps are spent, or rewrite a ticket the engine authored. Use only clutch verbs.
  2. What the engine does by itself, as in `## Goal / Why`.
  3. Each tick:
     - Observe: `clutch status`, `clutch roadmap status`, the tail of `${state_dir}/drain.out`. On a host with no `docs/roadmap.md`, skip `clutch roadmap status` (it refuses there) and treat the host as having no `next:` rows. A held writer lock or a running stem means an engine is running.
     - A running engine that is making progress is left alone. A stalled one (no new journal or `drain.out` output for 30+ minutes while a stem runs): name the root cause in one sentence, run `clutch prompt running <stem>`, carry out the prompt it prints, and execute its Recommendation (wait, `clutch stop`, or `clutch kill`).
     - With no engine running:
       - each Reject-queue stem goes through `clutch prompt diagnose <stem>`. The agent carries out the prompt it prints, then executes the Recommendation itself, being the person that prompt says to wait for. A ticket edit touches only `tickets/<stem>/ticket.md` and never changes `## Goal / Why` or removes an acceptance criterion (the engine supervisor's allowed-edit limit); a Recommendation that needs either is executed as `clutch reject --yes <stem>` plus `clutch suggest` for the replacement. After the edit, `clutch lint <stem>` runs until it exits 0, `clutch review <stem>` until it prints approve (repairing each finding), then `clutch confirm --yes <stem>`. A retirement is `clutch reject --yes <stem>`;
       - drafts go through `clutch prompt drafts` and its `clutch confirm --yes` and `clutch reject --yes` steps;
       - only between drains (`clutch triage` and `clutch dismiss` take the writer lock), the Suggestion Box messages `clutch status` lists as pending or reopened go through `clutch prompt box <id> ...`, taking only messages pending when the tick starts. The agent carries out the prompt it prints, then executes its Recommendation itself, being the person that prompt says to wait for: `clutch triage <id> ...`, `clutch dismiss <id> ...`, or an edit it names to an existing ticket, made under the Reject-queue edit rule above, with `clutch confirm --yes` only for a draft or Reject-queue stem (confirm refuses any other). A Recommendation to write a new ticket is executed as `clutch triage <id>`, whose Author stage writes it. Each message is triaged at most once per tick, and a suggestion filed this tick waits for the next tick. Triage's verdict is final: never re-file a message triage declined or tombstoned. Drafts triage writes are released through `clutch prompt drafts` as above;
       - a fix needing no verdict (lint or format errors, a file missing from `## Scope fence` or `## Context`, a stale path, a wording fix) keeps today's rule: name the root cause, edit only that `ticket.md`, run `clutch lint <stem>` until it exits 0, and commit that one file by explicit path. A requisition-stage premise park is released by the committed edit with no confirm;
       - a cause fix a diagnosis or Recommendation names goes to `clutch suggest "<summary>"`.
     - Start the engine with `clutch drain --detach` when a stem is eligible. Also start it when `clutch roadmap status` shows a `next:` row, unless the last drain this loop started merged nothing and authored nothing: the `merged:` count in `clutch status` did not grow while it ran, and its `roadmap_drive` events in `${state_dir}/engine.log` hold no `roadmap: authored` line. Such a drain found its open roadmap rows held, and another would author nothing either. Never start one while the lock is held.
     - Done check: no engine is running, the start rule above starts none, no Reject-queue stem or draft is left that a Recommendation releases, every box message pending when the tick started went through `clutch prompt box` this tick, and this tick changed nothing. A message whose triage errored stays pending and is reported, not retried within the tick.
  4. Verdicts this loop gives are journaled with `actor: operator`, like a person's, so `clutch roadmap merged --unattended` does not count a stem it confirmed or kept.
  5. Hard limits:
     - confirm or reject only by executing a Recommendation, always with `--yes`; never pass `--extension`;
     - never re-offer a stem whose caps are spent except through a reviewed edit and `clutch confirm --yes`;
     - never edit `ticket.md` while that stem is running (a mid-run edit causes a `ticket_changed` hold);
     - never change a ticket's `## Goal / Why` or remove an acceptance criterion;
     - never edit code, docs, `docs/roadmap.md`, conduct files, specs, or config, and never author a ticket yourself; a new ticket comes only from `clutch triage`;
     - triage or dismiss a Suggestion Box message only by executing a `clutch prompt box` Recommendation, only between drains, only for messages pending when the tick starts, and at most once per tick; triage's verdict is final, so never re-file a message it declined;
     - never push, run a tree-wide destructive git verb, delete `clutch.lock`, or rerun a flaky failure until it passes;
     - do not fix an engine, gate, environment, or fixture cause; `clutch suggest` it;
     - for each fix, name the class-prevention change and `clutch suggest` it without building it.
  6. Final report, terse:
     - merged this session, and releases tagged;
     - verdicts executed (stem or box id, verdict, the prompt whose Recommendation it came from, commit of any edit, ticket or decision record triage wrote);
     - fixes made (stem, root cause, edit, commit);
     - stems and box messages left waiting and why no Recommendation released them;
     - suggestions filed;
     - a `Still open:` list.
- `tests/integration/test_ask_drain_loop.py::test_drain_loop_keeps_owner_verdict_limits`: its first assertion, `assert "Never run \`confirm\` or \`reject\`" in text`, becomes `assert "only by executing a Recommendation" in text`. Its `ticket_changed` assertion stays. Nothing else in the file changes.
- `docs/how-clutch-works.md` section 7.5 (written by `driver-loop`): add one paragraph on the supervising agent loop. `clutch prompt drain-loop` prints its prompt. It releases Reject-queue stems and drafts by executing `clutch prompt diagnose` or `drafts` Recommendations, with `clutch confirm --yes` or `clutch reject --yes`. It files cause fixes with `clutch suggest` and never authors a ticket itself. Between drains it triages or dismisses the Suggestion Box messages pending when its tick starts, each at most once per tick, by executing a `clutch prompt box` Recommendation; triage's verdict is final. Running the prompt is the owner's delegation of those verdicts. They are journaled with `actor: operator`, so `roadmap merged --unattended` does not count those stems. Nothing else in the file changes.
- A new test file, `tests/integration/test_ask_drain_loop_agent.py`.

Scope out:
- `CORE_TEMPLATE` in `clutch/hostfiles.py`, `CLAUDE.md`, and `AGENTS.md`: box-000508 was declined; this prompt carries the delegation.
- The journal actor of `confirm` and `reject`: box-000514 was declined; the verdicts stay `actor: operator`.
- Engine bounds on triage: the pending-at-tick-start, once-per-tick, and final-verdict bounds are prompt text; `clutch triage`, `clutch dismiss`, and the Author stage run unchanged.
- `clutch/ask.py`, the `prompt` verb, the other `clutch/specs/ask/` prompts, `clutch/help.py`, `clutch/docs/host-running.md`, and the extension: their text about the drain-loop prompt stays true.
- Any engine code: the prompt describes the engine; it changes nothing the engine does.

## Scope fence
- clutch/specs/ask/drain-loop.md
- tests/integration/test_ask_drain_loop.py
- tests/integration/test_ask_drain_loop_agent.py
- docs/how-clutch-works.md

## Acceptance criteria
1. `tests/integration/test_ask_drain_loop_agent.py::test_prompt_delegates_recommendations` renders `ask.render("drain-loop", "", config, tmp_path)` against `tests/integration/test_config.py::VALID`. The text contains each of these:
   - `clutch prompt diagnose`, `clutch prompt drafts`, `clutch prompt running`;
   - `clutch confirm --yes`, `clutch reject --yes`;
   - `clutch lint`, `clutch review`, `clutch suggest`;
   - `clutch roadmap status`, `clutch drain --detach`;
   - `actor: operator`, `--unattended`, `release.publish`, `rework.md`, `standing delegation`, `## Goal / Why`.

   It does not contain `Never run \`confirm\` or \`reject\``, `Needs a human`, or `never pass \`--yes\``. `standing delegation` comes before the first `clutch confirm --yes`. Ruled out: a prompt that still forbids the delegated verdicts, omits one of the three prompts whose Recommendations it executes, or leaves the operator actor unstated.
2. `tests/integration/test_ask_drain_loop_agent.py::test_prompt_keeps_hard_limits` asserts the same rendered text contains `Confirm or reject only by executing a Recommendation`, `never pass \`--extension\``, `Never push`, `ticket_changed`, `docs/roadmap.md`, `Still open:`, `merged nothing and authored nothing`, and `no \`docs/roadmap.md\``, and has no `${` left. Rendered with `VALID`'s `state_dir: .clutch` replaced by `state_dir: custom/state` (as `tests/integration/test_ask_drain_loop.py` does), it contains `custom/state/drain.out` and `custom/state/engine.log`. Ruled out: a dropped push, extension, or running-ticket limit; a loop that restarts drains forever while its open roadmap rows are held; a done check that waits on `clutch roadmap status` on a host without a roadmap; and a placeholder left unrendered.
3. `tests/integration/test_ask_drain_loop_agent.py::test_prompt_bounds_box_triage` asserts the text rendered against `VALID` contains `clutch prompt box`, `clutch triage`, `clutch dismiss`, `only between drains`, `pending when the tick starts`, `at most once per tick`, and `never re-file`, and does not contain `never triage or dismiss` or `left for the owner`. Ruled out: a loop that never triages, so the cause fixes it files wait in the box forever with no human to triage them; a loop that triages while a drain holds the writer lock; and a loop that feeds itself without end by triaging a suggestion it filed in the same tick, triaging a message twice in one tick, or re-filing a message triage declined.
4. `./dev.py test tests/integration/test_ask_drain_loop.py tests/unit/test_ask_drain_loop.py tests/integration/test_ask.py` exits 0, with `test_drain_loop_keeps_owner_verdict_limits` changed only as `## Scope in / Scope out` names.
5. The docs command in `## Verification` exits 0: `docs/how-clutch-works.md` section 7.5 names `clutch prompt drain-loop`, `clutch prompt box`, `actor: operator`, and `--unattended`.
6. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_ask_drain_loop_agent.py
./dev.py test tests/integration/test_ask_drain_loop.py tests/unit/test_ask_drain_loop.py tests/integration/test_ask.py
uv run python -c "import pathlib; t = pathlib.Path('docs/how-clutch-works.md').read_text(); s = t.split('### 7.5 Roadmap driver')[1].split('## 8.')[0]; assert all(w in s for w in ('clutch prompt drain-loop', 'clutch prompt box', 'actor: operator', '--unattended'))"
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- the prompt lets the loop confirm or reject anything but a Recommendation's verdict, or without `--yes`, or with `--extension`;
- the prompt lets the loop triage or dismiss a Suggestion Box message other than by executing a `clutch prompt box` Recommendation between drains for a message pending when the tick starts, lets it triage a message more than once per tick or re-file a message triage declined, or lets it start another drain for `next:` rows after a drain that merged and authored nothing;
- the prompt lets the loop push, edit a running ticket, author a ticket itself instead of through `clutch triage`, or edit code, docs, specs, config, or conduct files;
- it edits `CORE_TEMPLATE`, `CLAUDE.md`, `AGENTS.md`, `clutch/ask.py`, another ask prompt, or engine code;
- an existing test other than the one assertion named in `## Scope in / Scope out` changes;
- a file outside `## Scope fence` changes.

## Time budget
- expected: 45m
- stuck: 120m
