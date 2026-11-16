---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- rework-supervise-gate
- supervise-cap-lineage

## Context
- clutch/runner.py::drive
- clutch/runner.py::failure_terminal
- clutch/daemon.py::apply_rework
- clutch/rework.py
- clutch/caps.py
- clutch/stages.py::lift_outbox
- clutch/status.py::reject_queue
- clutch/drain.py::parked_blob
- clutch/drain.py::awaiting_operator
- clutch/drain.py::reofferable
- clutch/reconcile.py::orphans
- tests/unit/test_premise_overruled.py
- tests/integration/test_requisition_gate.py
- docs/how-clutch-works.md#3.3 What the engine writes back
- docs/how-clutch-works.md#6.1 Order of handling
- docs/how-clutch-works.md#6.6 The Reject queue, keep and kill
- docs/roadmap-driver-plan.md#2. The supervisor step

## On-demand
- clutch/specs/ask/diagnose.md

## Goal / Why
Roadmap row 89 (`docs/roadmap.md`, owning design `docs/roadmap-driver-plan.md` section 2) wires together three engine pieces that the owner chained by hand for 78 of 142 verdicts: Diagnose, a reviewed Rework `update`, and a keep. Today Rework runs only for a `split` verdict or an over-bound render (`clutch/runner.py::drive`). A ticket routed to the Reject queue because Implement said `premise_failed`, or because a cap is spent, waits for a person. Any keep but an operator's leaves its spent caps spent.

`rework-supervise-gate` gives Rework a supervisor mode: Diagnose's lessons as input, update-or-escalate only, and an allowed-edit gate that refuses a split, an unchanged ticket, a changed `## Goal / Why`, or fewer acceptance criteria before any review. On a refusal it returns the refused proposal. `supervise-cap-lineage` makes a `reject_verdict keep actor: supervisor` start a lineage, adds `caps.supervise` (default 2), and counts `supervise` draws since the last operator keep (`caps.supervise_draws`). This ticket is the trigger that uses both. When `drive` ends an attempt in a terminal routed to the Reject queue as a `premise_failed`, or as a `gate_failed` with a spent cap, and the stem has supervisor budget left, the engine:

1. Runs supervisor-mode Rework with the terminal's findings and the lineage's diagnosis lessons. On approve, Rework's publication commits the edit as `clutch(<stem>): rework`.
2. After journaling the terminal, journals one `supervise` draw and `reject_verdict keep actor: supervisor`. The stem leaves the Reject queue with a fresh lineage, and drain or serve re-offers the edited ticket.
3. When the proposal is refused, snagged, or escalated, writes `tickets/<stem>/rework.md` (trigger, outcome, refusing findings, and the proposed ticket when there is one). It lifts the file as `clutch(<stem>): rework-proposal` and leaves the stem in the Reject queue, so whoever answers it (`clutch prompt diagnose` under the owner's no-human loop) starts from the engine's best attempt.

Departures from the plan, and why:
- The plan says "premise_failed or a spent cap". This ticket supervises a spent-cap route only when its terminal is `gate_failed`. An `infra_error`, `timeout`, `invalid_artifact`, or `incomplete` terminal is a provider or runtime failure that no allowed edit (lint, fence or Context entry, stale path, wording) can fix, and its Rework call would go to the provider that just failed.
- `ticket_changed` and `abandoned` stay with the person (open decision 2, Proposed option). The step runs only from `drive`, never from serve's merge-queue deliveries (`TicketWriter.consume_result`, `consume_handoff`), as the plan places it "inside `runner.drive`'s terminal handling".
- It never runs in an attempt that already ran Rework. A second Rework in the same attempt would reuse that attempt's Effect keys (`llm/<stem>/<seq>/rework/<attempt>/<n>`, `ticket-plane/<stem>/<attempt>/rework`) and replay the first call.

Every effect of the step (Rework calls, publication, the `rework.md` lift) runs before the terminal is journaled. A prototype that ran it after the terminal left a failed Rework call's Effect intent open. `clutch/reconcile.py::orphans` then reaped the stem as `abandoned`, a second terminal for one run, and `audit_journal` flagged it (`one_terminal_per_run`). Only the `supervise` draw and the keep signal follow the terminal, because `reject_queue` clears a stem only on a verdict that comes after its routed terminal.

## Scope in / Scope out
Scope in:
- `clutch/runner.py`:
  - `failure_terminal` gains the keyword `supervised: bool = False`. `drive` passes `supervised=True` on exactly two calls: the `attempts`-cap call and the final call. Every other caller keeps the default.
  - In `failure_terminal`, after the terminal dict is complete (`dispatch` and `routed` decided) and before it is journaled, the supervisor step runs only when all of these hold:
    - `supervised` is true;
    - not `split`, not `rework_requested`, and `provider_drought` is None;
    - `terminal.get("routed") == "reject_queue"`, and no finding has code `ticket_changed`;
    - `terminal["to"] == "premise_failed"`, or `terminal["to"] == "gate_failed"` and `spent(ctx.config.caps, history, stem, pending=terminal)` names a cap;
    - `ctx.worktree(stem).exists()`;
    - `supervise_draws(history, stem) < ctx.config.caps.supervise`.
  - The step builds `Supervise(trigger, lessons)`. `trigger` is `spent_reason(cap)` for the cap that `spent(..., pending=terminal)` names, else `"premise_failed"`. `lessons` is every `diagnosis` signal's `lessons` for the stem within `caps.lineage(history, stem)`, in journal order, without repeats. It calls `clutch.daemon.apply_rework(ctx, ticket, findings, attempt=attempt, supervise=...)`.
    - Result `ok` with a `ReworkOrder` whose action is `update`: read `sha = HEAD:tickets/<stem>/ticket.md`. After the terminal is journaled, journal `caps.consume(journal, stem, "supervise", sha)` and then the signal `{"signal": "reject_verdict", "verdict": "keep", "actor": "supervisor", "ticket_sha": sha}`, in that order.
    - Any other result (a non-`ok` outcome, or an `escalate` order): write `tickets/<stem>/rework.md` into the worktree outbox with `ctx.fs.write`, passed through `ctx.driver.redactor.scrub`, then call `lift_outbox(ctx, stem, "rework-proposal", attempt=attempt, only="rework.md")`. Both happen before the terminal is journaled. The file is these lines: `# Supervisor Rework escalated`, a blank line, `- trigger: <trigger>`, `- outcome: <result outcome>`, and `- action: <the artifact's action, or none>`. Then a blank line, `## Findings`, a blank line, and one line ``- `<code>`: <message> -- <paved_road>`` per result finding (`- none` when there are none). When the result's artifact carries a proposal (`tickets` non-empty), the file ends with a blank line, `## Proposed ticket`, a blank line, and the first proposal's ticket text verbatim between ` ````markdown ` and ` ```` ` fence lines.
  - `failure_terminal` still returns the producing outcome, and journals exactly one terminal transition per run. With a spent `supervise` budget or a missing worktree there is no Rework call, no `rework.md`, no draw, and no keep.
- `tests/integration/test_requisition_gate.py`: in each of `test_unreviewed_ticket_is_reviewed_once_then_runs`, `test_approved_content_runs_without_review`, `test_render_feasibility_snag_proceeds_to_implement` and `test_edit_releases_and_reviews_the_new_content`, the Implement `premise_failed` now spends `premise_bounce` (default 1) and meets the supervisor. Each test's FakeLLM script gains one last reply, `json.dumps({"action": "escalate", "tickets": []})`, and its expected surface list gains a last `"rework"`. Nothing else in the file changes.
- `clutch/specs/ask/diagnose.md`: after the sentence that names what to read, add "If tickets/${stem}/rework.md exists, read it too: it is the supervisor's last ticket edit that was refused or escalated, with the findings that stopped it." Nothing else changes.
- `docs/how-clutch-works.md`, three edits:
  - Section 3.3's lift-kind table gains the row `` `rework-proposal` | `rework.md` (the supervisor's refused or escalated edit) ``.
  - Section 6.1's step 8 becomes three steps: decide the dispatch; the supervisor step (section 6.6) when it applies; journal the terminal, then any supervisor keep. Step 9 is renumbered.
  - Section 6.6 gains a **Supervisor keep** bullet stating the trigger, the exclusions and their reasons, the keep and draw, `caps.supervise`, and the `rework.md` escalation.
  No other section changes.
- New tests in two new files: `tests/unit/test_supervisor_trigger.py`, which drives `runner.failure_terminal` against fakes as `tests/unit/test_premise_overruled.py` does (`clutch/runner.py` has a positive unit floor in `test-gate.toml`), and may import `MemoryJournal` from that file unchanged; and `tests/integration/test_supervisor_rework.py`, which may import `setup`, `dispatch` and `reply` from `tests/integration/test_requisition_gate.py`, `implement_reply` from `tests/integration/test_stages.py`, and `approve` from `tests/approval.py`, as other modules do.

Scope out:
- The supervisor step at drain or serve idle points for stems that entered the Reject queue some other way (the drain's quiescence `reject_arrival`, serve's merge-queue deliveries). That is the driver loop (`docs/roadmap-driver-plan.md` section 6).
- `clutch/specs/ask/drain-loop.md`; `CORE_TEMPLATE` in `clutch/hostfiles.py`, `CLAUDE.md` and `AGENTS.md` (the session rules do not change); `clutch/drain.py`, `clutch/scheduler.py`, `clutch/serve.py`, `clutch/daemon.py`, `clutch/rework.py`, `clutch/caps.py`, `clutch/config.py`, `clutch/status.py`, `clutch/stages.py`, and the extension.
- Any new journal signal, cap, config field, verb, or `help` entry.

## Scope fence
- clutch/runner.py
- clutch/specs/ask/diagnose.md
- docs/how-clutch-works.md
- tests/integration/test_requisition_gate.py
- tests/unit/test_supervisor_trigger.py
- tests/integration/test_supervisor_rework.py

## Acceptance criteria
1. `tests/unit/test_supervisor_trigger.py::test_keep_follows_the_terminal`. The journal holds stem `work`'s `running`, a `diagnosis` signal with lessons `["Fence tests/x.py"]`, and one `premise_bounce` draw. `failure_terminal(..., outcome="premise_failed", stage="implement", verdict="abandon-human", attempt=0, supervised=True)` runs with a faked `clutch.daemon.apply_rework` that returns `ok` with an `update` `ReworkOrder`, and `git.rev_parse` faked to `"new-sha"`. It asserts:
   - the call returns `premise_failed`;
   - the fake received `supervise == Supervise("premise_bounce cap spent", ("Fence tests/x.py",))`;
   - the journal's last three events are, in order, the terminal (`to: premise_failed`, `routed: reject_queue`), `cap_consumed` `{"cap": "supervise", "ticket_sha": "new-sha"}`, and the `reject_verdict keep actor: supervisor` signal with `ticket_sha: "new-sha"`;
   - `reject_queue(events)` lacks `work`, `spent(Caps(), events, "work") is None`, and `lift_outbox` was never called.
   Ruled out: a keep journaled before the terminal (the stem would stay queued), a missing draw, and lost lessons.
2. `tests/unit/test_supervisor_trigger.py::test_refusal_lifts_rework_md_before_the_terminal`. The same setup, but the fake returns `gate_failed` with artifact `ReworkReply(action="update", tickets=[proposal])` and one `supervise_edit` finding. It asserts:
   - `ctx.fs.write` wrote `<worktree>/tickets/work/rework.md`, containing `- trigger: premise_bounce cap spent`, `- outcome: gate_failed`, `- action: update`, the finding's code, message, and road, and the proposal text inside a ` ````markdown ` fence;
   - the faked `lift_outbox` was called once with `"rework-proposal"` and `only="rework.md"`, at a moment when the journal held no terminal for this run;
   - no `supervise` draw and no keep were journaled, and `reject_queue(events)` holds `work`.
   A second case, an `ok` `escalate` order, asserts `- action: escalate`, `- none` under `## Findings`, and no `## Proposed ticket`.
   Ruled out: an escalation without `rework.md`, effects after the terminal, and a keep on a refused edit.
3. `tests/unit/test_supervisor_trigger.py::test_supervisor_skips` is parametrized, with a recording fake `apply_rework` that each case asserts was never called:
   - `supervised=False`;
   - a `ticket_changed` finding;
   - `rework_requested=True` with `reworked=None`;
   - an `infra_error` terminal with the `infra` cap spent;
   - a `gate_failed` routed by a `reject` verdict with no cap spent;
   - a missing worktree;
   - two `supervise` draws since the last operator keep.
   A positive control is a `gate_failed` whose pending terminal spends `attempts` (four prior failed terminals): the fake was called once with trigger `attempts cap spent`. Ruled out: supervising any excluded route, and an always-off trigger.
4. `tests/integration/test_supervisor_rework.py::test_premise_terminal_is_edited_reviewed_and_kept` uses the `test_requisition_gate.py` rig with `approve(...)`. The script is `[implement_reply("premise_failed", ...), <update proposal rewording one Scope in / Scope out line>, reply("approve")]`. It asserts:
   - the request surfaces are `["implement", "rework", "requisition_review"]`, and the rework prompt contains `"trigger": "premise_bounce cap spent"`;
   - the last commit touching `tickets/gate/ticket.md` has subject `clutch(gate): rework`, and its blob equals the proposal;
   - a `reject_verdict keep actor: supervisor` follows the terminal with that blob's sha;
   - `reject_queue(events)` lacks `gate`, `awaiting_operator(events, "gate", caps)` is False, `reofferable(events, "gate", caps)` is True, and `parked_blob(events, "gate")` differs from the new blob.
   Ruled out: today's behavior, where the stem waits in the Reject queue with its `premise_bounce` cap spent.
5. `tests/integration/test_supervisor_rework.py::test_refused_edit_escalates_with_rework_md` runs the same rig with the script `[implement_reply("premise_failed", ...), <update proposal that rewords ## Goal / Why>]`. It asserts:
   - the surfaces are `["implement", "rework"]`, and `tickets/gate/ticket.md` is unchanged on main;
   - `tickets/gate/rework.md` is committed on main by a commit with subject `clutch(gate): rework-proposal`, and contains `supervise_edit` and the proposed Goal text;
   - `gate` is in `reject_queue(events)`, and no `supervise` draw or supervisor keep was journaled;
   - `audit_journal` of the journal returns `[]`.
   Ruled out: a published Goal change, an escalation with nothing attached, and a second terminal for the run.
6. `tests/integration/test_supervisor_rework.py::test_spent_supervise_cap_leaves_the_stem_for_the_operator` journals two `supervise` draws for `gate` before dispatch and scripts only the Implement `premise_failed`. It asserts the surfaces are `["implement"]`, no `tickets/gate/rework.md` exists, and `gate` is in `reject_queue(events)`. Ruled out: a third supervisor attempt in one operator lineage.
7. `./dev.py test tests/integration/test_requisition_gate.py` exits 0 with only the eight edits `## Scope in / Scope out` names: one script reply and one surface per test.
8. `./dev.py test tests/integration/test_terminal.py tests/integration/test_reject_queue.py tests/integration/test_caps.py tests/integration/test_drain.py tests/integration/test_serve_admission.py tests/integration/test_shakeout.py tests/integration/test_daemon_soak_runner.py tests/integration/test_reliability_battery.py tests/integration/test_kill_cli_activation.py tests/integration/test_watchdog_activation.py tests/integration/test_second_problems.py tests/integration/test_audit.py tests/integration/test_ask.py tests/unit/test_premise_overruled.py` exits 0 unedited.
9. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_supervisor_trigger.py
./dev.py test tests/integration/test_supervisor_rework.py
./dev.py test tests/integration/test_requisition_gate.py
./dev.py test tests/integration/test_terminal.py tests/integration/test_reject_queue.py tests/integration/test_caps.py tests/integration/test_drain.py tests/integration/test_serve_admission.py tests/integration/test_shakeout.py tests/integration/test_daemon_soak_runner.py tests/integration/test_reliability_battery.py tests/integration/test_kill_cli_activation.py tests/integration/test_watchdog_activation.py tests/integration/test_second_problems.py tests/integration/test_audit.py tests/integration/test_ask.py tests/unit/test_premise_overruled.py
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- the supervisor runs for a `ticket_changed`, `abandoned`, `infra_error`, `timeout`, `invalid_artifact` or `incomplete` terminal, from `consume_result` or `consume_handoff`, or in an attempt that already ran Rework;
- any supervisor effect runs after the terminal is journaled, or a run journals two terminals;
- a keep is journaled for a refused, snagged, or escalated proposal, or without a `supervise` draw;
- a person's verdict verbs (`confirm`, `reject`) or the machine keep change;
- a file outside `## Scope fence` changes, or a new signal, cap, config field, or verb is added;
- any existing assertion other than the eight named in `## Scope in / Scope out` is changed or weakened.

## Time budget
- expected: 100m
- stuck: 180m
