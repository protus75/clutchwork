<!-- Evidence copy for ticket plan-drain-prompts (2026-11-16). The session's kickoff prompt record: the request, the owner's corrections, the rewritten kickoff (section 3), and why each change exists. Machine paths, another host, credential names, and shell-specific launch commands are replaced with placeholders or generic wording; nothing else changed. -->

# Prompt: large automated work effort (clutch roadmap run)

Kept from the run that implemented roadmap phase 0.3.0 on 2026-11-15/16. Section 1 is the
original request, section 2 the corrections the owner gave during the run, and section 3 the
prompt rewritten so a new session starts with all of them. Section 4 says why each change exists.

## 1. Original request (2026-11-15)

> read all the docs/ I want to implement this roadmap in an aggressively automated fashion. I
> trust the prompts that I have been using for human feedback and have been accepting their
> recommendations from diagnosis for fixing blocked tickets and for confirm/reject drafts.
> Instead of directly authoring, route all cause fix tickets into suggestion box, do not
> directly author, that way the triage and confirmation pathway can make the decision.
>
> begin with the roadmap specified phase, and make sure to bump the minor version prior to each
> phase as well as tag the git repo.

## 2. Corrections given during the run

1. Gates and cadences count runs, never wall-clock time ("a week" is a human schedule).
2. No human in the loop. Hand tests, owner decisions, and calibration are agent work. If a
   person is needed, the planning failed. The only true external input is a credential.
3. Seventeen tickets authored before the first drain is too many. Spec drift from source
   decides how far ahead to author.
4. Two hours of authoring before draining is too slow. Authoring must never hold the drain.
5. Each ticket passing its own criteria is not enough: at the end of each phase, check that the
   tickets taken together satisfy the phase's plan (an end-of-phase acceptance review).
6. Acceptance gaps become roadmap rows (documentation that drives new tickets through the
   driver), never Suggestion Box messages that may or may not become tickets.

## 3. The prompt

```text
Read every document under docs/, then run <ROADMAP> (default docs/roadmap.md) to completion,
unattended, starting at the phase it names as current. You act as the operator under my
standing delegation. Everything below is the plan; nothing waits for me.

Before you start (do these first, they each cost hours when skipped):
- Check the environment: the venv's entry-script shebangs and __pycache__ match this checkout's
  path (a renamed directory leaves stale ones; clear __pycache__, `uv sync --reinstall-package`
  the scripts); every provider credential the plan needs is present (some live only in
  interactive shells: start engines from one); `./dev.py test` passes on main.
- List every credential, hand test, and owner decision the plan's prerequisites name. Hand tests
  and decisions become agent work (below). A missing credential is the only thing you report
  to me, once, up front; skip only the rows that need it and keep going.
- Bump the minor version and create an annotated tag `v<version>` before each phase starts
  (`clutch release --minor` once it exists). If the engine's own release step ships a phase at
  its gate, that IS the bump for the next phase: never bump twice.

My delegation:
- Run `clutch prompt diagnose|drafts|box|running` exactly as I would and execute each
  Recommendation, including `confirm --yes` / `reject --yes`, the ticket edits it names (then
  lint to exit 0 and `clutch review` to approve before any confirm), `triage`, and `dismiss`.
- Every cause fix goes to `clutch suggest`; never author one. Triage's verdict is final: never
  re-file what it declined. Instance fixes and conflicts inside confirmed, unmerged tickets are
  fixed by editing those tickets.
- No human in the loop: hand tests are agent-run captures committed as ticket evidence; open
  plan decisions take the plan's Proposed option, else three independent agents propose and a
  fourth judges, recorded in the plan by ticket; calibration and GO baselines use an AI label
  panel from a different model family than the judge; every gate is a command counted in
  runs, never time.
- Never push or publish (that needs me to say "push"); never run tree-wide destructive git;
  never edit code, docs, specs, or config on main yourself (tickets do that).

Authoring:
- Author at most 4 tickets ahead of the drain, 2 after any drift failure (a premise park or a
  snag citing code an earlier merge changed). Never author a row before its Depends on merged.
- Authoring overlaps the running drain; never hold a drain for it. Authors edit a scratch copy
  and replace ticket.md in one write, check `clutch status` first, and stop editing a stem the
  moment it is dispatched.
- Cite code by symbol, heading, or exact text, never line numbers; state values relative to
  main at the base commit.
- After `clutch review` approves, run one independent adversarial audit per ticket against the
  code (it caught blockers review passed in most tickets): premises, forced files missing from
  the fence, criteria that pass on the wrong result, and collisions with every confirmed,
  unmerged ticket that shares a file or an interface (fake configs that miss a field another
  ticket adds are the usual case), in either merge order.
- Once the engine can author roadmap rows itself (a driver), stop hand-authoring and let it.

Supervising:
- Arm a monitor on merges, holds, the Reject queue, driver digests, and the engine exiting;
  match this checkout's engine process exactly (other hosts run their own).
- On any failure, name the root cause in one sentence from the stem's artifacts before acting,
  classify it as drift or not, and file the class-prevention change with `clutch suggest`.
- A drain with the driver authoring ahead rarely quiesces: for a box message that wastes runs
  or can wedge the engine, `clutch stop` at a ticket boundary, triage, and restart.
- Keep a state file of every action, verdict, and filing, and end each reply with a
  `Still open:` list.

Closing each phase:
- Before a phase ships, review its merged rows taken together against the phase's theme and
  ship gate and the owning plans' target design (`clutch roadmap accept <release>` once it
  exists; until then a read-only agent review). Every partial or unmet promise becomes a P1 row
  in that phase's table (a deferred one goes to the next phase's table), never a suggestion, so
  the gate waits on it. A stuck row (declined or rejected) gets a reworded or replacement row.
```

## 4. Why each change

- **Environment check first.** The run lost time to entry scripts and bytecode still pointing at
  the pre-rename `chupa` path: `./dev.py test` failed in the main checkout and the first release
  gate failed on a traceback-format test.
- **Credentials up front.** Rows needing one provider sat blocked until its credential appeared; it then existed
  only in interactive shells, so engines must start from one.
- **No double bump.** Once the driver merged, its `ship` step tags at gate pass, which is the
  same moment as "before the next phase".
- **Triage is final, cause fixes via suggest.** This is the original request; the run also showed
  triage declines doc-only staleness reliably, so do not re-file it.
- **No human, runs not time.** Corrections 1 and 2.
- **Small, drift-adaptive window.** Correction 3. One ticket drifted when a sibling merge bumped
  a spec it cited by literal version and line numbers.
- **Overlap authoring with draining, atomic edits.** Correction 4. One draining intake committed
  a half-edited ticket mid-edit.
- **Adversarial audit.** It found blocking defects `clutch review` had approved in 6 of 8 audited
  tickets, including a provider key that would have reached every child process.
- **Phase acceptance, gaps as rows.** Corrections 5 and 6. The 0.3.0 review found 13 partial or
  unmet promises behind rows struck as merged (scoped-out halves, unbuilt rows, a driver that
  could not release its own stuck rows); suggestions for them had been declined by triage.
- **Exact process match, `clutch stop` for urgent box items.** A watcher matched its own
  command line; another host's drain shared the bare process name; the driver-ahead drain did
  not quiesce for hours.
