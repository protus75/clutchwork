# merge_conflict_facts capture (parallel plan A0)

Agent capture for `docs/roadmap.md` row 46 (`merge-model-resolve`), taken 2026-11-16 at main `f418b4c6`. It was read-only while a drain was running.

## Answer

**This repo's journal has zero `merge_conflict_facts` events, and no rebase or merge conflict of any kind is recorded anywhere.** That covers the journal, the engine log, all 769 ticket attempt harvests, and main's history (0 merge commits). The plan and roadmap claim "13 `merge_conflict_facts` events exist", but those 13 are `requisition_verdict` signals. Their prose quotes the string `merge_conflict_facts`, written on 2026-10-06/07 while the merge-queue feature that emits the signal was being authored. They do not record conflicts.

No path has ever conflicted, so none is chronic. The §18.2 trigger ("first chronically re-resolved conflict shown by the journaled conflict facts") has not fired.

## Range read

Journal: `.clutch/state/journal/`, 16 segments (`000001-20261005.jsonl` .. `000016-20261115.jsonl`), **30,243 events**, all parseable. The first event is at `2026-10-05T07:10:12.073800+00:00` and the last at `2026-11-16T12:20:59.113639+00:00`. The journal has no events between `2026-10-10T15:20:46` (end of segment 4) and `2026-11-03T15:05:41` (start of segment 5). The drain appended to segment 16 while this capture ran: earlier passes saw 30,211 events, and the final tally pass saw 30,243. No merge, conflict, or merge-stage event was added in between (566 merged before and after).

| Segment | Events | First ts | Last ts |
|---|---|---|---|
| 000001-20261005 | 3892 | 2026-10-05T07:10:12 | 2026-10-07T23:59:21 |
| 000002-20261007 | 4528 | 2026-10-07T23:59:43 | 2026-10-08T23:49:51 |
| 000003-20261009 | 1974 | 2026-10-09T00:00:49 | 2026-10-10T00:00:40 |
| 000004-20261010 | 1040 | 2026-10-10T00:00:53 | 2026-10-10T15:20:46 |
| 000005-20261103 | 556 | 2026-11-03T15:05:41 | 2026-11-04T15:04:21 |
| 000006-20261104 | 881 | 2026-11-04T15:06:11 | 2026-11-05T14:40:25 |
| 000007-20261105 | 1536 | 2026-11-05T15:12:49 | 2026-11-06T15:10:56 |
| 000008-20261106 | 2851 | 2026-11-06T15:30:07 | 2026-11-07T15:29:55 |
| 000009-20261107 | 729 | 2026-11-07T15:30:20 | 2026-11-08T15:29:39 |
| 000010-20261108 | 4098 | 2026-11-08T15:31:40 | 2026-11-09T15:31:39 |
| 000011-20261109 | 1180 | 2026-11-09T15:33:09 | 2026-11-10T08:09:54 |
| 000012-20261111 | 2109 | 2026-11-11T00:50:17 | 2026-11-12T00:04:42 |
| 000013-20261112 | 463 | 2026-11-12T04:00:38 | 2026-11-12T22:54:39 |
| 000014-20261113 | 1224 | 2026-11-13T07:13:19 | 2026-11-14T03:46:08 |
| 000015-20261114 | 1041 | 2026-11-14T12:37:10 | 2026-11-15T12:13:56 |
| 000016-20261115 | 2141 | 2026-11-15T17:45:21 | 2026-11-16T12:20:59 |

Engine log: `.clutch/state/engine.log`, 13,198 lines, from 2026-10-05T07:07:26 to 2026-11-16T12:17:23. It records `engine_start` lines from 2026-11-06T19:23 and merge-surface stage lines from 2026-11-07T06:21.

## Method

Every read used `python3 -I` scripts, one JSON object per line.

1. Journal: counted events whose `body.kind` or `body.signal` equals `merge_conflict_facts`, which is what `MergeQueue._facts` (`clutch/mergequeue.py`) writes. Separately counted every line that contains the literal string, and grouped the hits by event type and signal.
2. Journal: searched each line for `conflict` (case-insensitive), `CONFLICT (`, `Merge conflict in`, `could not apply`, `rebase onto main refused` (the inline refusal message), `post_rebase_regate`, `ConflictHandoff`, `conflicted_paths`, and `rebase`. Grouped the hits by event type, signal, and key prefix.
3. Journal: listed every `state_transition` with `to: gate_failed` and `stage: merge`, every merge-stage transition, every `rework_order` signal, and every `merge-regate/*` effect completion (serve-queue admission receipts). Counted `merged` transitions. For each merge, checked whether another stem merged between that ticket's last `running` transition and its own `merged` transition, which measures whether main moved under a run.
4. Engine log: searched for `conflict`, tallied the `surface: merge` stage outcomes and `gate_failed` codes, and tallied `engine_start` by `verb`.
5. Tickets: read every `tickets/*/attempts/*/harvest.json` (769 files) and printed the findings for each one with `stage: merge`. Grepped `tickets/` and `.clutch/state/{spools,rework,box,drain.out}` for the git conflict strings above, and read the context of each hit.
6. Git (read-only): `git log --merges main` and `git log -i --grep=conflict main`. Ran a scratch-repo probe of `git rebase` to see which stream carries `CONFLICT (...)` lines (git 2.43.0).

## Findings

### 1. `merge_conflict_facts`: 0 events

There are 16 journal lines that contain the literal string. 13 are `requisition_verdict` signals and 3 are `llm/*` effect completions (model output that discusses the code). The 13 below are the "13 events" the plan cites:

| ts | ticket | verdict |
|---|---|---|
| 2026-10-06T21:04:46 | merge-queue | snag |
| 2026-10-06T23:45:27 | merge-queue | approve |
| 2026-10-07T02:09:08 | phase3-continue-06 | snag |
| 2026-10-07T02:48:19 | merge-queue-activation | snag |
| 2026-10-07T03:06:28 | merge-queue-activation | approve |
| 2026-10-07T14:36:35 | phase3-continue-08 | approve |
| 2026-10-07T15:19:11 | phase3-continue-09 | snag |
| 2026-10-07T15:35:30 | phase3-continue-09 | approve |
| 2026-10-07T16:27:52 | admission-holds-activation | snag |
| 2026-10-07T16:45:42 | admission-holds-activation | snag |
| 2026-10-07T17:09:43 | admission-holds-activation | snag |
| 2026-10-07T17:40:14 | admission-holds-activation | snag |
| 2026-10-07T17:59:31 | admission-holds-activation | approve |

All 13 are in segment `000001-20261005.jsonl` (lines 1719-3108).

### 2. Why there are none: the serve merge queue has never admitted a ticket here

- Only `MergeQueue._admit` with `conflict_facts=True` (serve) writes the signal. Since `merge-queue` (`4423bf04`, 2026-10-06), `_admit` has called `_facts` on every path after the rebase, success or refusal. So zero facts means no serve admission ever reached that point.
- The journal has 0 `merge-regate/*` effect completions. Serve writes that admission receipt, so no serve admission has finished.
- All 296 `engine_start` lines in the engine log (from 2026-11-06T19:23) have `verb: drain`. None is from `serve` or `run`.
- Inline merge (`merge.merge`, used by `drain` and `run`) passes `conflict_facts=False` and `conflict_ladder=False`. Before today's `merge-admission-single-owner` (`b43025e4`) it was a separate copy with no facts call. A drain-mode conflict is therefore never written as `merge_conflict_facts`. It would appear only as `gate_failed` with reason `post_rebase_regate` and a finding message that starts `rebase onto main refused:`.

### 3. No conflict under drain either: 566 merges, 0 conflict refusals

- The journal has 566 `merged` transitions, for 566 unique stems, and 566 unique `merge/*` effect keys.
- 0 transitions have reason `post_rebase_regate`, and 0 lines contain `rebase onto main refused`, `CONFLICT (`, `Merge conflict in`, or `could not apply`.
- **Main never moved under a run through an engine merge:** for 0 of 566 merges did another stem merge between the ticket's last `running` and its `merged`. Drain is single-flight, so a ticket branch only rebases over ticket-plane commits (the `tickets/` tree is restored from the branch before the rebase) or over operator commits on main. None of those rebases conflicted.
- Main has 5,712 commits and 0 merge commits, because every engine merge is a squash.

### 4. Merge-stage `gate_failed`: 10, none caused by a conflict

The journal has 10 merge-stage failures (review 111, check 74), and they match the 10 merge-stage harvests one for one. The engine log shows 232 merge-surface `stage_end` lines since 2026-11-07, 230 `ok` and 2 `gate_failed`.

| ts | stem | attempt | reason | routed | paths / cause | outcome |
|---|---|---|---|---|---|---|
| 2026-10-06T13:06 | phase2-exit | 1 | requisition_review | retry | `## Context` path `tests/test_seeded_phase3_core.py` missing | merged 2026-10-06T13:33 |
| 2026-10-06T20:32 | phase3-core | 10 | requisition_review | reject_queue | same missing Context path | merged 2026-10-06T20:45 |
| 2026-11-05T23:39 | serve-self-upgrade | 2 | verification | retry | `uv run pytest -q` failed in `clutch/serve.py` watcher | merged 2026-11-06T09:10 |
| 2026-11-06T19:48 | order-verb | 2 | dirty_checkout | reject_queue | main checkout had local edits to `docs/how-clutch-works.md`, `vscode-clutchwork/extension.js`, `vscode-clutchwork/package.json` | merged 2026-11-06T20:51 |
| 2026-11-06T19:58 | order-verb | 3 | dirty_checkout | reject_queue | same three paths | (same) |
| 2026-11-07T04:47 | requisition-coverage-dependents | 1 | dirty_checkout | reject_queue | `clutch/specs/requisition_review.md`, `tests/test_specs.py` | merged 2026-11-07T06:21 |
| 2026-11-07T04:55 | requisition-coverage-dependents | 2 | dirty_checkout | reject_queue | same two paths | (same) |
| 2026-11-07T05:00 | requisition-coverage-dependents | 3 | dirty_checkout | reject_queue | same two paths | (same) |
| 2026-11-07T06:56 | box-view | 4 | dirty_checkout | reject_queue | `clutch/observe.py`, `tests/test_watch.py`, `vscode-clutchwork/extension.js`, `vscode-clutchwork/package.json` | merged 2026-11-07T07:02 |
| 2026-11-10T04:23 | pypi-readme-user-guide | 0 | integration | retry | integration suite red (`PydanticSerializationUnexpectedValue`) | merged 2026-11-10T04:37 |

### 5. Nearest analogue: `dirty_checkout` (6 refusals, 3 stems)

Two writers touching the same file has happened only between a ticket's squash and uncommitted edits in the operator's main checkout. Git never conflicted between two ticket branches. The overlapping paths, counted per refusal: `vscode-clutchwork/extension.js` 3, `vscode-clutchwork/package.json` 3, `clutch/specs/requisition_review.md` 3, `tests/test_specs.py` 3, `docs/how-clutch-works.md` 2, `clutch/observe.py` 1, `tests/test_watch.py` 1. Each was routed to the Reject queue, and each stem merged once the overlap cleared, 6 to 94 minutes after its first refusal. These paths overlap the plan's fence hot list (`docs/how-clutch-works.md`, `tests/unit/test_specs.py`, `test_watch.py`).

### 6. Semantic sibling conflict (not a git conflict)

Commit `287bbb54` (`requisition-review-sibling-tickets`, 2026-11-16) records one case: two confirmed, unmerged tickets (one of them `release-publish`) would each have broken the other's Verification in a file outside its fence. A manual audit caught it, and requisition review now sees sibling tickets. This is the plan's "two changes that each pass but break together" risk. It is the only recorded instance, and no run reached a conflict over it.

### 7. Hits that are not conflict records

- Every `CONFLICT (` hit in `.clutch/state/spools/` is test-fixture text quoted in prompts or provider event streams, for example `git((1, "", "CONFLICT (content)\n"), ...)` in `test_refused_rebase_is_aborted_before_refusal_returns`.
- `conflicted_paths`, `resolving_rung`, and `ConflictHandoff` appear only in ticket prose, retro documents (`tickets/retro/000035-000049.md`), implement-stage harvests that quote source, and requisition and review prompts.
- The journal has 5 `rework_order` signals: `chupa-ruff-config` split, `split-test-serve` split, `menu-mirrors-verb-admission` split, `fs-seam-mkdir-remove` update, and `merge-admission-single-owner` update. None came from a conflict handoff, because `consume_handoff` is reached only from the serve queue.
- The engine log has 3 `conflict` lines: two Author lint codes (`criteria_conflict` and `unit_test_disk_conflict`), plus one `roadmap_drive` line that names this row.

## What the design can rest on

1. **There is no empirical base for the step-2 bounds.** No conflict has been observed, so the limits of 3 files and 60 marker lines, the text-only rule, and the safety-inventory exclusion are design choices, not calibrated values. The §18.2 trigger has not fired. The departure from the design record rests only on the owner's 2026-11-13 parallel decision, not on observed conflicts.
2. **Conflicts appear only when main moves under a run, and in this repo it never has.** That held across 566 merges, because drain is single-flight and serve has never admitted a ticket here. Real conflict data begins when serve runs with `scheduler.parallel.enabled`, or when serve runs while main moves. The first `model` and `rerun` facts will be the first data points.
3. **Expected hot paths come from fences, not conflicts.** The only evidence of observed overlap is the `dirty_checkout` list above, and it agrees with the plan's fence counts: `docs/how-clutch-works.md`, `vscode-clutchwork/extension.js` and `vscode-clutchwork/package.json`, `tests/test_specs.py` (now `tests/unit/test_specs.py`), and `tests/test_watch.py`. `docs/how-clutch-works.md` is the plan's intended `shared_paths` entry. `vscode-clutchwork/package.json` and `extension.js` are not in the plan's lists.
4. **Measurement gap:** plan §8 says "`merge_conflict_facts` already records each conflict". That is true only for serve. Inline merge (`drain`, `run`, and the extension's default play action) sets `conflict_facts=False`. Its refusal message also keeps only git's stderr (`exc.err`). The scratch-repo probe showed that git prints `Auto-merging <path>` and `CONFLICT (content): Merge conflict in <path>` on **stdout**, and only `error: could not apply <sha>... <subject>` and hints on stderr. A drain-mode conflict would therefore leave no record of which paths conflicted.
5. **Stale claims to correct:** "13 events exist; nobody has read them" appears in `docs/roadmap.md` §3.3 and in the row 46 Agent tasks bullet ("reads the 13 `merge_conflict_facts` events"). "13 `merge_conflict_facts` events exist in this repo's journal" appears in `docs/parallel-tickets-plan.md` (Departures table, and ticket 7 row "read the 13 `merge_conflict_facts` events"). All of these are false: the count is 0, and the 13 are `requisition_verdict` text matches.
