<!-- Evidence copy for ticket plan-drain-prompts (2026-11-16). The session's hand-authoring brief for one roadmap row. Machine paths, another host, credential names, and shell-specific launch commands are replaced with placeholders or generic wording; nothing else changed. -->

# Brief for agents authoring clutch tickets in the roadmap run

You author one clutch ticket (or a split of one row into at most 3) in the main checkout at
<checkout>. Run every clutch command as `uv run clutch <verb>` from there.

## Facts

- Roadmap: `docs/roadmap.md` (section 8 is the master ticket table). Its audit sections 2-4 were
  written at 80b76d5d on 2026-11-13 and are stale; never trust a roadmap line number or claim
  without reading the code at HEAD. Cite code as `path.py::Name`, not line numbers.
- Plan digests with fence gaps, stale facts, and roadmap conflicts per plan:
  `<session plan digest>` (read the entry for your row's plan).
- Version 0.3.0 (tag v0.3.0) started roadmap phase "0.2.0". Merged from that phase so far:
  release-verb (`clutch release --minor|--patch` exists), docs-truth-sweep,
  docs-truth-sweep-code-strings, conduct-files-parity, contention-authoring-rules (its rules are
  now in CLAUDE.md/AGENTS.md: new tests in new files, new fixtures in new modules, fence only what
  is forced, do-not-grow list), unit-criteria-disk-snag, fence-closure-registries,
  watch-surface-tier-truth, redaction-harvest-seam, dev-surface-completeness,
  paved-roads-name-verbs. Row 88 `superseded-settles` was skipped: its premise is false
  (`clutch/runner.py::failure_terminal` already retires a split parent without routing it to the
  Reject queue). Nothing depends on it.
- The PyPI distribution is `clutchwork` (the command is `clutch`): install commands and extras
  are `clutchwork`, `clutchwork[images]`, `clutchwork[images-embed]`, never `clutch[...]` as some
  plans write (e.g. `docs/gemini-graphics-refactor-plan.md` around line 226). A graphics ticket
  fixes that plan line when it fences the plan.
- Owner decisions of 2026-11-16 that override the plans:
  1. No human in the loop. No `gate: operator`; every gate is a command. Hand tests are agent-run
     captures committed as ticket evidence. Calibration and GO baselines use an AI label panel of
     a different model family than the judge, never hand labels.
  2. Gates and cadences count runs, never wall-clock time ("the next 10 merged tickets", "after
     every settle"), never "a week" or "daily".
  3. Plan open decisions take the plan's "Proposed" option unless this brief says otherwise.
  4. Cause fixes are never authored: file them with `uv run clutch suggest "<summary>"`.
  5. Publishing (PyPI, Marketplace) stays behind `release.publish` (default false); nothing pushes.

## Limits

Other agents author other tickets in this checkout at the same time, and `clutch triage` may be
running (it holds the writer lock and commits drafts). Write ONLY under `tickets/<your stems>/`
and scratch files under
`<scratch>/<stem>/`.
Never edit code, docs, specs, config, CLAUDE.md, AGENTS.md, or another ticket. Never run git
add/commit/reset/checkout/stash/clean, or clutch drain, run, serve, confirm, reject, triage,
dismiss, stop, kill. `uv run clutch review <stem>` commits your ticket through intake; that is the
only commit you cause. Second problems you notice go to `uv run clutch suggest`, never into the
ticket. If `clutch review` fails with a provider error, drought, or rate limit (not a verdict),
wait about two minutes (`timeout 120 tail -f /dev/null`) and retry, up to 3 times.

A drain usually runs while you author, and its intake commits any edited ticket.md it sees. So
edit a copy under your scratch dir and replace `tickets/<stem>/ticket.md` with it in ONE write
(`cp`), never by a series of in-place edits; and before each write, if your stem's
`## Depends on` stems are all merged, run `uv run clutch status` and stop if it is in flight.

## Procedure

1. Read the row's owning design and every code and doc location it cites, at HEAD. Grep
   `git log --oneline` and `tickets/` for merged work that already covers part of the row. Fully
   satisfied: create nothing, return "skipped" with concrete evidence. Partly: author only the rest
   and list what you dropped and why.
2. `uv run clutch new <stem> --kind <kind>`. For a bug, first save real observed evidence (output
   you just captured) to your scratch dir and pass `--evidence <file>`. Read
   `clutch/docs/host-authoring.md` IN FULL, then the skeleton, then one recent approved ticket for
   shape (e.g. `tickets/paved-roads-name-verbs/ticket.md`).
3. Fill every section per the guide, plus:
   - The smallest change that satisfies the row; nothing it does not ask for.
   - New tests in NEW test files; new fixtures in new modules; fence only what the change forces.
   - Verification uses `./dev.py test [pytest args]`, never raw pytest.
   - Fence closure: grep `tests/`, `docs/`, `clutch/`, `vscode-clutchwork/` for every name, value,
     verb, path, state, or set member the ticket adds or changes, including in-code registries and
     closed sets (argparse choices, `clutch/help.py` entries, snapshot vocabularies, parity tests,
     the verb tables in `clutch/docs/host-running.md` and `docs/how-clutch-works.md`, config field
     inventories in `clutch/docs/host-contract.md`), and fence every hit that asserts against it or
     must change. Fence documents describing changed behavior and say in Scope in which part to
     update. A bumped prompt spec states "the next minor above its value on main at the base
     commit" and fences its version-pin test.
   - Priority, Depends on (merged code only), and Runs before exactly as your assignment says;
     omit a Runs before stem that has no `tickets/<stem>/` directory yet.
   - Realistic Time budget; `stuck` at most 180 minutes. If the row cannot fit, split into at most
     3 tickets, keeping the row's stem as one of them.
4. `uv run clutch lint <stem>` until it exits 0.
5. The guide's pre-review checks: no criterion contradicts merged behavior or a test outside the
   fence; all criteria can hold together; every invariant has a criterion whose test fails if it
   is dropped.
6. `uv run clutch review <stem>`; repair every finding, re-lint, re-review until it prints
   approve. After 6 rounds without approve, stop and report the last findings verbatim.

## Report

Return: status (approved, skipped, review_stuck, failed); per ticket its stem, kind, priority,
review rounds, final fence, Depends on, Runs before, expected and stuck minutes; what you dropped
from the row and why; suggestions you filed (ids); anything the orchestrator must know.
