<!-- Evidence copy for ticket plan-drain-prompts (2026-11-16). The session's supervising loop procedure; its "Since drain-loop-agent merged" section lists what the session added on top of `clutch prompt drain-loop`. Machine paths, another host, credential names, and shell-specific launch commands are replaced with placeholders or generic wording; nothing else changed. -->

# Roadmap supervising loop

Procedure for the self-paced `/loop` that runs `docs/roadmap.md` unattended. Read this file and
`<session state file>` at the start of every tick. Append one dated line per tick to the
state file's log, and keep its "Needs human" and "Still open" lists current.

## Authority (owner, chat of 2026-11-15)

The owner delegated the operator role to this loop:

- Run `clutch prompt diagnose <stem>`, `clutch prompt drafts`, `clutch prompt box <ids>`, and
  `clutch prompt running <stem>` exactly as the owner does, and carry out the Recommendation each
  one produces, including `confirm --yes` and `reject --yes`, the ticket edits it names (then
  `clutch lint` to exit 0 and `clutch review` to approve before any confirm), `triage`, and
  `dismiss`. The owner has accepted these recommendations by hand and trusts them.
- Every cause-fix ticket a diagnosis or investigation calls for goes to the Suggestion Box with
  `uv run clutch suggest "<summary with evidence paths>"`. Never author a cause fix directly;
  triage and the drafts verdict decide it. Instance fixes and roadmap rows may be authored.
- Before each roadmap phase starts, bump the minor version and create an annotated tag `v<version>`.
- Hard limits that still stand: never push or run any remote-mutating verb; never edit code, docs,
  specs, config, CLAUDE.md, or AGENTS.md on main (tickets do that), except the version-bump files
  (`pyproject.toml`, `uv.lock`, `vscode-clutchwork/package.json`, `vscode-clutchwork/README.md`)
  until `release-verb` merges, after which use `uv run clutch release --minor`; commit only files
  this loop wrote, by explicit path; never run a tree-wide destructive git verb; never delete
  `clutch.lock`; never edit a ticket while its stem is running; never rerun a flaky failure until
  it passes and call it fixed.

## Phase map

Since `roadmap-plan-corrections` merged (19dfce12), the roadmap's release names ARE the versions:
a phase is bumped and tagged at its start with `uv run clutch release --minor`.

| Version tag | Roadmap release | Start gate (docs/roadmap.md section 1) |
|---|---|---|
| v0.3.0 (tagged at c761b213) | 0.3.0 truth, hygiene, infrastructure, driver | none |
| v0.4.0 | 0.4.0 journal query layer (conditional) | re-measurement (row 35 capture) shows journal reads still dominate; else skip the phase, no bump |
| v0.5.0 (or v0.4.0 if 0.4.0 slides) | 0.5.0 parallel runs, graphics kind | dedup rows merged; Gemini A0 fact 7 answered (done: negative, api-provider-client joins) |
| next | 0.6.0 training, panels, index | evidence store captured at least one full drain |
| next | 0.7.0 document agent | `isolated-readonly-call` merged; owner's lens prompts adapted (agent task) |

A phase is done when every row in its section 8 tables is merged, skipped with evidence, or parked
on a hand test listed under "Needs human". Gates are counted in runs, never in wall-clock time
(owner, 2026-11-16: "times in the roadmap are for human schedules, not AI"): read any "for a week",
"one week", or "daily" gate as "the next 10 merged tickets" until `roadmap-no-human-gates`
rewrites the text.

**No human in the loop** (owner, 2026-11-16: "there will be no human in this loop; all human
guidance was supposed to be encoded in prompts before this run started"). There is no "Needs
human" category. Every prerequisite takes an AI path:
- Hand test (CLI facts, GitHub prefill limits, journal re-measurement, conflict-facts read): an
  Agent runs it in a scratch directory, saves the captured output, and the row's author commits
  it as the ticket's evidence.
- Open owner decision in a plan: take the plan's "Proposed" option; where none exists, three
  independent Agents each pick and argue an option, a fourth picks the winner, and the choice is
  recorded in the plan through a ticket before the dependent row is authored.
- GO baseline or calibration that the plans give to hand labels (`visual_baseline`, review
  baselines): labels come from an AI panel of a different model family than the judge being
  calibrated (roadmap decision 13), and the gate is the judge's agreement with that panel.
- `gate: operator`: not allowed; every gate is a command.
- Missing credential (the only true external input): report it once, skip the rows that need
  it, and have an Agent find a path through providers that are already authenticated before
  the dependent phase starts.
Publishing to PyPI or the Marketplace stays off: it is a push, and the owner has not said push.
Once `release-publish` and `driver-loop` merge, the driver may run `release` itself when a gate
passes: before bumping, check `git tag` and `pyproject.toml`; never bump twice for one phase.

## Since driver-loop merged (0bd495c1, 2026-11-16)

The engine runs the roadmap driver itself at every drain/serve idle point: it strikes and links
rows, authors up to 2 rows ahead (`roadmap_row`, confirmed), runs the current release's gate
block, and when the gate passes runs `ship` (release --minor, tag, then publish only under
`release.publish: true`), then sends a digest. So this loop NO LONGER runs `roadmap author` or
bumps/tags by hand: watch `engine.log` `roadmap_drive` events and `git tag`, and only step in
when the driver is stuck (a row that waits forever, a gate that fails for a non-row reason, an
error in the step). The phase bump the owner asked for is the driver's `ship` at gate pass, which
is the same moment as "before the next phase starts"; never bump twice.

## Since drain-loop-agent merged (2cb89253, 2026-11-16): use the engine's prompt

Each tick, render `uv run clutch prompt drain-loop` and follow it: it now encodes the owner's
delegation (diagnose, drafts and box Recommendations, bounded triage, no human). The steps below
remain only as this session's additions to it:
- start drains with `uv run clutch drain --detach` from an interactive shell
  (a provider credential lives only in interactive shells);
- match this checkout's engine as `^<checkout>/.venv/bin/python3 -m clutch drain`
  (another host on this machine runs its own clutch drain);
- driver wedge watch (box-000540, declined by triage 2026-11-16): if a drain or serve exits within
  a minute of starting with a non-Refusal error from the roadmap driver step (engine.log / drain.out
  traceback naming clutch/roadmap.py or a pydantic ValidationError), nothing unattended can
  recover; send the owner a notification with the error and the offending roadmap row;
- when the driver authors ahead the drain rarely quiesces, so for a pending box message that
  matters (an engine-wedge or run-wasting cause), `clutch stop` at a ticket boundary, triage,
  and restart, rather than waiting for quiescence.

## Each tick

1. **Observe.** `uv run clutch status`, `tail -40 .clutch/state/drain.out`, and whether a writer
   holds the lock (`pgrep -af "<checkout>/.venv/bin/python3 -m clutch (drain|serve)"`
   or a `clutch triage|run` launched from this checkout; a running stem in status). Another host
   (`<another host's checkout>`) runs its own clutch drain: never match a bare `clutch drain`.
2. **Drain running.** If it is making progress (new drain.out or journal output in the last 30
   minutes), do nothing and wake in about 25 minutes. If a stem has run past its `stuck` budget or
   shows no output for 30+ minutes, run `uv run clutch prompt running <stem>`, have an Agent carry
   out that prompt read-only and return its report, then follow its Recommendation (wait, `clutch
   stop`, or `clutch kill`).
3. **No drain running.** In this order:
   a. **Reject queue and blocked stems.** For each stem awaiting the operator: render
      `uv run clutch prompt diagnose <stem>`, have an Agent carry out that prompt (read-only) and
      return the report with its Recommendation, then execute the Recommendation. A cause ticket
      it proposes goes to `clutch suggest`, never authored. Name the root cause in one sentence in
      the state log before any edit.
   b. **Suggestion Box.** For pending messages: render `uv run clutch prompt box <ids>`, have an
      Agent carry it out, then run the `clutch triage` / `clutch dismiss` it recommends.
   c. **Drafts.** If `uv run clutch prompt drafts` lists drafts, have an Agent carry out that
      prompt, then run the `confirm --yes` / `reject --yes` commands it recommends.
   d. **Supervising fixes** from `clutch prompt drain-loop` (lint, missing fence or Context entry,
      stale path, wording) on non-running tickets, committed by explicit path.
   e. **Top up the queue.** Since `roadmap-author` merged (d37d2709), top up with the engine's
      own driver verb between drains (it takes the writer lock): `uv run clutch roadmap author --ahead <window>`
      from an interactive shell, where the
      window is 2 or 4 per the drift rule below. Its rows start confirmed (source
      `box:roadmap_row`) and count toward the 0.3.0 gate's driver-authored rows. Hand-author only
      `driver-loop` (held until rows 89-92 merge) and a row the verb declines twice, recording why.
      Owner, 2026-11-16: authoring 17 tickets before a drain was more than
      expected; spec drift from source decides the window. Author nothing while more than 4
      roadmap tickets are confirmed and unrun. Classify every failure as drift (a premise park, or
      a requisition or review snag citing code an earlier merge changed) or not, and log it. Any
      drift failure: the window drops to 2 (top up only when fewer than 2 are confirmed and
      unrun, at most 2 per wave). No drift over a whole drain: it may return to 4. Never author a
      row before every stem in its `Depends on` has merged. When the window allows, author the
      next rows in the current phase (release order, then priority, then the Runs before column),
      skipping rows that need a hand test (list them under "Needs human"). Author with one Agent
      per row, in parallel, using the author prompt in `author-roadmap-rows.js` (beside this file)
      (`authorPrompt` and `COMMON`, with `args.where` = current HEAD and version), then one
      audit Agent per ticket with `auditPrompt`, and a repair Agent for blocking findings. Run
      that file as a Workflow (args `{where, rows: [...]}`) only when ultracode is on or the
      owner asked for a workflow. Authoring overlaps a running drain (owner, 2026-11-16: waiting
      on authoring before draining was too slow). An author lints and self-checks fully before its
      first `clutch review`, so review rounds are few; if a ticket it is still repairing gets
      dispatched, it stops editing that ticket. Never hold a drain for an authoring agent. For roadmap 0.2.0: once `driver-loop` has merged, stop hand-authoring and let the
      driver author the remaining rows (its ship gate needs at least three rows the driver
      authored and ran with no operator verdict); hand-author again only if the driver authors
      nothing for two consecutive idle ticks, and record why.
   f. **Phase change.** When the current phase is done and the next phase's start gate passes:
      bump the minor version and tag (see Authority), update the state file, then top up.
   g. **Start work.** If any stem is eligible, `uv run clutch drain --detach`
      from an interactive shell. Never while the lock is held. The interactive shell matters: a provider
      credential is set only in fresh interactive shells (the shell profile), not in this session's tool
      shell, and the engine needs it once that provider is configured. Never print the credential.
4. **Done check.** No drain running, nothing eligible, nothing to author whose prerequisites are
   met, and no action this tick: stop the loop and print the final report.

## Final report (and the state file's summary)

Merged this session; tickets authored; fixes made (stem, root cause, edit, commit); verdicts
issued (stem, verdict, which prompt recommended it); suggestions filed; needs human (one line
each with the exact verb or evidence that releases it); Still open.
