---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- docs/how-clutch-works.md
- README.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- clutch/docs/host-authoring.md
- clutch/__main__.py::_parser
- clutch/stages.py::_lift_decision
- clutch/reconcile.py::orphans
- clutch/journal.py::SIGNAL_NAMES
- clutch/journal.py::_NOT_EMITTED
- clutch/thresh.py::Thresh._select
- clutch/scorecard.py::project_scorecard
- clutch/enginelog.py

## Goal / Why
The maintained documents say things the code does not do. `docs/how-clutch-works.md` says its own rule: "Where this document and the code disagree, the code wins and this document is fixed." The roadmap audit (`docs/roadmap.md` sections 3.4, 4.1 and 4.2, row 4 of section 8) lists the disagreements. Each one below was re-checked against the code on main on 2026-11-15, and rows that a merged ticket already fixed or that another roadmap ticket owns are left out (see Scope out). Every ticket authored after this one cites these documents, so a wrong sentence here becomes a wrong criterion later. Roadmap release 0.2.0 needs this ticket merged before it can ship, so that the next audit starts clean.

After this change every sentence listed in Scope in states what the code does, and no code changes.

## Scope in / Scope out
Scope in. Each item names the section, the false claim, and the code that owns the truth. Change only the sentence or table row named; keep every heading's text exactly as it is, except the two `host-contract.md` retitles below, because `clutch/help.py` and the `vscode-clutchwork/package.json` setting descriptions link to these headings and `tests/integration/test_help.py` resolves the links.

`docs/how-clutch-works.md`:
1. Section 2.1, `probe` row: add that it exits 1 when any probe fails and 2 for a provider name that is not declared (`clutch/__main__.py::main`, the `probe` branch). The row must contain the words `exits 1 when any probe fails`.
2. Section 2.1, `drain` row: add `--parked STEM` and `--deadline ISO`, and say the self-upgrade re-exec sets them, not the operator (`clutch/__main__.py::_parser`). Leave `--stop-lifecycle` undocumented; its help is suppressed.
3. Section 2.1, `reject` row: the signature becomes `reject <stem> [--yes|--extension]`, and the text says `--yes` or `--extension` skips the prompt (`clutch/__main__.py::_verdict`).
4. Section 2.2, the extension paragraphs: add one sentence naming `clutch.command`, the command and arguments the extension runs the engine with (default `.venv/bin/clutch`, resolved from the workspace folder; `vscode-clutchwork/package.json`).
5. Section 3.1, the `state` bullet: replace `` `draft` (awaits `confirm`) `` with wording saying a `draft` is an Author-written ticket awaiting `confirm`, and that intake stamps a new hand-written ticket `confirmed` (`clutch/tickets.py` line 695, the intake stamp).
6. Section 3.3: the lift skips symlinks without error (`clutch/stages.py::_lift_decision` returns `"skip"` for a symlink); it still refuses a file over 256 KB. The words `refuses symlinks` leave the section, and no wording says the size limit is the lift's only refusal (`clutch/stages.py::lift_outbox` also refuses an invalid registered report through `_validate_reports`).
7. Section 3.3 lift table: add a `harvest-rework` row, `attempts/<n>/harvest.json` written when Rework itself failed (`clutch/runner.py::drive`, the `kind="harvest-rework"` call).
8. Section 3.3, "Other engine commits on `main`": add `clutch(decisions): <id>` (a triage decision record, `clutch/author.py`), `clutch: retro NNNNNN` (`clutch/retro.py::Retro.commit_report`) and `clutch(<stem>): undo refused rework` (`clutch/daemon.py::apply_rework`). Also say that Check's `clutch(<stem>): autofix` commit lands on the ticket branch, not on `main` (`clutch/stages.py::check_autofix`).
9. Section 4.3, step 1: autofix runs only when Implement replied `ok` and `review.autofix` is nonempty (`clutch/stages.py::check`). The step must name `` `review.autofix` ``.
10. Section 6.3, last paragraph: when the worktree is gone, no `diagnosis.json` is written or lifted, and only the journaled `diagnosis` signal records the mechanical verdict (`clutch/runner.py::drive`, the `# A lost workspace has no outbox` branch). The section must contain the words `` no `diagnosis.json` is written ``.
11. Section 6.7, **Reconcile** bullet: two stems are not reaped. One is a stem whose merge-queue receipt for its current attempt is `HELD`. The other is a stem whose only unfinished effects are a standalone review's `llm/review-<stem>/` calls (`clutch/reconcile.py::orphans`). The bullet must contain `HELD` and `llm/review-`.
12. Section 7.1, step 2: between tickets the drain also ingests host bug reports into the Suggestion Box (`clutch/drain.py::_Drain.run` calls `triage.report_intake` every loop; section 9.4 owns the details). The step must contain the words `bug report`.
13. Section 7.2.1, first paragraph: the skip rule also requires that the attempt has no `HELD` receipt (`clutch/mergequeue.py::MergeQueue._admit`, `skip = unchanged and bool(evidence.changed_files) and not receipts`).
14. Section 8.1, the **Preflight** bullet: preflight also runs at the start of `review`, and at the start of a standalone `retro` that has a merge to report (`clutch/__main__.py::_review` and `clutch/__main__.py::_retro`). The bullet must name `` `review` `` and `` `retro` ``.
15. Section 8.3: the spill is decided before waiting. When the first candidate has no free slot and the projected wait for it is over 60 seconds, the call goes to the next candidate with a free slot (`clutch/thresh.py::Thresh._select`, `SPILL_WAIT_SECONDS`). The words `over 60s spills` leave the section and the word `projected` appears. The quota sentence gains `(default 60)` after `limits.quota_window_minutes` (`clutch/config.py::Limits`).
16. Section 9.6, scorecard bullet: a prune candidate has 25+ evaluations, no catch and no escape (`clutch/scorecard.py::project_scorecard`, `catches == escaped == 0`). The bullet must contain the words `no catch and no escape`.
17. Section 10.1 table: add rows or row text for `drain.out` (output appended by `drain --detach`), `coverage-map.json` (written by `covmap`, read by requisition review), `rework/<stem>/<attempt>/<call>/` (the scratch worktree where Rework validates a proposal, `clutch/rework.py`), `spools/probe/` (captures from `probe`), and `box.seq/` (Suggestion Box id reservations, `clutch/box.py::Box._enqueue`). Extend the `worktrees/` row with `.base/` and `.regression-base/`, the scratch merge-base worktrees for base-red reruns and the bug gate. State the bounds too. `engine.log` rotates at 16 MiB and keeps 3 backups (`clutch/enginelog.py`). A journal segment rolls at 64 MiB or 24 hours (`clutch/journal.py`, `ROLL_BYTES` and `ROLL_AGE`). The table must contain `16 MiB` and `64 MiB`.
18. Section 10.2, the event-type sentence. Add `checkpoint`, a reserved type that readers accept and `Journal.append` refuses (`clutch/journal.py::_NOT_EMITTED`). Then say what the closed list of signals is: a `signal` body names exactly one member of `SIGNAL_NAMES` in `clutch/journal.py`, under the key `signal` or `kind`, and append refuses any other name. Cite the registry by name only. Do not copy its members into the document: a copied list would be a second home for a closed set.
19. Section 11, config table. In the `providers` row, say that every `kind: cli` provider requires `package`, the pnpm package the preflight reads (`clutch/config.py::Provider`). Also add `(default `medium`)` after `routing_default_tier` (`clutch/config.py::Config`).

`README.md`, "The working loop" step 6: drop "Runs that exhaust attempt caps" from the list of things that file to the Suggestion Box. A run that exhausts its caps goes to the Reject queue and waits for `confirm` or `reject` (`clutch/runner.py`, `terminal["routed"] = "reject_queue"`). The step must say `Reject queue`.

`clutch/docs/host-running.md`, `retro` row: drop "(serve accepts it but does not yet run it)". The running engine runs a queued retro at its next idle point (`clutch/serve.py::Serve.run_retro`). Keep the row's leading `| `retro` |` cell. `clutch/help.py` reads this row's text for the `verb.retro` help entry, and `tests/integration/test_help.py::test_verb_what_from_run_guide` compares the two at test time, so no help or test file changes.

`clutch/docs/host-contract.md` (roadmap section 3.4 and the section 4.2 rows):
- Opening paragraph: delete the sentence "Report intake and cutover below are pending Phase 6 consumer contracts, not an activation instruction." Keep "Foreign process-state adoption is excluded." because `tests/integration/test_host_contract.py` requires it.
- Retitle `## Pending report-inbox contract` to `## Report-inbox contract` and `## Pending cutover contract` to `## Cutover contract`. The bodies stay. Nothing links to the old anchors: no `#pending-report-inbox-contract` or `#pending-cutover-contract` appears in `clutch/help.py`, `vscode-clutchwork/package.json` or `docs/`. `clutch/triage.py::report_intake` and `clutch/inbox.py` ship the report consumer, and serve, drain and triage run it.
- Delete the last line, "This document adds no report consumer, GO writer or runtime activation."
- In the `host-example` block, the `trigger_map` comment becomes `# accepted and read by nothing`. Keep the value `{src/: [scope_fence]}` and keep a comment on that line, because `tests/integration/test_host_contract.py::test_host_contract_example_loads` asserts both. In the prose under "Checks and injectable seams", replace "Host surfaces use their own triggers; trigger_map concerns engine gates." with a sentence saying `review.trigger_map` is accepted and read by nothing (`clutch/config.py::Review` declares it, and no module reads it).
- Ticket fields paragraph: replace "Put ordering in Depends on and priority, not extra metadata." with wording that says `Depends on` names only tickets whose merged code this ticket needs, and other ordering goes in priority and `## Runs before`, not extra metadata (`clutch/docs/host-authoring.md`, "What each section is for").

`clutch/docs/host-authoring.md`, Workflow step 2: the sentence listing what lint applies also names the `drain.max_ticket_minutes` stuck ceiling. Lint reports a `stuck` over that ceiling as a finding and exits 1 (`clutch/__main__.py::stuck_ceiling_finding`, `clutch/__main__.py::_lint`).

Scope out:
- All code, including the docstrings, argparse help and the `retro_check` outcome vocabulary. Those belong to `docs-truth-sweep-code-strings`.
- `docs/how-clutch-works.md` section 2.2's claim that unit tests run under `clutch.testguard`. `dev-surface-completeness` makes `./dev.py test` load the plugin, which makes the sentence true, so it is not rewritten here.
- The drain report's `uv run python -m clutch` paved roads, and the `clutch confirm` and `clutch reject` wording in sections 6.7 and 7.1. That code fix is `paved-roads-name-verbs`.
- `clutch/redact.py`'s checklist and harvest redaction (`redaction-harvest-seam`).
- The `CORE_TEMPLATE` parenthetical and `CLAUDE.md`/`AGENTS.md` parity (`conduct-files-parity`).
- `watch` tier display (`watch-surface-tier-truth`).
- `clutch/docs/host-qwen.md` and `clutch/specs/ask/*.md`. They no longer name `./dev.py`; `dev-py-dev-tasks-only` fixed that.
- The `served_review` exception swallow. No maintained document describes it, and the code fix is `merge-admission-single-owner`'s.
- Removing the rule restatements listed in roadmap section 2.5.
- The new "Onboarding a host" and "Operating facts" sections of `host-contract.md` (`host-onboarding-doc`).
- `docs/roadmap.md` and `CLUTCH_PLAN.md`.

## Scope fence
- docs/how-clutch-works.md
- README.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- clutch/docs/host-authoring.md

## Acceptance criteria
1. The first `## Verification` command exits 0. It checks the sections 2 to 4 items of `docs/how-clutch-works.md`: the `reject`, `drain` and `probe` rows; `clutch.command` in section 2.2; `` `draft` (awaits `confirm`) `` gone; and, in section 3.3, `refuses symlinks` gone with `harvest-rework`, `clutch(decisions)`, `clutch: retro` and `undo refused rework` present; plus `` `review.autofix` `` in section 4.3. Ruled out: today's text, on which every one of those checks fails.
2. The second `## Verification` command exits 0. It checks the sections 6 to 9 items of `docs/how-clutch-works.md`: `` no `diagnosis.json` is written `` in 6.3; `HELD` and `llm/review-` in 6.7; `bug report` in 7.1; `HELD` in 7.2.1; `` `review` `` and `` `retro` `` on the Preflight line; in 8.3, `over 60s spills` gone with `projected` and `(default 60)` present; `no catch and no escape` in 9.6. Ruled out: today's text, on which each check fails.
3. The third `## Verification` command exits 0. In section 10.1 of `docs/how-clutch-works.md` it finds `drain.out`, `coverage-map.json`, `rework/`, `spools/probe/`, `box.seq/`, `.base/`, `.regression-base/`, `16 MiB` and `64 MiB`. In 10.2 it finds `` `checkpoint` `` and `SIGNAL_NAMES`. In 11 it finds `package` and ``default `medium` ``. It also asserts that section 10.2 names at most two members of `clutch.journal.SIGNAL_NAMES` in backticks, so the list is cited, not pasted. Ruled out: today's text, and a 10.2 that pastes the signal list.
4. The fourth `## Verification` command exits 0. It checks the four guides: `README.md` no longer contains `Runs that exhaust attempt caps` and does contain `Reject queue`. `clutch/docs/host-running.md` no longer contains `does not yet run it`. `clutch/docs/host-contract.md` contains `## Report-inbox contract` and `## Cutover contract` and `## Runs before`, and no longer contains `Pending `, `pending Phase 6`, `adds no report consumer`, `engine gate codes only`, `concerns engine gates` or `Put ordering in Depends on and priority`. `clutch/docs/host-authoring.md` contains `drain.max_ticket_minutes`. Ruled out: today's text, on which each check fails.
5. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_host_contract.py tests/unit/test_readme.py tests/unit/test_host_running.py tests/unit/test_host_authoring.py tests/integration/test_author.py` exits 0. These are the tests that read the edited documents: help links still resolve to unchanged headings, the `host-example` block still loads with its `trigger_map` value and comment, every phrase `test_host_contract.py` mentions survives, and the Author prompt still embeds the guide byte for byte. Ruled out: a renamed heading, a dropped `trigger_map` comment, or a deleted pinned phrase.
6. `./dev.py test` exits 0.

## Verification
```
uv run python -c "import pathlib; t = pathlib.Path('docs/how-clutch-works.md').read_text(); sec = lambda a, b: t.split(a, 1)[1].split(b, 1)[0]; row = lambda v: next(l for l in t.splitlines() if l.startswith('| `' + v)); assert '--extension' in row('reject '); assert '--parked' in row('drain ') and '--deadline' in row('drain '); assert 'exits 1 when any probe fails' in row('probe '); assert 'clutch.command' in sec('### 2.2 ', '## 3. '); assert '`draft` (awaits `confirm`)' not in t; s = sec('### 3.3 ', '## 4. '); assert 'refuses symlinks' not in s; assert all(p in s for p in ('harvest-rework', 'clutch(decisions)', 'clutch: retro', 'undo refused rework')); assert '`review.autofix`' in sec('### 4.3 ', '### 4.4 ')"
uv run python -c "import pathlib; t = pathlib.Path('docs/how-clutch-works.md').read_text(); sec = lambda a, b: t.split(a, 1)[1].split(b, 1)[0]; assert 'no `diagnosis.json` is written' in sec('### 6.3 ', '### 6.4 '); s = sec('### 6.7 ', '## 7. '); assert 'HELD' in s and 'llm/review-' in s; assert 'bug report' in sec('### 7.1 ', '### 7.2 '); assert 'HELD' in sec('#### 7.2.1 ', '### 7.3 '); p = next(l for l in t.splitlines() if '**Preflight**' in l); assert '`review`' in p and '`retro`' in p; s = sec('### 8.3 ', '### 8.4 '); assert 'over 60s spills' not in s and 'projected' in s and '(default 60)' in s; assert 'no catch and no escape' in sec('### 9.6 ', '## 10. ')"
uv run python -c "import pathlib; from clutch.journal import SIGNAL_NAMES; t = pathlib.Path('docs/how-clutch-works.md').read_text(); sec = lambda a, b: t.split(a, 1)[1].split(b, 1)[0]; s = sec('### 10.1 ', '### 10.2 '); assert all(p in s for p in ('drain.out', 'coverage-map.json', 'rework/', 'spools/probe/', 'box.seq/', '.base/', '.regression-base/', '16 MiB', '64 MiB')); s = sec('### 10.2 ', '### 10.3 '); assert '`checkpoint`' in s and 'SIGNAL_NAMES' in s; assert len([n for n in SIGNAL_NAMES if '`' + n + '`' in s]) <= 2; s = sec('## 11. ', '## 12. '); assert 'package' in s and 'default `medium`' in s"
uv run python -c "import pathlib; r = pathlib.Path('README.md').read_text(); assert 'Runs that exhaust attempt caps' not in r and 'Reject queue' in r; g = pathlib.Path('clutch/docs/host-running.md').read_text(); assert 'does not yet run it' not in g; c = pathlib.Path('clutch/docs/host-contract.md').read_text(); assert all(p in c for p in ('## Report-inbox contract', '## Cutover contract', '## Runs before')); assert not any(p in c for p in ('Pending ', 'pending Phase 6', 'adds no report consumer', 'engine gate codes only', 'concerns engine gates', 'Put ordering in Depends on and priority')); a = pathlib.Path('clutch/docs/host-authoring.md').read_text(); assert 'drain.max_ticket_minutes' in a"
./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_host_contract.py tests/unit/test_readme.py tests/unit/test_host_running.py tests/unit/test_host_authoring.py tests/integration/test_author.py
./dev.py test
```

## Definition of rejected
The branch is rejected if it:
- changes any file outside the fence, or any code, docstring or test;
- renames or renumbers a heading in any of the five documents, other than the two `host-contract.md` retitles Scope in names;
- copies the members of `SIGNAL_NAMES`, or any other closed set, into a document instead of citing its owner;
- rewrites a sentence that Scope in does not name, including the `clutch.testguard` sentence in section 2.2 and the `clutch confirm` and `clutch reject` paved roads in sections 6.7 and 7.1;
- states a behavior that the cited code does not have;
- removes a phrase that `tests/integration/test_host_contract.py` or `tests/unit/test_host_authoring.py` requires;
- adds the "Onboarding a host" or "Operating facts" sections.

## Time budget
- expected: 60m
- stuck: 120m
