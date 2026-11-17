---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- plan-status-rusage-packages

## Context
- docs/evidence-trail-plan.md#Roadmap
- docs/evidence-trail-plan.md#Principles
- docs/evidence-trail-plan.md#Current state
- docs/evidence-trail-plan.md#6. What is deliberately over-recorded
- docs/evidence-trail-plan.md#7. Redaction
- docs/roadmap-driver-plan.md
- docs/gemini-graphics-refactor-plan.md#Roadmap
- docs/gemini-graphics-refactor-plan.md#Part A: Gemini CLI provider
- docs/upstream-issue-plan.md#Roadmap
- docs/upstream-issue-plan.md#Current state
- clutch/caps.py::lineage
- clutch/caps.py::supervise_draws
- clutch/drain.py::awaiting_operator

## Goal / Why
Roadmap row 148. Roadmap section 1 wants the 0.3.0 acceptance review (`clutch/acceptance.py::accept`, which reads `docs/roadmap.md` and the plan of every 0.3.0 row owner) to start clean. Row 147 (`plan-status-rusage-packages`) fixes two stale claims. Four of the six plans the review reads still describe other merged work as open, pending or missing. Each claim below was checked against the code at `d58427dd`:
- `docs/evidence-trail-plan.md`. The Roadmap says the Gemini normalizer waits on `gemini-provider`, but rows 32 and 33 merged. Principle 6 and Target design section 7 treat `spools/providers/` as today's capture, but row 29 replaced it with the evidence store written by `clutch/providers.py::CliAdapter.invoke`. The section 6 table says killed or timed-out calls are dropped, but since row 29 `CliAdapter.invoke` writes their `end.json` with the partial output. Current state is the baseline from before the plan's rows merged, but it reads as present: `Parsed` has no `model` (row 32 added `clutch/providers.py::Parsed.model`); nothing pins the Codex cached-token basis (row 30 added `clutch/evidence/codex.py::INPUT_INCLUDES_CACHED`); the raw capture is written only at exit with no arrival times (row 29 writes `start.json` before the spawn and records a time per stdout line); the exec seam reports no resource usage (`clutch/seams.py::reap_outcome` calls `on_rusage`, and row 123 records it in `end.json`).
- `docs/roadmap-driver-plan.md`. The summary says the driver publishes to the Marketplace and that the operator handles held tickets "today by hand". `clutch/roadmap.py::ship` uploads only to PyPI, only under `release.publish`, and keeps the VS Code package through `clutch/release.py::run_packages` (decision 20, row 108). The supervisor step handles held tickets (rows 89 and 96). Status names the stem `supervise-idle-point`; the ticket that merged is `supervise-at-idle-point` (row 114). Current state says Rework-update fires only on `split` and nothing runs it for `premise_failed` or a spent cap. `clutch/runner.py::failure_terminal` runs `clutch/runner.py::supervise_step` for both, from `runner.drive` and `clutch/daemon.py::TicketWriter.consume_result` (rows 89 and 96), and `clutch/supervise_idle.py::supervise_idle` runs it at the idle point (row 114). Current state says a cap's lineage starts at the last operator keep, but `clutch/caps.py::lineage` also counts supervisor keeps (row 89, box-000530).
- `docs/gemini-graphics-refactor-plan.md`. The Roadmap says Part A waits on its agent capture and `evidence-normalize-gemini` waits on `gemini-provider`; rows 32 and 33 merged. Part A's Current state says there is no Gemini adapter, watchdog branch or `live_call` label. Since row 32, `clutch/providers.py::ADAPTERS` holds `GeminiAdapter`, `clutch/watchdog.py::CallMeter` reads Gemini's `tool_use` events, and `clutch/observe.py::live_call` labels gemini processes.
- `docs/upstream-issue-plan.md`. The Roadmap says the plan waits on its agent capture; row 34 merged. Current state says the CORE_TEMPLATE rule names no way to report. Since row 34 it names `clutch issue` (`clutch/hostfiles.py`, `clutch/issue.py`).

After this ticket every one of these claims names what merged, and each Current state section that records the baseline before its plan's rows merged says so in a lead sentence instead of being rewritten. This ticket depends on row 147 because both edit `docs/evidence-trail-plan.md` and `docs/roadmap-driver-plan.md`. It starts from row 147's merged text and leaves the parts row 147 changed alone.

## Scope in / Scope out
In: edit only the sentences listed here. Before writing each one, read the code it cites and state only what that code shows. Keep every heading's text unchanged, because roadmap section 7 fixes the plan section names.

docs/evidence-trail-plan.md:
1. Roadmap, the "What needs it" sentence: the clause "the Gemini normalizer, which waits on `gemini-provider` (0.3.0)" says both have merged (rows 32 and 33).
2. Principles, item 6: "Capture replaces today's always-on `spools/providers/`" says capture replaced it (row 29).
3. Current state: add a lead sentence under the heading. It says the section records the code before this plan's rows merged, with captures counted at `0895b5d4`, and names what merged since: rows 28 and 29 replaced `spools/providers/` with the evidence store, `CliAdapter.invoke` writes `start.json` before the spawn and `end.json` with arrival times, row 30 pins the Codex cached-token basis (`INPUT_INCLUDES_CACHED`), row 32 added `Parsed.model`, and row 123 records the exec seam's `on_rusage` figures. Change "handles its CLI today" and "What clutch keeps today:" so they refer to that baseline. Leave the table and the bullets as written.
4. Target design section 6, the "Killed or timed-out calls" row: "dropped today" says these calls were dropped before row 29.
5. Target design section 7, first sentence: "as `spools/providers/` does today (`providers.py:384-388`)" names `CliAdapter.invoke`, which replaced that writer in row 29.

docs/roadmap-driver-plan.md:
6. Summary paragraph, the two sentences about held tickets and releases. The operator did the held-ticket sequence by hand before the supervisor step (rows 89 and 96). At release the driver bumps the version and tags it (`clutch/release.py::release`), uploads to PyPI only when `release.publish` is set, and keeps the VS Code package for the owner's Marketplace upload (decision 20, row 108). Do not use the phrase "hand upload", because row 147's criteria refuse it in this file.
7. Status: replace `supervise-idle-point` with row 114, `supervise-at-idle-point`.
8. Current state, the Rework-update bullet: replace its bold lead and the "Nothing runs it" sentence. Rework still runs on a `split` verdict or an over-bound render. Since rows 89 and 96, `failure_terminal` also runs `supervise_step` for a `premise_failed` or spent-cap terminal routed to the Reject queue, from `runner.drive` and `TicketWriter.consume_result`, and row 114 runs it at the idle point (`supervise_idle`).
9. Current state, the machine-keep bullet. The lineage sentence says the lineage starts at the last operator or supervisor keep (`clutch/caps.py::lineage`) and that `caps.supervise` bounds supervisor keeps (`clutch/caps.py::supervise_draws`, row 89). In the same bullet, "for a person" in the `awaiting_operator` sentence follows from that: an operator keep releases the hold, and for a spent cap a supervisor keep also releases it, because it starts a new lineage. The bold lead stays; machine keeps still never reset a cap.

docs/gemini-graphics-refactor-plan.md:
10. Roadmap: "is release 0.3.0 (row 32); it needs nothing and waits on its agent capture" says Part A merged in 0.3.0 (row 32). The sentence saying `evidence-normalize-gemini` "waits on `gemini-provider` and uses the A0 agent capture as its fixture" says it merged (row 33) with that capture as its fixture.
11. Part A Current state: add a lead sentence under the heading. It says the bullets record the code before row 32 merged and names what merged: `GeminiAdapter` in `ADAPTERS`, the Gemini branch in `CallMeter`, and the gemini label in `live_call`. Leave the bullets as written.

docs/upstream-issue-plan.md:
12. Roadmap: "waits on its agent capture" says row 34 merged in 0.3.0.
13. Current state: add a lead sentence under the heading. It says the bullets record the code before row 34 merged and names what merged: the `clutch issue` verb in `clutch/issue.py` and the CORE_TEMPLATE rule in `clutch/hostfiles.py` that names it. Leave the bullets as written.

Out:
- Row 147's text. In docs/evidence-trail-plan.md the Status paragraph (the rusage clause), and in docs/roadmap-driver-plan.md the release tooling bullet of Current state (the `./dev.py vscode-package` sentence). This ticket does not edit either part.
- The driver plan's Current state is not re-headed. Rows 104, 124 and 147 keep its bullets current, so only items 8 and 9 change there.
- Every other sentence of the four plans, and all code and tests. No test reads plan text (owner ruling, box-000676).
- Not stale-status claims, so out: old verb names (`clutch new`, `clutch lint`, `clutch review`; box-000710 owns that sweep), dated line references and counts (`providers.py:NNN`, capture counts, CORE_TEMPLATE bytes), the "graphics-kind (0.5.0)" slot in the upstream Roadmap's budget sentence, and the driver plan's "§9" reference.
- docs/roadmap.md, docs/parallel-tickets-plan.md and docs/journal-sql-refactor-plan.md are not edited.
- Checked at `d58427dd` and still true, so unchanged:
  - evidence Status: rows 62–64 remain planned, with no tickets and no `evidence` verb.
  - evidence Open decisions: "Nothing here remains open".
  - evidence: qwen is still `unverified` (no qwen fixture), and the three-parsers risk is still deferred (row 64).
  - driver Status: rows 89–93 have merged.
  - driver Current state: split parents are still retired with `actor: operator` (`clutch/runner.py::reject_ticket`); `clutch/triage.py` is still the only caller of `clutch/author.py::author`; the drain-loop chat prompt and serve's idle hooks are still there; the roadmap is still machine-readable.
  - driver section 4: the extension still has no roadmap view.
  - driver section 5 and ticket row 5: Marketplace publishing is still manual.
  - driver section 7: "Gemini has none on this machine" (`config.yaml` declares only claude and codex).
  - gemini Status: rows 49–55 remain planned. Part B Current state holds while row 49 is open.
  - upstream Status: inbound triage is still manual, and the extension has no issue command. There is no `.github/`. Open decision 3 is still manual.
  - parallel-tickets Status: rows 42–48 remain planned.
  - journal-sql Status: "nothing in it is in effect" and "None are authored yet" hold while rows 35–41 are open.

## Scope fence
- docs/evidence-trail-plan.md
- docs/roadmap-driver-plan.md
- docs/gemini-graphics-refactor-plan.md
- docs/upstream-issue-plan.md

## Acceptance criteria
1. Reading `docs/evidence-trail-plan.md#Roadmap`, `#Principles` item 6, `#6. What is deliberately over-recorded` and `#7. Redaction` shows no sentence saying the Gemini normalizer waits, that `spools/providers/` is today's capture, or that killed calls are dropped today. Each changed sentence names its merged row (32 and 33, or 29).
2. Reading `docs/evidence-trail-plan.md#Current state` shows a lead sentence placing the section before this plan's rows merged. It names rows 28–30, 32 and 123 with `CliAdapter.invoke`, `INPUT_INCLUDES_CACHED`, `Parsed.model` and `on_rusage`. The table rows and bullets are unchanged, and nothing in the section still calls the baseline "today".
3. Reading `docs/roadmap-driver-plan.md` shows a summary that no longer says the driver publishes to the Marketplace or that the operator does this "today by hand". Status names `supervise-at-idle-point` (row 114), not `supervise-idle-point`.
4. Reading `docs/roadmap-driver-plan.md#Current state` shows a Rework-update bullet that no longer says it fires only on `split` and names `supervise_step` with rows 89, 96 and 114. The machine-keep bullet says the lineage starts at an operator or supervisor keep (`clutch/caps.py::lineage`). The release tooling bullet matches what row 147 merged.
5. Reading `docs/gemini-graphics-refactor-plan.md#Roadmap` and `docs/upstream-issue-plan.md#Roadmap` shows that neither says its merged ticket waits on its agent capture. Each names row 32 (and 33) or row 34 as merged.
6. Reading the Part A `### Current state` of `docs/gemini-graphics-refactor-plan.md` and `docs/upstream-issue-plan.md#Current state` shows that each opens with a lead sentence placing its bullets before row 32 or row 34 merged and naming what merged. The bullets are unchanged.
7. `git diff --name-only main...HEAD` lists only the four fenced plans.
8. `./dev.py test` exits 0.

## Verification
```
./dev.py test
```

## Definition of rejected
The branch is thrown away if any of these hold:
- A changed sentence claims a merge, code path or config value that the cited code does not show.
- An edit lands outside the sentences listed in Scope in, a heading is renamed, or a Current state bullet or table row is deleted or rewritten instead of re-headed.
- Row 147's evidence Status clause or the driver plan's `./dev.py vscode-package` sentence is changed.
- A file outside the fence changes, or a test that reads plan text is added.

## Time budget
- expected: 15m
- stuck: 30m
