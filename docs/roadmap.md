# clutch roadmap

The one place that orders clutch's planned work. Each plan under `docs/` owns its own design; this document owns what the plans share: priority, release slot, cross-plan ordering, shared budgets, and the decisions that settle where plans overlap or contradict. It also carries the audit of the code and documents that the ordering rests on: what is duplicated, what is missing, and where the documents have drifted from the code.

A plan change that moves a ticket, adds a dependency on another plan, or spends a shared budget updates this document in the same change. A ticket authored from a row here is linked by stem in that row.

## Status

Written 2026-11-13 at commit `80b76d5d` (clutch `0.1.5`, extension `0.0.40`, no git tags). The audit sections are a snapshot at that commit, produced by six read-only passes over `clutch/`, `tests/`, `dev.py`, `docs/`, `clutch/docs/`, `clutch/specs/`, `CLAUDE.md`, `AGENTS.md`, `README.md`, and `CLUTCH_PLAN.md` §18-19. Re-run the audit before each minor release; the section headings are the checklist.

Facts the ordering rests on:

- 506 tickets merged, 0 in flight, 0 confirmed and unrun. The queue is empty. One stem awaits a verdict in the Reject queue (`vscode-help`, `premise_failed`). Four stems are blocked in the journal with no ticket directory (`authoring-reading-specs`, `host-mechanical-check`, `phase7-continue`, `journal-sql-refactor-plan`).
- Four Suggestion Box messages are pending: `box-000324` (fence closure misses in-code registries; recurrence recorded in `tickets/retro/000046.md`), `box-000440` (operator prompts hard-code `./dev.py`), `box-000441` and `box-000442` (unit-test criteria that need disk pass requisition review, then fail Implement). None is a ticket yet.
- Spend to date $2,681.50. 5,090 commits since 2026-10-01.
- `CLUTCH_PLAN.md` phases P3-P6 are complete. P7 `host-review-surfaces` was refused instead of built (`config.py:308-309`). P8 `rules-render` (`core --check`, a start-command file) and the "Onboarding a host" and "Operating facts" sections of `clutch/docs/host-contract.md` were never built and have no ticket. The registry that tracked them was retired, so only this document and the frozen plan record them.
- The CLI has 29 verbs (`clutch/__main__.py:237-287`) against the frozen plan's closed set of 16 (§18.1). Each arrived by ticket; the plan cannot be amended.

## 1. Release plan

Versions follow `pyproject.toml` (`0.3.0` today). Each release below is a minor version, named for the version `clutch release --minor` gives it: a phase is bumped and tagged at its start, so tag `v0.3.0` (`c761b213`) opened 0.3.0. These names were once one minor lower (0.3.0 was `0.2.0`), and older commits, tickets, and Suggestion Box messages use the old names. Each phase takes the next minor when it starts, so if the conditional 0.4.0 window slides, the phases after 0.3.0 are renamed to the versions they start at. `clutch release --minor|--patch` (`release-verb`, merged) bumps, commits, and tags; `./dev.py publish` still bumps the patch again before it uploads, which `release-publish` (row 92) replaces with a publish that never bumps.

| Release | Theme | Gate to start | Gate to ship |
|---|---|---|---|
| **0.3.0** | Truth, hygiene, shared infrastructure, and the roadmap driver (`docs/roadmap-driver-plan.md`) | none | every P0 and P1 row merged; evidence capture live; `docs-truth-sweep` merged so the next audit starts clean; the driver has authored and run at least three roadmap rows on this repo with no operator verdict |
| **0.4.0** | Journal query layer (`docs/journal-sql-refactor-plan.md`) | re-measurement shows a drain start or `status` still dominated by journal reads after `journal-incremental-read` (merged `f790cf71`); if not, this release slides behind 0.6.0 | all four port groups merged and the SQL-only gate in place; no feature ticket runs during the window |
| **0.5.0** | Parallel runs and the graphics kind (`docs/parallel-tickets-plan.md`, `docs/gemini-graphics-refactor-plan.md` Part B) | 0.3.0 dedup tickets merged (`active-slot-single-owner`, `merge-admission-single-owner`, `closed-sets-single-home`); Gemini agent capture A0 committed (fact 7 decides `api-provider-client`); decision 19’s credential rule applies while this machine has no Gemini credential | parallel serve has merged the next 10 tickets with no conflict-rerun cap hit; one `generate` graphics ticket merged through the select commit; `visual_baseline` GO recorded |
| **0.6.0** | Training flywheel, stage panels, and the project index (`docs/training-data-plan.md`, `docs/stage-panels-plan.md`, `docs/annotations-index-plan.md`, evidence verbs) | evidence store has captured at least one full drain | `training export` produces every record kind from this repo's journal; `training eval` scores one lens; a two-member review panel has reviewed the next 10 tickets with its unique-catch count in the retro report; this repo's docs and tests carry filled meta blocks and `context suggest` returns selectors for a real ticket |
| **0.7.0** | Document agent (`docs/document-agent-plan.md`) | isolated read-only calls proven by `isolated-readonly-call`; the owner's lens prompts adapted | the three plans written on 2026-11-13 moved into doc sets and reviewed with `scope` and `buildability` |

Independent of release: `gemini-provider` and `upstream-issue-verb` land in 0.3.0 because they touch nothing the later releases reshape, and both wait on an agent-run capture committed as their evidence; their plans say which agent action captures which facts.

### 1.1 Why this order

- **Truth first.** The audit found 16 places where the maintained documents say something the code does not do, and a capture bug that has lost 1,662 of 3,960 raw model-call records (counted at `328d07d9`). None of the feature plans can be authored against documents that are wrong, and the training plan cannot capture data that is being overwritten.
- **Dedup before parallel.** Parallel runs change the one-run assumption in six separate trackers and the merge path in two separate implementations. Making each of those a single owner first turns the parallel tickets from a rewrite into an edit.
- **Capture early, export late.** The evidence store (0.3.0) only has value once it holds data. Export and eval (0.6.0) are useful on day one if capture started three releases earlier.
- **Journal window is conditional.** Its measured trigger (157 of 164 seconds in journal reads) predates `journal-incremental-read`. The refactor freezes features for a release; it earns that only if re-measurement shows the cost is still there.
- **Document agent last.** It is the largest new surface, depends on the isolated-call mode and the evidence record, and its first real use is reviewing the other plans, which is more useful once those plans have tickets behind them.

## 2. Analysis: duplication

Ranked by how many later tickets it blocks. Every item names the single owner that should remain.

### 2.1 Engine core

| # | Duplicated | Locations | Owner after fix | Ticket |
|---|---|---|---|---|
| 1 | Inline merge and queue admission share about 15 steps verbatim: `ticket_change_findings`, timing and `_refused`, `rev_parse`, `main_code_unchanged`, `restore(TICKETS_DIR)`, the `RebaseRefused` finding text, `gather_safety_evidence`, the skip rule, `read_candidate`, `check_severity`, `run_gates` on both gate sets, hard and soft flattening, `dirty_overlap`, `write_squash` + `retire` | `merge.merge` (`clutch/merge.py:285-328`) vs `MergeQueue._admit` (`clutch/mergequeue.py:271-370`) | `_admit`, with the conflict ladder, safety tier, receipt, tree check, and red streak as parameters; `merge.merge` becomes a thin inline call | `merge-admission-single-owner` |
| 2 | Six trackers for "is something running": `scheduler.py:35-36`, `daemon.py:547-549` (`DaemonAdmission`), `daemon.py:440` (`TicketWriter.active`), `mergequeue.py:86,91`, `driver.py:152`, `restart.py:16` + `serve.py:112`. `serve.upgrade_idle` reads five of them (`serve.py:325-333`). `Scheduler._slot` wraps `admission.dispatch`, which takes its own lock | as listed | `DaemonAdmission` owns the run set; others read it | `active-slot-single-owner` |
| 3 | Three filters over `review.mechanical`: `stages.triggered_hosts` (`stages.py:982-987`), `merge.py:317` (`hard_only=True`), `MergeQueue.host_checks` (`mergequeue.py:198-224`); spool names also diverge (`check/host-NN`, `merge/host-NN`, `merge-<tier>/host-NN`). `docs/how-clutch-works.md:337` says "one shared command runner": true for execution, false for selection | as listed | `triggered_hosts(tier=...)` | `host-check-selection-single-owner` |
| 4 | Run-argv-with-stuck-budget, spool, tail: `run_host_command` (`stages.py:712-728`), `gather_evidence` branch loop (872-885), base loop (893-902), `_gather_bug.execute` (822-829); `MergeQueue._command` (195-196) is a pure pass-through | `clutch/stages.py` | `run_host_command` | `host-check-selection-single-owner` |
| 5 | "Latest `state_transition` for stem" scanned inline 13 times: `stages.py:287,1562`; `serve.py:151,158,411`; `drain.py:107,456,547,586,594,681,699,731`. `status.last_states` returns only the state string | as listed | `journal.last_transition(events, stem)` beside `run_terminals` | `journal-last-transition-helper` |
| 6 | Effect-completion lookups by key bypass `Effects._recorded` (`effects.py:49-53`): `stages.served_review:198`, `mergequeue.retained_ticket:138`, `merge.lifted_report_paths:370-376`, `runner.apply_admission:676-680`, `mergequeue._finish:164`, `checkpoint._history` | as listed | `Effects.recorded(key)` | `journal-last-transition-helper` |
| 7 | Eligibility filter: `Scheduler.dispatch_next` (`scheduler.py:50-76`) and `_Drain._select` (`drain.py:508-558`) both compute `settled_dependencies`, `supersedes_maps`, `authored_at`, `parked_blob`, `reofferable`, then `order_tickets` + `write_queue`; drain adds `depends_cycle`, over-budget, storm, drought | as listed | one `eligible(events, tickets, ...)` in `drain.py`, consumed by `Scheduler` | `serve-parallel-dispatch` (it rewrites `dispatch_next` anyway) |
| 8 | The former `run_stages` provider-exception mapper had no production caller: `Driver._run` maps stage failures first. Only a deleted test invoked requisition review inside a stage; `requisition_review` was the correct surface for that exception. | `runner.drive` and formerly `run_stages` | No mapper covers stage operations; the driver maps their provider failures | `provider-failure-single-mapper` (done) |
| 9 | `running` transition + reoffer written by three callers: `runner.run_ticket:525-526`, `drain._run_one:571-574`, `serve.py:150-154` | as listed | `runner.run_ticket` | `serve-parallel-dispatch` |
| 10 | Constructors repeated: `EngineLog(...)` built 8 times (`runner.py:123,503`; `drain.py:232,357,606`; `serve.py:117`; `driver.py:190`; `triage.py:369`), `storm_producer(...)` 15 times with identical args, `Driver.from_config(...); driver.journal = ...; driver.effects = Effects(...)` 5 times (`__main__.py:619-621`, `triage.py:85-87,110-112`, `runner.py:139-141,487-489`). `Driver.from_config` builds a `Journal` and `Effects` every caller overwrites; `Effects.__init__` scans the whole journal, so each bind pays a wasted read | as listed | `Checkout`/`StageContext` carry `log` and `box`; `Driver.from_config` takes `journal` | `main-verb-groups` |
| 11 | `gather_safety_evidence` runs twice per admission: `merge.py:307` then inside `gather_evidence` (`stages.py:911`); same at `mergequeue.py:312` + 330 | as listed | `gather_evidence` reuses the safety result | `merge-admission-single-owner` |
| 12 | "Refused" constructors: `merge._refused`, the `refused` closure in `_admit`, `stages._short`, and inline `StageResult(outcome="gate_failed", ...)` at `runner.py:219`, `stages.py:1454,1457,1465,1577`, `daemon.py:360,404,415-422` | as listed | `artifacts.refused(findings, cost)` | `merge-admission-single-owner` |
| 13 | Fence matching: owner `stages._in_fence` (978-979); re-implemented at `watchdog.py:60`, `drain.py:484` (different semantics: trailing-slash dirs only), raw `startswith(f"{TICKETS_DIR}/")` at `merge.py:108,248,385`, `stages.py:1224` | as listed | `_in_fence`, moved to `clutch/tickets.py` (the fence grammar's home) | `fence-overlap` (it adds the pure overlap function beside it) |
| 14 | `retro_check` phase logging with two outcome vocabularies: `drain.py:605-613` ("ran"/"no_report") vs `serve.py:339-353` ("due"/"not_due") | as listed | one vocabulary in `retro.py` | `docs-truth-sweep-code-strings` (done) |

### 2.2 Closed sets with more than one home

| Set | Homes | Owner |
|---|---|---|
| Tiers `low|medium|high|max` | `config.py:21`, `llm.py:10-11`, `tickets.py:33`, `caps.py:13`, `policy.py:15`, `__main__.py:378` | `llm.py` |
| Priorities `P0..P3` | `tickets.py:58`, `__main__.py:273`, `dev.py:87` (`observe.py:716` already derives from `Frontmatter`) | `tickets.py` |
| Kinds `feature|bug|chore` | `tickets.py:59`, `tickets.py:810`, `__main__.py:269,791`, `dev.py:83`, `author.py:245` (different order), `hostfiles.py` CORE_TEMPLATE | `tickets.py`; the template names the verb, not the list |
| Settled and retired states | `status.py:17` `SETTLED`, `drain.py:53` `RETIRED`, `stats.py:11` `SETTLED` (same name, different set), `tickets.py:711` literal; `SETTLED | {"rejected"}` spelled out 15 times, `SETTLED | RETIRED` 8 times | `status.CLOSED = SETTLED | RETIRED`; `stats.SETTLED` deleted |
| Failed-attempt terminals | `caps.py:48`, `scorecard.py:85`, `journal.py:101`, `stats.py:122` | `journal.py` |
| Surfaces | `specs/__init__.py:32` (8), `observe.py:33-44` (10), `stats.py:12` (6), `observe.py:274,814`, `providers.py:29`, `policy.py:14` | `specs/__init__.py`; observe and stats derive |
| Spike kinds | `config.py:23` owner; `clutch/docs/host-contract.md` repeats the list at lines 133, 193, 202, 206 | `config.py`; the contract lists it once |
| Box classes and policy rows | `box.py:18`, `config.py:25-49`, `policy.py:33-45`, `host-contract.md:134,213`, `specs/triage.md:20-28` | `box.py` (classes), `config.py` (rows), `policy.py` the only bridge |
| Triage verdicts | `triage.py:33`, `box.py:63,69,403` (three overlapping Literals in one file) | `box.py` |
| Control verbs | `control.py:16,72`, `__main__.py:254-257`, `lockfile.py:19`, `observe.py:835-842` | `control.py` |
| Ask kinds | `ask.py:11` owner; `__main__.py:398-421` branches per literal; `observe.py:527-529` hand-lists three menu entries | `ask.py` |
| Finding codes | `ticket_schema` at `tickets.py:30`, `author.py:39`, `rework.py:66`; `requisition_review`/`requisition_rma` at nine sites; `core_drift` at `hostfiles.py:192,205,214` | `gates.ENGINE_GATE_CODES` plus one registry for stage finding codes |
| Conduct-file routing `{claude, qwen}` -> `CLAUDE.md` | `providers.py:131`, `host-contract.md:274`, `how-clutch-works.md:756` | `providers.py`; docs cite it |

Ticket: `closed-sets-single-home`.

### 2.3 Repeated helpers and projections

- `NonBlank` redefined in `author.py:28`, `triage.py:27`, `box.py:55`, `inbox.py:15` while `artifacts.py:25` exists. `_Strict` bases in `config.py:61`, `box.py:58`, `inbox.py:29`, `artifacts.py:47`, `stages.py:79`.
- Repo-relative path validators: `tickets.py:210`, `box.py:22`, `inbox.py:22`, `config.py:118`, `covgate.py:54`.
- Spec-major extraction `int(version.split(".")[0])`: `requisition.py:141,161`, `rework.py:212`, `policy.py:28`, `baseline.py:45`; `stages.py:391` is already a helper nobody calls.
- Hand-rolled git blob SHA: `requisition.py:136`, `hostfiles.py:203`, `stages.py:281`.
- Retro-recurrence reopen boundary: `author.py:159-161,179-181`, `triage.py:263-270`.
- `requisition_verdict` signal body built by hand: `__main__.py:643-655`, `author.py:360-364`, `rework.py:169-180`, `runner.py:199`. `ticket_intake` body: `tickets.py:768` uses `INTAKE_SIGNAL`, `author.py:359` a literal.
- Scorecard table builder byte-identical in `status.py:246-255` and `retro.py:255-265`.
- Literal `"box"` instead of `BOX_DIR` at `__main__.py:80,460`, `author.py:74`, `ask.py:24`, `observe.py:757`; `f"tickets/{stem}/ticket.md"` instead of `ticket_path()` at `__main__.py:141`, `triage.py:201`, `observe.py:240,678,687`.
- Last-state fold: `status.py:58-60` canonical; re-implemented at `observe.py:395-398,604-607,552`, `__main__.py:128,160-162,431`, `providers.py:244`. `observe.journal()` returns dicts, so `observe` wraps them in `SimpleNamespace` four times to call Event-typed helpers.
- Attempt counting with three semantics: `caps.py:54-56`, `observe.py:403`, `stats.py:112`. Spend sum at `status.py:194`, `stats.py:130-131`, `retro.py:151,160`.
- Frontmatter read by regex outside the owner: `observe.py:218-224,278-281`, `retro.py:228` (duplicates `tickets.py:82` `_BUDGET`), `__main__.py:789-792`.
- `"cap spent"` produced by `caps.py:108` and parsed back by `observe.py:315`. `provider_drought` body probed at 14 sites.
- `__main__.py`: lock acquire/try/release written four times (514-520, 527-539, 672-715, 839-861); `_require_engine` + `read_active` + `ValueError -> Refusal` three times; `observe.Context(...)` twice; `lambda: load_config(...)` six times; four ad-hoc `print(..., file=sys.stderr); return 2` beside the shared handler at 580-586; `checkout` built for every verb past line 435.

Tickets: `main-verb-groups` (the `__main__.py` items and constructors), `closed-sets-single-home` (helpers that guard a closed set), `journal-last-transition-helper` (projection folds).

### 2.4 Provider stream parsing

`ClaudeAdapter.parse` (`providers.py:465-479`) and `CodexAdapter.parse` (493-511) read the terminal event and usage; `watchdog.CallMeter._consume` (85-126) re-parses the same fields with its own guards; `observe.live_call` (189-215) re-encodes the adapters' argv by regex over `ps` output. `docs/evidence-trail-plan.md` makes the per-provider normalizer the single parser and lists moving `CallMeter` and `Parsed` onto it as a follow-up once normalizers have run on real traffic.

### 2.5 Rules stated in more than one home

Second problems to the Box and verify at base (`hostfiles.py:55`, `CLAUDE.md:90-91`, `AGENTS.md:84-85`, `specs/implement.md:24-26,133-134`); read before write (`hostfiles.py:56`, `CLAUDE.md:92-93`, `AGENTS.md:86-87`); smallest change (`hostfiles.py:52`, `CLAUDE.md:72-73`, `AGENTS.md:68-69`, `implement.md:23-24`); never push (`hostfiles.py:44,54`, `CLAUDE.md:88-89`, `implement.md:56-58`); never hand-edit the managed block (`hostfiles.py:53`, `CLAUDE.md:82-83`, `host-contract.md:272`); the set-membership grep rule verbatim in `host-authoring.md:55` and `specs/requisition_review.md:24`; the bug-evidence refusal sentence three times (`host-authoring.md:88-92`, `how-clutch-works.md:148-151,315-318`); unit-test discipline in `implement.md:60-68`, `review.md:37-39`, `retro.md:24`, `how-clutch-works.md:225-229`.

The `CLAUDE.md` rule "a rule has one of two homes" is the fix; `docs-truth-sweep` removes the restatements in `docs/` and `clutch/docs/`, and `conduct-files-parity` settles the three rule files. Specs may restate a rule the model needs; documents may not.

### 2.6 Tests

- No `conftest.py` anywhere. 37 test modules double as fixture libraries (257 top-level cross-test imports); `tests/integration/serve_rig.py:21-24` imports from four test modules; `test_drain.py:30-33` imports and calls a test function from `test_merge.py` as its body; `test_merge.py:43` reads `test_stages.py` as text and slices its `CONFIG` literal out.
- Fakes: 9 clock fakes, 18 exec fakes, 11 filesystem fakes, 10 journal fakes, 8 git fakes defined across tests; `clutch/seams.py` ships none (only `FakeLLM` in `clutch/llm.py:58`).
- `until`/wait has three implementations with three semantics (`serve_rig.py:27`, `test_drain_admissions.py:15`, `tests/waiting.py:10`); `repo()` fixtures six times building the same shape; `git()` four times with four meanings; `reply()` seven times.
- `CONFIG` literal at 12 sites (three byte-identical groups), `TICKET` at 7, `config.yaml` written in 63 files, git-init sequences in 22.
- The do-not-grow rule is in `CLAUDE.md` section A and `AGENTS.md` `## Engine conduct` (`contention-authoring-rules`, done). It names seven files: the five measured at `80b76d5d` (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `serve_rig.py`), which took 53 commits in the 13 days to 2026-11-13, and `tests/integration/test_cli.py` and `tests/integration/test_watch.py`, added when the list was re-measured at `c761b213`.

Tickets: `test-fakes-and-conftest`, `contention-authoring-rules` (done).

## 3. Analysis: gaps

### 3.1 Defects found by the audit

| Defect | Location | Ticket |
|---|---|---|
| The former stage mapper had no production caller; only a deleted test called requisition review inside a stage, for which `requisition_review` was the correct label. `Driver._run` maps production stage failures, so no mapper covers stage operations. | formerly `stages.run_stages` | `provider-failure-single-mapper` (done) |
| Raw provider captures overwritten across processes: `_seq` restarts at 0 per process, so `providers/<stem>/<provider>-0001` is rewritten by the next run of the same stem. 3,960 journaled calls, 2,298 captures with `events.jsonl` at `328d07d9`; reproduced by `tickets/provider-capture-overwrite/evidence/` | `providers.py:294,324-325` | `provider-capture-overwrite` (P0, authored 2026-11-14); cause fix `evidence-envelope` |
| `served_review` swallows `ValueError, KeyError, TypeError, AttributeError, GitError` to `(None, None)`, nulling the receipt's provider and model on any defect | `stages.py:227-228` | `docs-truth-sweep` names it; fix in `merge-admission-single-owner` |
| Coverage parse `except: pass`, so coverage is silently absent although §5.4 says it is recorded; base `results` read then discarded | `stages.py:1104-1105,1191-1194` | `host-check-selection-single-owner` |
| `diagnosis.json` is not written when the worktree is gone, although §6.3 promises it | `runner.py:275-277` | `docs-truth-sweep` (document the truth) |
| Operator paved roads print `uv run python -m clutch drain|confirm|reject` and other argv instead of a verb, in the drain report and in `status.py`, `doctor.py`, and `providers.py`; `Admission("refuse", "unknown box id")` carries `paved_road=""`; `retro.py:458` collapses the stage outcome into `ValueError`; seven `BoxError`s name the fault without a repair | `drain.py:182,186,710,721`; `status.py:149`; `retro.py:458`; `box.py:179-434` | `paved-roads-name-verbs` (done, `tickets/paved-roads-name-verbs/`) |
| `watch` shows spec-frontmatter tier and effort for review, diagnose, author, triage, and requisition_review, but the code never passes spec tier for those surfaces | `observe.py:229-231`; `author.py:316`, `triage.py:311`, `stages.py:453,660,1508` | `watch-surface-tier-truth` |
| `harvest.json` is written without the redactor; `diff_stat` and finding messages are not pre-scrubbed. `redact.py:7-9` checklist says "journal writer NOT YET WIRED" and "harvest serialization: not built" | `runner.py:443-483`; `redact.py:7-9` | `redaction-harvest-seam` (done) |
| `argparse` help for `review` says "under the lock"; the verb takes no `Lockfile` | `__main__.py:258` vs 589-660 | `docs-truth-sweep-code-strings` (done) |

### 3.2 Seams bypassed

`FileSystem` (`seams.py:207-216`) has no `mkdir` or `remove`, so callers cannot comply: `enginelog.py:29-32,39` raw `mkdir`/`open("ab")`/`Path.replace`; `journal.py:149` constructs `LocalFileSystem()` itself and `176-191` uses raw `os.open`/`os.write`; `stages.py:486,496` raw `mkdir`, `519,867,1068,1186,1446-1447` raw `unlink`; `driver.py:189` `fs or LocalFileSystem()` default in engine code; `scheduler.py:80` reaches into `journal.dir.parent`, `journal._fs`, `journal._clock` to write `queue.json`. Ticket: `fs-seam-mkdir-remove`, which also makes `write_queue` take the seams it needs.

### 3.3 Deferred items whose trigger has fired

| §18.2 item | Trigger | Fired | Decision |
|---|---|---|---|
| Mechanical scope-fence closure analyzer | first fence-gap escape `requisition_review` misses | twice: `box-000324` (three rejects), recurrence in `tickets/retro/000046.md` proposal 2 (`test_menu_verb_parity.py:185`) | Decided (section 6, decision 1): 0.3.0 widens the prompt rule to in-code registries (`fence-closure-registries`); a third escape schedules a spike for the mechanical analyzer in 0.4.0 |
| DuckDB analytics | first projection measured too slow as a fold | yes, 157 of 164 seconds (`tickets/journal-incremental-read/evidence/`), before the incremental reader merged | re-measure; 0.4.0 is conditional on it |
| Triage-dedup real-model eval | daemon-era entry | yes, serve has run since the daemon era | not scheduled; `training-eval` (0.6.0) covers triage records and makes this the first lens to score |
| Concurrent worker pool, dispatch overlap skip | measured starvation post-cutover | not fired; owner chose to bring it back for contention, not starvation | 0.5.0, declared in `docs/parallel-tickets-plan.md` |
| Conflict-only micro-rework | first chronically re-resolved conflict in `merge_conflict_facts` | 13 events exist; nobody has read them | `merge-model-resolve` starts by reading them (its plan's A0) |

### 3.4 Never built, no ticket

- P8 `rules-render`: `clutch core --check` and a start-command file. `doctor` has a `core` drift row (`doctor.py:67-73`); `serve`, `drain`, `run` refuse on stale blocks. Decided 2026-11-13: dropped (section 6, decision 2).
- `clutch/docs/host-contract.md` "Onboarding a host" and "Operating facts" sections (P8). Its two sections still titled "Pending report-inbox contract" and "Pending cutover contract" describe shipped code. `docs-truth-sweep` retitles them; the onboarding checklist is `training-docs`' sibling, `host-onboarding-doc`, scheduled in 0.3.0.
- `review.surfaces`: refused at config load "until a host that uses them onboards". Stays refused. `docs/document-agent-plan.md` Open decision 2 is the first proposal that would need host-defined prompts and it routes them as data instead.
- `kind: api` provider: refused at `config.py:460-465`; stays deferred.

### 3.5 Dev surface and tests

- At the audit, five verbs had no `./dev.py` subcommand: `covgate`, `doctor`, `migrate-config`, `retro`, `snapshot` (`pause`, `resume` also absent). `CLAUDE.md` §B now directs missing engine tasks to new `clutch` verbs and missing build tasks to new `dev.py` subcommands.
- `./dev.py test` runs `uv run pytest -q` with `addopts = "-n auto"`; it never loads `clutch.testguard`, so the unit IO guard and the 60-second budget apply only inside Check. `how-clutch-works.md:79` says otherwise.
- `tests/regress_*.py` (45 files) run only as bug tickets' `## Regression` argv; 10 have no `__main__` guard and execute at import. `tests/vscode_task_identity.js` is referenced by one of them and no test.
- `test-gate.toml` lists 57 of 59 modules; `clutch/graph.py` has no floor; eight modules sit at floor 0 (`audit`, `covmap`, `doctor`, `observe` at 856 lines, `seams`, `stats`, `thresh`, `watchdog`).
- Lint and the authoring guide disagree in both directions. Guide rules not linted: spec version "next minor above main" with a fenced pin (`host-authoring.md:57-58`), fence the document a behavior change affects (55-57), criterion names the wrong result it rules out (63-65). Linted rules the guide does not state: banned adjectives (`tickets.py:78`), no `clutch/specs/*.md` in `## Context` (377-378), `stuck` exceeds `expected` (462-463), `## On-demand` under the fence (422-423), `## Depends on` accepts `none` (342), reserved stems (28), `## Regression` refused on a non-bug (447), the stuck ceiling (`__main__.py:718`).
- Extension: `order` argv is assembled in JavaScript (`vscode-clutchwork/extension.js:52,56,58`) while `confirm`/`reject`/`drain` argv come from the snapshot; `review`, `lint`, `run`, `triage`, `dismiss`, `serve`, `stop`, `prompt <kind>` are JavaScript literals (334-371); `clutchRoot()` (9-13) picks the workspace folder by probing the filesystem. `CLAUDE.md` says argv and policy come from the snapshot.
- Config declared and read nowhere: `caps.poison` (`config.py:182`), `review.trigger_map` (151; pinned by four test files), `ReviewSurface` and `rules_doc` (129-133, unreachable). Spec frontmatter `consumes`, `emits`, `gates` (`specs/__init__.py:76-80`) is validated and read by no stage; `tier:` is honored only by retro (`retro.py:451`). `requisition_review.md:54-58` `context` always receives the literal `"included in render"` (`requisition.py:218`).
- No engine caller: `heartbeat.is_fresh`, `Timers.wait_next`, `Git.branch`, `Git.init`, the `effects.effect` decorator, `gates.lint_gate`, `providers.CliAdapter.parsed_failure`, `requisition.RequisitionGate`, `requisition.base_render_chars`, `observe.uncommitted_tickets` (20+ tests monkeypatch it), `policy.baseline_identity`, `audit.audit`, `watchdog.Detector.watch`. Untested production paths: `mergequeue.retained_ticket`, `stages.served_review`, `serve.Responsiveness`, `runner.PreparedDispatch`, `stages.ticket_blob`.

Tickets: `dev-surface-completeness`, `regress-scripts-guarded`, `test-gate-floors`, `lint-guide-parity`, `extension-argv-from-snapshot`, `dead-config-and-spec-fields`.

## 4. Analysis: drift

Every row is a claim the owning document makes that the code contradicts. `docs-truth-sweep` fixes each by changing the document to the code's behavior, except where the row names a code ticket.

### 4.1 `docs/how-clutch-works.md`

| Line | Claim | Code | Truth |
|---|---|---|---|
| 79 | unit tests "run under `clutch.testguard`" via `./dev.py test` | `dev.py:62`, `pyproject.toml:30`, no conftest | only the Check-gate argv loads the plugin (`config.yaml:36`); code fix in `dev-surface-completeness` |
| 131 | `draft` "awaits `confirm`" | `tickets.py:692-695` | intake stamps every new hand-written ticket `confirmed`; only Author drafts wait |
| 177-178 | lift "refuses symlinks" | `stages.py:332-342` | symlinks are skipped silently; only over-size raises |
| 244 | Check "runs configured autofix commands" | `stages.py:1407` | only when Implement replied `ok` and `review.autofix` is nonempty |
| 373 | lift kind `harvest` | `runner.py:371` | also `harvest-rework` |
| 388-389 | worktree gone: `diagnosis.json` is lifted | `runner.py:275-277` | nothing is written or lifted; only the journal signal |
| 452-453, 485-488 | paved roads say `clutch confirm|reject` | `drain.py:182,186,710,721` | drain prints `uv run python -m clutch ...`; code fix in `paved-roads-name-verbs` (done, `tickets/paved-roads-name-verbs/`) |
| 463-464 | Reconcile reaps any stem still `running` | `reconcile.py:22,38` | stems with a HELD regate receipt at the current attempt and intents under `llm/review-<stem>/` are excluded |
| 475-477 | drain loop steps omit Box intake | `drain.py:396` | drain calls `triage.report_intake` every iteration |
| 528-530 | queue skip rule | `mergequeue.py:313` | also requires no HELD receipt |
| 581 | preflight at run/drain/serve/triage | `__main__.py:618,696-697` | also `review` and `retro` with a report |
| 592-593 | "a call waiting over 60s spills" | `thresh.py:167,177` | spill is decided up front from the projected wait |
| 679-680 | prune candidate: 25+ evaluations and no catch | `scorecard.py:94` | also requires zero escapes |
| 694 | one `retro_check` phase | `serve.py:353`, `drain.py:613` | two outcome vocabularies; one (`clutch/retro.py::RetroCheckOutcome`) since `docs-truth-sweep-code-strings` (done) |
| 708 | `signal` is "a closed list" | `journal.py:94` | no registry; writers use `signal` or `kind` as the body key |
| 72 | `reject <stem> [--yes]` | `__main__.py:277-281` | also `--extension` |
| 10.1 table | state_dir files | `__main__.py:342,370`, `covmap.py:32`, `rework.py:122`, `box.py:268` | omits `drain.out`, `coverage-map.json`, `rework/<stem>/<attempt>/<call>/`, `spools/probe/`, `box.seq/`, `worktrees/.base/`, `.regression-base/`; rotation bounds 16 MiB x 3 and 64 MiB / 24 h unstated |
| 10.2 | event types | `journal.py:32` | `checkpoint` type exists, never emitted; about 30 signal kinds unlisted |
| 3.3:188 | engine commits on main | `retro.py:298`, `stages.py:1393` | omits `clutch(decisions): <id>`, `clutch: retro NNNNNN`, `undo refused rework`, branch `autofix` |
| 11 | config areas | `config.py:83-91,226,75` | `providers[].package` (required for every CLI) unmentioned; `routing_default_tier` and `quota_window_minutes` defaults unstated |
| 54 | `probe` row | `__main__.py:391` | exits 1 when any probe fails |
| 61 | `drain [--detach]` | `__main__.py:284-285` | also `--parked STEM`, `--deadline ISO` (set by the self-upgrade re-exec) |

### 4.2 Other documents

| Document | Claim | Truth |
|---|---|---|
| `README.md:31` | runs that exhaust attempt caps file to the Suggestion Box | they route to the Reject queue (`runner.py:390-393`, `drain.py:687`); `how-clutch-works.md:416,432` are right |
| `clutch/docs/host-running.md:19` | serve "accepts [retro] but does not yet run it" | `serve.py:339-355` runs it |
| `clutch/docs/host-contract.md:6-7,383,422,442` | "Pending report-inbox contract", "Pending cutover contract", "adds no report consumer" | `triage.py:358-372`, `inbox.py:120` ship the consumer |
| `host-contract.md:45,330` | `trigger_map` is "engine gate codes only" | `config.py:151` validates nothing; it is read by nothing |
| `host-contract.md:299` | "Put ordering in Depends on and priority" | `## Runs before` exists for ordering; `Depends on` is merged-code only (`hostfiles.py:22`, `host-authoring.md:33-38`) |
| `host-authoring.md:15-21` | lint's checks | omits the `drain.max_ticket_minutes` stuck ceiling (`__main__.py:718-721,759`) |
| CORE_TEMPLATE (`hostfiles.py:20`) | `clutch docs` prints "(authoring, running, config contract)" | four guides including qwen (`__main__.py:312`); dropping the parenthetical frees 36 of the template's 352 spare bytes |
| `CLAUDE.md` vs `AGENTS.md` | "a rule add/change/remove touches both files" | `AGENTS.md` lacks "Lean ticket frontmatter" (`CLAUDE.md:94-95`), "The plan is the seed" (86-87), "Phase order" (107-108), and the "compress it to one line" sentence (57) |
| `clutch/docs/host-authoring.md:12,16,25`, `host-qwen.md:66`, `clutch/specs/ask/*.md` | name `./dev.py` | engine-owned files carry this repo's dev surface, which no host has (`box-000440`) |
| `clutch/mergequeue.py:1`, `clutch/heartbeat.py:1` | "Dormant" | serve routes every merge through the queue (`serve.py:129`); serve refreshes the heartbeat every loop (`serve.py:203-209`); both docstrings fixed by `docs-truth-sweep-code-strings` (done) |
| `clutch/redact.py:7-9` | "journal writer NOT YET WIRED", "harvest serialization: not built" | fixed by `redaction-harvest-seam` (done): `clutch/runner.py::harvest` scrubs `harvest.json` at the write, and the checklist names every writer |
| `vscode-clutchwork` settings | `how-clutch-works.md:116-119` names `clutch.playAction`, `clutch.statsWindow` | `clutch.command` (`package.json:73-83`) is named only in `README.md:77` |

### 4.3 Plan documents (fixed in this revision)

| Plan | Was | Now |
|---|---|---|
| training-data | `docs/host-contract.md` | `clutch/docs/host-contract.md` |
| training-data | 2,301 capture directories | 2,453 (directories holding `events.jsonl` at `0895b5d4`) |
| training-data, evidence-trail | two stores (`training/`, `evidence/`), two layouts, two retention stories, `spools/providers/` both kept and replaced | one store, section 5 decision 1 |
| parallel-tickets | `tests/test_stages.py` | `tests/integration/test_stages.py` (tickets fenced the old path) |
| gemini-graphics | `__main__.py:771`; "the watchdog's unit test file" | the kind check in `_new` (line 791 at `80b76d5d`); `tests/integration/test_watchdog.py`, `test_watchdog_activation.py` |
| journal-sql | measurement presented as current | `journal-incremental-read` merged at `f790cf71`; trigger must be re-measured |
| upstream-issue | status cites `ed48cbc9` (the Gemini plan's commit) | written 2026-11-13; revised at `80b76d5d` |
| document-agent | `docs:` config block, `specs/doc/review.md`, `writes` "flag" | `documents:`, `specs/doc/lens.md`, `writes` is derived from `WRITING_SURFACES` |
| all seven | different status forms, ticket-table columns, "Deferred" vs "Open" decisions, no priorities in three | one shape, section 7 |

## 5. Cross-plan decisions

Each decision settles a place where two plans overlapped or contradicted. The plans are revised to match; a plan that wants to change one of these changes it here first.

1. **One call-record store.** `<state_dir>/evidence/` (`docs/evidence-trail-plan.md`) is the only store for model-call records. The training plan adds attempt manifests, export, and eval on top of it and owns no store of its own. `spools/providers/` is replaced by the evidence store in `evidence-envelope`; the per-attempt `spools/<stem>/<attempt>/` (prompt, output, check output) stays until a later ticket moves it, which no plan schedules.
2. **Capture always on, training gated.** The envelope and raw stdout/stderr are captured for every call, as `spools/providers/` is today, because diagnosis and harvest read them. Retention is `evidence.max_gb` (default 20; evidence plan). Attempt manifests with full diffs, export, and eval are behind `training_data.enabled` (default false; training plan). `training_data.dir` is dropped: the store location is fixed.
3. **Record identity.** A record's id is the journal effect key. Ticketless calls key under their surface name (`driver.py:274`), so `stem` is nullable and `group` is the stem or, for triage, author, retro, and document lenses, the surface. Isolated calls (document agent) record `repo: null` and `process.cwd` as the scratch directory; no conduct file is loaded and the record says so.
4. **One P0 for the capture bug.** `provider-capture-overwrite` is a single bug ticket owned by this roadmap. Its cause fix, under the CORE two-ticket rule, is `evidence-envelope` (every capture path keyed by the journal identity of what it captures). Both plans cite the stems; neither owns them.
5. **CORE_TEMPLATE byte ledger.** 7,840 of 8,192 bytes used (`tests/integration/test_hostfiles.py:33`). Spend: `conduct-files-parity` frees 36; `upstream-issue-verb` adds about 264; `graphics-kind` adds 9. Order in 0.3.0 and 0.5.0 keeps them from colliding; after both, about 115 bytes remain. Any further template text first compresses a rule that has gained its gate (`CLAUDE.md:57`).
6. **Names.** The document agent's config block is `documents:` (not `docs:`, which is a verb and a directory). Its lens spec is `clutch/specs/doc/lens.md` (not `review.md`, which exists at `clutch/specs/`). Its specs carry the spec frontmatter that `tests/unit/test_specs.py:24` checks on everything under `clutch/specs/`.
7. **Journal window.** 0.4.0 runs only on re-measurement. Its port tickets touch the same files as `serve-parallel-dispatch` and `conflict-discard-rerun`, so the parallel tickets land after the window, or before it if the window slides. Several runs in one process appending to the journal is compatible with the query layer's per-process offset because `journal.lock` serializes appends; the journal plan states this.
8. **Shared files between plans.** `graphics-render-check` and `conflict-discard-rerun` both bump `clutch/specs/implement.md`; `graphics-render-check` runs first (it heads the longer chain). `upstream-issue-verb` (0.3.0) and `graphics-kind` (0.5.0) both edit `hostfiles.py`, `CLAUDE.md`, `AGENTS.md`, `README.md`; releases separate them. `gemini-provider`, `evidence-envelope`, `isolated-readonly-call`, and the journal ports all fence `clutch/providers.py`; under the parallel plan's own overlap rule they serialize, which the release slots already arrange.
9. **Design-record departures are declared.** A plan that re-opens a `CLUTCH_PLAN.md` §18 item names the item, the trigger, and the owner decision in a "Departures from the design record" table. The parallel plan already did; the training, evidence, and document plans now do (audit trail and blob store, §18.1; metadata taxonomies, §18.1). The owner's decision of 2026-11-13 is the cited incident.
10. **Host-command lock.** The parallel plan's engine-wide semaphore around `run_host_command` also serializes the graphics plan's render command and the merge queue's host checks. One lock, stated in both plans.
11. **The mergequeue docstring** was fixed by `docs-truth-sweep-code-strings` (done), not by a parallel-plan ticket; that plan's row 2 now points at the roadmap's `active-slot-single-owner` and `merge-admission-single-owner`, the two 0.3.0 chores its dispatch and merge tickets depend on.
12. **Optional dependencies.** The graphics plan's image libraries ship as the extras `clutch[images]` and `clutch[images-embed]`, imported lazily by `clutch/images.py`; core clutch gains no dependency. A later plan that needs a heavy library follows the same shape. The journal plan's `duckdb` is the one core dependency a plan adds, earned by D3's named trigger.
13. **Generator and judge are different models.** Any surface that judges a model's output (`review_visual` now; a future image or audio judge) routes to a different model family than the surface that produced it; `doctor` warns and lint snags when a config breaks that. The owner's 2026-11-14 note on the Gemini models is the incident: image models answer with pictures, and a model grading its own family grades kindly.
14. **One panel mechanism.** Running a stage as several independent calls and combining them is `docs/stage-panels-plan.md`'s `clutch/panel.py`, declared per routing row. The document agent's `doc-review-runner` depends on `panel-combiners` instead of building its own; the graphics judge's `judge_samples` majority is the `majority-verdict` combiner. No plan adds a second fan-out.
15. **The index is a cache.** `<state_dir>/index.duckdb` (`docs/annotations-index-plan.md`) is derived and rebuildable, read by no gate and no dispatch. `duckdb` enters `pyproject.toml` once, with whichever of `journal-query-layer` or `index-build` lands first, under D3's named trigger. clutch ships no embedding model; vectors come from a host-declared command.
16. **The driver's authority.** The roadmap driver (`docs/roadmap-driver-plan.md`) may edit a held ticket only through a reviewed Rework-update within the supervising rules, may keep it at most `caps.supervise` times per operator lineage, authors at most `--ahead` rows past the running set, and publishes only under `release.publish: true`. Sessions never push on their own. The supervising agent loop confirms or rejects only by executing a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation (driver plan open decision 5). CORE_TEMPLATE’s supervising-session rule still forbids a session to confirm or reject, and its change waits in the Suggestion Box as box-000508.
17. ~~**Superseded is settled.** A split's parent enters a settled state `superseded` and leaves the Reject queue by itself; the three historical parents rejected by hand are the incident.~~ Struck: the premise is false. A published Rework split never reaches the Reject queue: `clutch/runner.py::failure_terminal` journals the parent's terminal without `routed` and retires it through `reject_ticket` in the same second (box-000471). The split parents a person killed were Rework splits that did not publish, and they carry no `supersedes` signal (box-000473).

## 6. Owner decisions (decided 2026-11-13)

Decided by the owner in chat on 2026-11-13. Each plan's "Open decisions" section records its decisions; later decisions below amend them.

1. **Mechanical fence-closure analyzer** (§18.2; trigger fired twice). Decided: instructions first. `fence-closure-registries` (0.3.0) widens the reviewer prompt to in-code registries and tables. A third escape schedules a bounded spike for the mechanical checker in 0.4.0.
2. **P8 `core --check` and start-command file.** Decided: dropped. `doctor`'s `core` row and the start refusal cover drift detection; no host has asked for a start-command file. Both are recorded here as not built on purpose and are tracked nowhere else.
3. **Settled-ticket archive.** 537 directories under `tickets/`. Decided: nothing until a scan (lint with no stems, intake, the snapshot) is timed and found slow; the timing is filed as evidence when it happens.
4. **Split the do-not-grow test files.** Decided: the do-not-grow rule lands in 0.3.0 (`contention-authoring-rules`, done; it names seven files, the five measured at `80b76d5d` plus `tests/integration/test_cli.py` and `tests/integration/test_watch.py` measured at `c761b213`); splitting is chore tickets, one per file, during the 0.4.0 window if it runs, else in 0.5.0 before parallel runs start.
5. **Parallel plan.** Decided: `serve` only; longest-chain ordering below P0 only (P0 keeps the emergency lane); conflict reruns have their own cap `CONFLICT_RERUN_LIMIT = 2` and never draw `retry`.
6. **Training plan.** Decided: the export includes the full normalized tool-call trajectory (a per-run flag can trim it); Author-written tickets are included, tagged `authored_by: author`.
7. **Evidence plan.** Decided: providers' own session transcripts are not copied, only their ids are recorded; Claude thinking text is stored as a blob with `visibility: text`.
8. **Document plan.** Decided: `diverse: false` by default (same model per panel, `--diverse` per run); host-defined lenses and facets allowed as data inside the engine frame; commands only, no `doc` ticket kind in v1.
9. **Journal plan.** Decided: DuckDB; the SQL-only rule goes in `CLAUDE.md` and `AGENTS.md` with a lint gate that lands in the last port ticket and carries a named allowlist for the folds that stay Python.
10. **Upstream issue plan.** Decided: five critical classes. The proposed four plus `wrong-refusal`: clutch refuses valid input (config, ticket, intake) with a message whose paved road cannot be followed.

Decided 2026-11-14, from the plans' remaining open items:

11. **Training eval.** Ships in clutch (`training-eval`, 0.6.0); it doubles as the deferred triage-dedup eval.
12. **Per-attempt spools.** Move onto the evidence store later: `spools-onto-evidence-store` (0.6.0), after the store has run a release.
13. **One parser per provider.** `CallMeter`, `Parsed`, and `live_call` move onto the evidence normalizers after a release of real traffic: `one-parser-per-provider` (0.6.0).
14. **Document agent.** Doc sets are any `docs/<name>/` with a `docset.yaml`, found by search; panels default 3, minimum 2; the plans written 2026-11-13 become the first doc sets once `doc-facet-registry` and `docset-manifest` merge, reviewed with `scope` and `buildability`.
15. **Journal plan items 3-7** take that plan’s recommendations (decision 19).
16. **Graphics scope.** AI-generated and AI-edited images are in v1 (`mode: generate`); they are the reason for the Gemini provider. Code-rendered output stays (`mode: command`).
17. **Graphics routing and sign-off.** `Route.kinds` is built now (`route-kinds-filter`); the visual judge decides and only an undecidable result parks; Gemini plan open decision 4 settles its release; until the `visual_baseline` GO is recorded, every graphics ticket parks.
18. **Graphics grading and libraries.** Three layers: deterministic checks (`image-quality-gate`), a vision-model judge on a rubric with structured output and majority sampling (`visual-review-surface`), best-of-N where only unsure cases park (`image-candidates-select`), calibrated against labels from an AI label panel of a model family other than the judge’s (§5, decision 13), with GO at 0.85 agreement (`visual-review-baseline`; amended 2026-11-16 by decision 19). Libraries ship as `clutch[images]` (Pillow, numpy, scikit-image, imagehash, opencv-python-headless) and `clutch[images-embed]` (open_clip, torch).


Decided 2026-11-16:

19. **No human in the loop.** Every gate and cadence counts runs or merged tickets, never wall-clock time. Every gate is a command, never a judgment a person makes. A prerequisite once run by a person becomes an agent-run capture committed under the dependent row's `tickets/<stem>/evidence/`; its plan says which agent action captures which facts. Escalations go through the supervisor and the diagnose path. A held stem or Author draft is released by the supervising agent loop executing the Recommendation of `clutch prompt diagnose <stem>` or `clutch prompt drafts` (`docs/roadmap-driver-plan.md` open decision 5). The only external input is a missing credential: skip a row needing one while an agent finds a route through authenticated providers; Gemini has no credential on this machine. Calibration and GO baselines use labels from an AI label panel of a different model family than the judge (§5, decision 13), never person-made labels; the `visual_baseline` GO gate is agreement with panel labels at 0.85 or above. A plan's open decision takes its Proposed option; the journal and upstream plans call it Recommendation and it counts as Proposed. Where none is proposed, a recorded AI design panel settles it before the dependent row is authored: three independent proposals and one judge, with the record committed as that row's evidence. A decision already settled by the owner or delegate needs no panel, as for driver plan open decision 5.

## 7. Plan document shape

Every plan under `docs/` has these sections in this order, so the next audit can read them mechanically: title; one-paragraph summary; `## Status` (one line: "Draft plan. Nothing in it is in effect and no ticket is authored. Written <date> at commit `<sha>`; revised <date> at commit `<sha>`."); `## Roadmap` (release slot, what it needs from other plans, what needs it, shared budgets it spends); `## Current state`; `## Departures from the design record` (when any); `## Target design`; `## Where each piece lives`; `## Ticket breakdown` with columns `# | Stem | Kind | P | Depends on | Content` and a `Runs before` sentence under the table; `## Risks`; `## Open decisions`. Stems are unique across all plans and this document, and none reuses a stem the journal already holds (`journal-sql-refactor-plan` is taken, rejected).

## 8. Master ticket table

Every proposed ticket, grouped by release and in priority order within a release. Row numbers are stable identifiers assigned in the order rows were added, not an ordering: the release sections and the `P` column order the work. "Owner" is the plan whose design the ticket implements; "roadmap" means the ticket comes from the audit above. `Depends on` lists only tickets whose merged code is needed; ordering that is not a dependency is in the `Runs before` column. Authoring follows `clutch new` and the authoring guide, and a row gains its link when it is authored (by the authoring agent today; by `roadmap author` once `docs/roadmap-driver-plan.md` lands).

Each release's ship gate (section 1) is also a fenced `gate` block under that release's first heading below. It has one argv command per line, no shell syntax, and runs from the checkout root. The gate passes when every command exits 0. `clutch roadmap gate <release>` runs it and journals the result. `clutch roadmap merged` is the query the blocks use. A later release's block checks only the suite and that release's rows: its other ship-gate clauses in section 1 have no command until merged code records their facts. The audit re-run before each minor release (section 9) adds to the next release's block a command for each such clause whose fact merged code now records.

### 0.3.0

| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |
|---|---|---|---|---|---|---|---|
| 1 | ~~`provider-capture-overwrite`~~ | roadmap (decision 4) | bug | P0 | | `evidence-store` | **Merged** (`tickets/provider-capture-overwrite/`). Instance fix: a stem's capture numbering continues from the highest `<provider>-NNNN` already on disk, read through a new `FileSystem.entries` seam method, so a later process never overwrites an earlier capture (`providers.py:294,325`). Evidence at `328d07d9`: 3,960 calls, 2,298 captures with `events.jsonl`. Keying by the journal call key is the cause fix in `evidence-envelope`. |
| 2 | ~~`provider-failure-single-mapper`~~ | roadmap | chore | P2 | | | **Merged** (`tickets/provider-failure-single-mapper/`). One provider-exception mapper in `runner.py`; delete the copy at `stages.py:1602-1615`. Its hard-coded `surface="requisition_review"` is unreachable: `Driver._run` maps `ProviderCallError` first with the right surface (`driver.py:324`), which a reproduction on 2026-11-14 confirmed (the Box report carried `stage=implement`). Dead duplicated code, not a live defect; demoted from the P0 bug the audit reported. |
| 3 | ~~`release-verb`~~ | journal plan (a) | feature | P1 | | | **Merged** (`tickets/release-verb/`). `clutch release --minor|--patch`: bumps `pyproject.toml`, commits, tags `v<version>`. |
| 4 | ~~`docs-truth-sweep`~~ | roadmap | chore | P1 | | | **Merged** (`tickets/docs-truth-sweep/`). Split in two: `docs-truth-sweep` (documents) and `docs-truth-sweep-code-strings` (code strings; `tickets/docs-truth-sweep-code-strings/`). Every row in section 4.1 and 4.2 that is a document fix; the `mergequeue.py` and `heartbeat.py` docstrings; the `redact.py` checklist; the `review` argparse help; `how-clutch-works.md` 10.1 and 10.2 gain the missing paths, the `checkpoint` type, and the signal-kind list. |
| 5 | ~~`conduct-files-parity`~~ | roadmap | chore | P1 | | `upstream-issue-verb` | **Merged** (`tickets/conduct-files-parity/`). `AGENTS.md` gains the four rules it lacks; CORE_TEMPLATE drops "(authoring, running, config contract)"; `clutch core` refreshes both blocks. |
| 6 | ~~`paved-roads-name-verbs`~~ | roadmap | chore | P1 | | | **Merged** (`tickets/paved-roads-name-verbs/`). Operator roads in `clutch/drain.py`, `clutch/status.py`, `clutch/doctor.py`, and `clutch/providers.py` name `clutch` verbs instead of `uv run python -m clutch` argv; the unknown-box-id refusal in `clutch/status.py` carries a road; a failed retro's `error_code` keeps the stage outcome; five `BoxError` sites name a repair. |
| 7 | ~~`dev-surface-completeness`~~ | roadmap | chore | P1 | | | **Merged** (`tickets/dev-surface-completeness/`). The launcher twins are superseded by `dev-py-dev-tasks-only`; `./dev.py test` loads `clutch.testguard` and `test-gate.toml`'s budget for `tests/unit`. |
| 8 | ~~`host-prompts-no-dev-py`~~ | roadmap (`box-000440`) | chore | P1 | | | **Not authored: already done at `73a41696`.** `clutch/specs/ask/*.md`, `host-authoring.md`, `host-qwen.md` render the host's verb prefix; `./dev.py` appears only in `README.md` and `how-clutch-works.md` §2.2. Superseded by `dev-py-dev-tasks-only`. |
| 9 | ~~`unit-criteria-disk-snag`~~ | roadmap (`box-000441`, `box-000442`) | feature | P1 | | | **Merged** (`tickets/unit-criteria-disk-snag/`). `requisition_review.md` snags a `tests/unit` criterion that needs disk, process, or network, with a road naming an in-fence seam; `diagnose.md` keeps floored lines reachable from `tests/unit`. |
| 10 | ~~`fence-closure-registries`~~ | roadmap (`box-000324`) | feature | P1 | | | **Merged** (`tickets/fence-closure-registries/`). `requisition_review.md:24` traces in-code registries and tables (menu keys, closed sets, adapter maps), not only symbol closure. |
| 11 | ~~`watch-surface-tier-truth`~~ | roadmap | bug | P1 | | | **Merged** (`tickets/watch-surface-tier-truth/`). `watch` shows the tier the code will use per surface (`observe.py:229-231`), or the code honors spec `tier:` for every surface; one truth. |
| 12 | ~~`redaction-harvest-seam`~~ | roadmap | chore | P1 | | | **Merged** (`tickets/redaction-harvest-seam/`). `harvest.json` passes the redactor; `redact.py` checklist matches the writers. |
| 13 | ~~`contention-authoring-rules`~~ | parallel plan 1 | chore | P1 | | every feature ticket below | **Merged** (`tickets/contention-authoring-rules/`). Section 7 of the parallel plan: new tests in new files, new fixtures in new modules, fence only what is forced, the do-not-grow list in `CLAUDE.md` and `AGENTS.md`. |
| 14 | ~~`fs-seam-mkdir-remove`~~ | roadmap | chore | P2 | | `evidence-store` | **Merged** (`tickets/fs-seam-mkdir-remove/`). `FileSystem` gains `mkdir` and `remove`; `enginelog`, `journal`, `stages`, `driver`, `scheduler.write_queue` use the seam. |
| 15 | ~~`active-slot-single-owner`~~ | roadmap | chore | P2 | | `serve-parallel-dispatch` | **Merged** (`tickets/active-slot-single-owner/`). `DaemonAdmission` owns the running set; `Scheduler._slot`, `TicketWriter.active`, `restart.mutating` read it; `serve.upgrade_idle` reads one thing. |
| 16 | ~~`merge-admission-single-owner`~~ | roadmap | chore | P2 | | `merge-model-resolve` | **Merged** (`tickets/merge-admission-single-owner/`). `merge.merge` becomes a thin call into `MergeQueue._admit` with the ladder, safety tier, receipt, tree check, and red streak as parameters; `gather_safety_evidence` runs once; one `refused` constructor; `served_review` stops swallowing. |
| 17 | ~~`host-check-selection-single-owner`~~ | roadmap | chore | P2 | | | **Merged** (`tickets/host-check-selection-single-owner/`). `triggered_hosts(tier=...)` is the one filter; `run_host_command` the one runner; the coverage parse and base `results` read stop swallowing. |
| 18 | ~~`journal-last-transition-helper`~~ | roadmap | chore | P2 | | | **Merged** (`tickets/journal-last-transition-helper/`). `journal.last_transition(events, stem)` replaces 13 scans; `Effects.recorded(key)` replaces six hand scans; `status.last_states` is the one fold observe and `__main__` use. |
| 19 | `closed-sets-single-home` | roadmap | chore | P2 | | `graphics-kind` | **Authored** (`tickets/closed-sets-single-home/`). Section 2.2 table: each set has one owner; argparse and `dev.py` derive choices; `NonBlank`, `_Strict`, path validators, spec-major, blob SHA become single helpers. |
| 20 | ~~`main-verb-groups`~~ | roadmap | chore | P2 | | | **Merged** (`tickets/main-verb-groups/`). `__main__.py` verb handlers grouped (utilities, projections, authoring, control, lock holders); one lock wrapper, one `_require_engine`, one `Context`, one error printer; `Checkout`/`StageContext` carry `log` and `box`; `Driver.from_config` takes the journal. |
| 21 | `test-fakes-and-conftest` | roadmap | chore | P2 | | | `tests/conftest.py` and `tests/fakes.py` with one clock, exec, filesystem, journal, and git fake and one `until`; `serve_rig.py` and the ten largest providers migrate; `test_merge.py:43` stops parsing another test's source. |
| 22 | `test-gate-floors` | roadmap | chore | P2 | | | **Authored** (`tickets/test-gate-floors/`). `clutch/graph.py` gains a floor; the eight floor-0 modules take their measured coverage as a ratchet. |
| 23 | ~~`lint-guide-parity`~~ | roadmap | chore | P2 | | | **Merged** (`tickets/lint-guide-parity/`). Every rule `tickets.py` lints is in `host-authoring.md`; the three guide rules lint can check (spec pin fenced on a version bump, document fenced on a behavior change, `## Depends on` ticket exists) are linted. |
| 24 | `extension-argv-from-snapshot` | roadmap | chore | P2 | | | **Authored** (`tickets/extension-argv-from-snapshot/`). Every verb the extension runs comes from an `observe.py` table; `clutchRoot()` uses the snapshot's root. |
| 25 | `dead-config-and-spec-fields` | roadmap | chore | P3 | | | Remove `caps.poison`, `review.trigger_map`, `ReviewSurface`; spec frontmatter `consumes`/`emits`/`gates` removed or wired; `requisition_review.md` `context` input removed; `host-contract.md` inventory follows. |
| 26 | `regress-scripts-guarded` | roadmap | chore | P3 | | | The ten `tests/regress_*.py` without a `__main__` guard get one; a test imports each script module and asserts nothing runs. |
| 27 | `host-onboarding-doc` | roadmap (P8 gap) | chore | P2 | `docs-truth-sweep` | | `clutch/docs/host-contract.md` gains "Onboarding a host" (checklist from install to first merge) and "Operating facts" (locks, state dir, upgrade, rollback). |
| 28 | `evidence-store` | evidence plan 2 | feature | P2 | `provider-capture-overwrite`, `fs-seam-mkdir-remove` | | Blob store, `clutch.evidence.*` schemas, strict writer, tolerant reader, JSON Schema generation, `evidence.max_gb` prune. |
| 29 | `evidence-envelope` | evidence plan 3 | feature | P2 | `evidence-store` | | `start.json`/`end.json` from `CliAdapter.invoke`; arrival times and rusage through the exec seam; tree ids through `git.py`; CLI version probe; `engine.log` stage events carry `call_key`; every reader of `spools/providers/` moves; the old writer is deleted. Cause fix for row 1. |
| 30 | `evidence-normalize-codex` | evidence plan 4 | feature | P2 | `evidence-store` | | Codex normalizer and golden fixture; pins whether `input_tokens` includes `cached_input_tokens`. |
| 31 | `evidence-normalize-claude` | evidence plan 5 | feature | P2 | `evidence-store` | | Claude normalizer and fixture; qwen reuses it flagged `unverified`. |
| 32 | ~~`gemini-provider`~~ | gemini plan A1 | feature | P2 | | | **Merged** (`tickets/gemini-provider/`). `GeminiAdapter`, two settings files, watchdog branch, live view, `host-gemini.md`; after its agent capture; skipped while this machine has no Gemini credential (decision 19). |
| 33 | `evidence-normalize-gemini` | evidence plan | feature | P3 | `evidence-store`, `gemini-provider` | | Gemini normalizer and fixture. |
| 34 | ~~`upstream-issue-verb`~~ | upstream plan 1 | feature | P2 | | | **Merged** (`tickets/upstream-issue-verb/`). `clutch issue` with five critical classes (decision 10), the CORE_TEMPLATE sentence (about 264 bytes), docs; after its agent capture. |

```gate
uv run clutch roadmap merged --release 0.3.0 --priority P0 P1
uv run clutch roadmap merged docs-truth-sweep evidence-envelope
uv run clutch roadmap merged --since v0.3.0 --at-least 3 --source box:roadmap_row --unattended
./dev.py test
```

### 0.3.0, last group: the roadmap driver

Runs after the rows above; it is what runs every later release (`docs/roadmap-driver-plan.md`).

| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |
|---|---|---|---|---|---|---|---|
| 88 | ~~`superseded-settles`~~ | driver plan 1 | bug | P1 | | | **Struck: premise false.** A published Rework split never reaches the Reject queue: `clutch/runner.py::failure_terminal` retires the parent through `reject_ticket` in the same second, so a `superseded` state would release nothing (box-000471, box-000472). The split parents a person killed by hand (`specs-in-package`, `vscode-help`, `vscode-help-registry`) were Rework splits that did not publish; they carry no `supersedes` signal (box-000473). |
| 89 | ~~`supervisor-rework`~~ | driver plan 2 | feature | P1 | | | **Merged** (`tickets/rework-supervise-gate/`, `tickets/supervise-cap-lineage/`). Rework-update on `premise_failed` and spent-cap terminals with the diagnosis lessons; allowed-edit gate (no goal or scope change); `caps.supervise`; supervisor keep that starts a new lineage; `rework.md` lifted on escalation. |
| 90 | ~~`roadmap-author`~~ | driver plan 3 | feature | P1 | | | **Merged** (`tickets/roadmap-row-message/`, `tickets/roadmap-table-parser/`, `tickets/roadmap-author/`). `roadmap_row` box message and policy row; `clutch/roadmap.py` table parser; `roadmap author --ahead N`; Author data blocks for the row and its plan; row linking and striking; capture refusal. |
| 91 | ~~`release-gates-as-commands`~~ | driver plan 4 | chore | P2 | | | **Merged** (`tickets/release-gates-as-commands/`). Fenced `gate` blocks per release in this document (every gate is a command); `clutch roadmap status`. |
| 92 | ~~`release-publish`~~ | driver plan 5 | feature | P2 | `release-verb` | | **Merged** (`tickets/release-publish/`). Publishing never bumps the version: `clutch publish` (PyPI, token env name in config) uploads the `pyproject.toml` version only when its `v<version>` tag is on HEAD, and refuses otherwise (box-000480; `./dev.py publish` bumps the patch first today, so a tagged release never reaches PyPI). `clutch release` (merged in `release-verb`) gains the `release` journal signal. `./dev.py vscode-publish` (Marketplace); publish only on `release.publish: true`, else nothing publishes. |
| 93 | ~~`driver-loop`~~ | driver plan 6 | feature | P1 | rows 89-92 | | **Merged** (`tickets/driver-loop/`). The idle-point sequence in serve and drain (supervise, author ahead, release when the gate passes, digest); the rewritten `drain-loop` prompt; how-clutch-works "Roadmap driver". |

### 0.4.0 (conditional)

| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |
|---|---|---|---|---|---|---|---|
| 35 | (re-measure) | journal plan | evidence | | | | Profile a drain start and `status` at the end of 0.3.0; the window runs only if journal reads still dominate. |
| 36 | `journal-query-layer` | journal plan (b) | feature | P2 | `release-verb` | | after its agent capture `tickets/journal-query-layer/evidence/re-measure.md`: DuckDB connection, bulk load, incremental insert, `duckdb` dependency. |
| 37 | `journal-ports-run-path` | journal plan (c) | chore | P2 | `journal-query-layer` | | `runner`, `stages`, `merge`, `mergequeue`, `rework`, `effects`, `driver`. |
| 38 | `journal-ports-loop` | journal plan (c) | chore | P2 | `journal-query-layer` | | `drain`, `serve`, `daemon`, `scheduler`, `timers`, `watcher`, `control`, `checkpoint`, `reconcile`. |
| 39 | `journal-ports-feedback` | journal plan (c) | chore | P2 | `journal-query-layer` | | `retro`, `triage`, `box`, `storm`, `flake`, `thresh`, `audit`, `notify`, `providers`. |
| 40 | `journal-ports-cli-authoring` | journal plan (c) | chore | P2 | `journal-query-layer` | | `__main__`, `author`, `tickets`, `observe` (its raw reader goes). |
| 41 | `journal-query-rule-gate` | journal plan (d) | chore | P2 | rows 37-40 | | The rule in `CLAUDE.md`/`AGENTS.md` and the lint that refuses `journal.read()` outside `clutch/journal.py`. |

```gate
uv run clutch roadmap merged --release 0.4.0
./dev.py test
```

### 0.5.0

| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |
|---|---|---|---|---|---|---|---|
| 42 | `parallel-config` | parallel plan 3 | feature | P2 | | | `scheduler.parallel` model, doctor warning, config table. |
| 43 | `fence-overlap` | parallel plan 4 | feature | P2 | | | `fences_overlap`, run-alone rule, `_in_fence` moved to `tickets.py`. |
| 44 | `chain-order` | parallel plan 5 | feature | P2 | | | `chain()`, parallel order, slot filling, starvation guard. |
| 45 | `serve-parallel-dispatch` | parallel plan 6 | feature | P2 | `parallel-config`, `fence-overlap`, `chain-order`, `active-slot-single-owner` | | Run set, slots, one eligibility filter, one `running` writer, host-command lock, idle checks. |
| 46 | `merge-model-resolve` | parallel plan 7 | feature | P2 | `merge-admission-single-owner` | | after its agent capture `tickets/merge-model-resolve/evidence/merge-conflict-facts.md`: `specs/resolve.md`, bounds, re-review of the resolution delta, `model` step value. |
| 47 | `conflict-discard-rerun` | parallel plan 8 | feature | P2 | `merge-model-resolve` | | Delete the Rework handoff; retire and re-offer; `prior-diff` lift; `implement.md` and `rework.md` bumps; rerun cap. |
| 48 | `status-hot-paths` | parallel plan 9 | feature | P3 | | | Hot-paths table in the snapshot and extension. |
| 49 | `graphics-kind` | gemini plan B1 | feature | P2 | `closed-sets-single-home` | | `kind: graphics` with `mode: command|generate`, `## Render`, `--reference` and `--input`, lint, authoring guide, CORE_TEMPLATE `|graphics` (9 bytes). |
| 50 | `graphics-render-check` | gemini plan B2 | feature | P2 | `graphics-kind` | `conflict-discard-rerun` | `command` mode render protocol at Check; `implement.md` block for both modes. |
| 51 | `route-kinds-filter` | gemini plan B3 | feature | P2 | | | `Route.kinds`, kind-aware `resolve()`, judge-independence warning in `doctor` and lint. |
| 52 | `image-quality-gate` | gemini plan B4 | feature | P2 | `graphics-kind` | | Layer 1: `clutch/images.py`, gate `image_quality`, the `images` and `images-embed` extras, side-by-side and heatmap artifacts. |
| 53 | `visual-review-surface` | gemini plan B5 | feature | P2 | `graphics-render-check`, `route-kinds-filter`, `image-quality-gate` | | Layer 2: `review_visual` spec with rubric, JSON schema, `graphics.judge_samples` majority. |
| 54 | `image-candidates-select` | gemini plan B6 | feature | P2 | `visual-review-surface` | | Layer 3: candidates in Implement, ranking, the select commit, `visual_undecided` park, its release (Gemini plan open decision 4). |
| 55 | `visual-review-baseline` | gemini plan B7 | feature | P2 | `visual-review-surface` | | `eval/visual/` fixtures labelled by an AI label panel of a model family other than the judge’s (§5, decision 13), `./dev.py visual-baseline`, the `visual_baseline` GO gate at 0.85 or above agreement with the panel’s labels. |
| (56) | `api-provider-client` | gemini plan (conditional) | feature | P2 | `gemini-provider` | `image-candidates-select` | Only if A0 fact 7 shows the CLI cannot generate images headlessly: the deferred `kind: api` client, scoped to image models. Row number is provisional. |

```gate
uv run clutch roadmap merged --release 0.5.0
./dev.py test
```

### 0.6.0

| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |
|---|---|---|---|---|---|---|---|
| 57 | `training-config` | training plan 1 | feature | P2 | | | `training_data: {enabled, exclude}` with the fixed exclude list; export refuses when off. |
| 58 | `training-attempt-manifest` | training plan 2 | feature | P2 | `training-config`, `evidence-envelope` | | Attempt manifest and full diff before worktree removal on every terminal. |
| 59 | `training-export` | training plan 3 | feature | P2 | `training-attempt-manifest` | | Record kinds, both formats, `--holdout`, scrub with drop count, provider-terms notice, `clutch training export`. The `conflict` kind lands with `merge-model-resolve` merged, else is skipped with a count. |
| 60 | `training-eval` | training plan 4 | feature | P3 | `training-export` | | Replay held-out records through a route; agreement scores. Decided to ship (decision 11). |
| 61 | `training-docs` | training plan 5 | chore | P3 | `training-export` | | Host guide: enabling, exclusions, provider terms, retrieval first. |
| 62 | `evidence-verbs` | evidence plan 6 | feature | P3 | `evidence-envelope`, rows 30-31 | | `evidence show`, `schema`, `renormalize`, `coverage`. |
| 63 | `spools-onto-evidence-store` | evidence plan 7 | chore | P3 | `evidence-envelope` | | Per-attempt `spools/<stem>/<attempt>/` move into the store; harvest, diagnosis, and the spool readers follow; one capture path (decision 12). |
| 64 | `one-parser-per-provider` | evidence plan 8 | chore | P3 | rows 30-31, `evidence-normalize-gemini` | | `CallMeter`, `Parsed`, and `live_call` read the normalized events; the adapter and watchdog parsers go (decision 13). |
| 65 | `panel-combiners` | panels plan 1 | feature | P2 | | `doc-review-runner` | `clutch/panel.py`: `findings-union`, `majority-verdict`, `best-of-n` over the existing artifact models; `panel_facts` body. Pure. |
| 66 | `panel-routing-config` | panels plan 2 | feature | P2 | `route-kinds-filter` | | `Route.panel {size, combine}`, surface-fit refusal, distinct-candidate assignment, `doctor` warning for single-slot providers. |
| 67 | `review-panel` | panels plan 3 | feature | P2 | `panel-combiners`, `panel-routing-config` | | Driver fan-out with member effect keys and evidence records; review, requisition review, diagnosis, and triage use the combined result. |
| 68 | `panel-scorecard` | panels plan 4 | feature | P3 | `review-panel` | | Per-member catch attribution; unique catches per 100 reviews and the cost multiplier in the retro report. |
| 69 | `meta-schema-and-refresh` | annotations plan 1 | feature | P2 | | | Six-key `clutch.meta/1.0` block for Markdown and Python, parser, hash, generated fields, `meta refresh` and `meta check`, `meta` config; fills this repo's blocks. |
| 70 | `meta-fill-surface` | annotations plan 2 | feature | P2 | `meta-schema-and-refresh` | | `specs/meta.md`, `meta fill` in batches, path validation, `verified` stamping. |
| 71 | `meta-drift-lint` | annotations plan 3 | feature | P3 | `meta-schema-and-refresh` | | Soft `meta_drift` gate; Check runs `refresh` on changed files and commits `clutch(<stem>): meta`. |
| 72 | `index-build` | annotations plan 4 | feature | P2 | `meta-schema-and-refresh`, `evidence-envelope` | | `clutch/index.py`: `files`, `chunks`, `embeddings` (host embed argv, VSS), `touches`, `calls`; incremental; post-merge build; adds `duckdb` if `journal-query-layer` has not. |
| 73 | `context-suggest` | annotations plan 5 | feature | P2 | `index-build` | | `clutch context suggest <stem>` and the Author data block. |
| 74 | `index-consumers` | annotations plan 6 | feature | P3 | `context-suggest` | | `index.implement_hint`, `doc draft --from <topic>`, the training export join. |

```gate
uv run clutch roadmap merged --release 0.6.0
./dev.py test
```

### 0.7.0

| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |
|---|---|---|---|---|---|---|---|
| 75 | `doc-facet-registry` | document plan 1 | feature | P2 | | | Facet format, loader, `clutch doc facets`, facet files. |
| 76 | `docset-manifest` | document plan 2 | feature | P2 | | | `clutch.docset/1.0`, section hashing, `clutch doc status` over any `docs/<name>/` with a manifest. |
| 77 | `isolated-readonly-call` | document plan 3 | feature | P2 | `evidence-envelope` | | Scratch working directory with only the declared files; evidence record with `repo: null`. |
| 78 | `doc-review-runner` | document plan 4 | feature | P2 | `doc-facet-registry`, `isolated-readonly-call`, `panel-combiners` | | `doc_review` surface over `specs/doc/lens.md`, stage runner on `clutch/panel.py`, accounting gate, report; panel default 3, minimum 2. |
| 79 | `doc-lenses-from-owner-prompts` | document plan 5 | feature | P2 | `doc-review-runner` | | `scope`, `viability`, `buildability`, `compression` facets from the owner's files. |
| 80 | `doc-lens-automatable` | document plan 6 | feature | P2 | `doc-review-runner`, `fence-overlap` | | The Automatable lens, mechanical ticket lint stage, automation ratio. |
| 81 | `doc-derive-fidelity` | document plan 7 | feature | P2 | `docset-manifest`, `doc-lenses-from-owner-prompts` | | `doc_derive`, fidelity gate by derive class. |
| 82 | `doc-fold-apply` | document plan 8 | feature | P2 | `docset-manifest`, `doc-derive-fidelity` | | `doc_fold`, `doc apply`, accept flow, `derive --stale`. |
| 83 | `doc-render` | document plan 9 | feature | P2 | `doc-facet-registry` | | Markdown to HTML with themes; PDF through host argv; `documents` config. |
| 84 | `doc-draft` | document plan 10 | feature | P2 | `doc-facet-registry`, `docset-manifest`, `context-suggest` | | Headless draft (with `--from <topic>` through the index) and the `doc-plan` ask prompt. |
| 85 | `doc-extension-menu` | document plan 11 | feature | P3 | `doc-fold-apply`, `doc-draft` | | Snapshot fields and menu items. |
| 86 | `plans-into-docsets` | document plan (decision 14) | chore | P3 | `doc-facet-registry`, `docset-manifest` | | Move the ten `docs/*.md` plans into doc sets and run `scope` and `buildability` on each; 0.7.0's ship gate. |
| 87 | `implement-best-of-n` | panels plan 5 | feature | P3 | `panel-combiners`, `serve-parallel-dispatch` | | Per-member worktrees, Check on every candidate, selection by Check pass then fewest soft findings then smallest diff, retirement of the rest. |

```gate
uv run clutch roadmap merged --release 0.7.0
./dev.py test
```

### Agent tasks (not tickets)

- For Gemini A0, an agent runs headless `gemini` per settings file with an empty `HOME`, saving stdout, stderr, exit code and live process argv for facts 1-8, and resolves the `images` and `images-embed` extras on Python 3.14 in a scratch venv, saving resolver output for fact 9. Commit the nine facts to `tickets/gemini-provider/evidence/`; skip the credential-dependent capture while the credential is missing.
- For GitHub prefill, an agent opens prefilled links of increasing body length in a headless browser, saving statuses and rendered fields for facts 1-2, then builds and installs the wheel non-editable in a scratch venv and saves metadata for fact 3. Commit to `tickets/upstream-issue-verb/evidence/`.
- For parallel A0, an agent reads the 13 `merge_conflict_facts` events from the journal and commits them as `tickets/merge-model-resolve/evidence/merge-conflict-facts.md`.
- For row 35, an agent profiles a drain start and `clutch status` at the end of the truth release, recording the share of wall time spent in journal reads, and commits `tickets/journal-query-layer/evidence/re-measure.md`.

## 9. Keeping this document true

- A ticket authored from a row links its stem in that row; a merged row is struck through, not deleted, until the release ships; a shipped release's rows move to a "Shipped" section at the end. Once `roadmap-author` lands, the driver makes these edits as ticket-plane commits; until then the agent that authors the row does.
- The audit (sections 2-4) is re-run before each minor release with the same six passes; rows that are fixed are removed, rows that recur are marked with the release that was supposed to fix them.
- Shared budgets (section 5, decision 5) and shared files (decision 8) are updated whenever a plan adds a ticket that touches them.
