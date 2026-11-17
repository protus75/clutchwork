# clutch roadmap

The one place that orders clutch's planned work. Each plan under `docs/` owns its own design; this document owns what the plans share: priority, release slot, cross-plan ordering, shared budgets, and the decisions that settle where plans overlap or contradict. It also carries the audit of the code and documents that the ordering rests on: what is duplicated, what is missing, and where the documents have drifted from the code.

A plan change that moves a ticket, adds a dependency on another plan, or spends a shared budget updates this document in the same change. A ticket authored from a row here is linked by stem in that row.

## Status

Audit refreshed at commit `14752dc5` (clutch `0.3.0`, extension `0.3.0`). The audit sections are a snapshot at that commit, produced by six read-only passes over `clutch/`, `tests/`, `dev.py`, `docs/`, `clutch/docs/`, `clutch/specs/`, `CLAUDE.md`, `AGENTS.md`, `README.md`, and `CLUTCH_PLAN.md` §18-19. Re-run the audit before each minor release; the section headings are the checklist.

Facts recorded in the original 2026-11-13 snapshot (counts were not re-measured):

- 506 tickets merged, 0 in flight, 0 confirmed and unrun. The queue is empty. One stem awaits a verdict in the Reject queue (`vscode-help`, `premise_failed`). Four stems are blocked in the journal with no ticket directory (`authoring-reading-specs`, `host-mechanical-check`, `phase7-continue`, `journal-sql-refactor-plan`).
- Four Suggestion Box messages are pending: `box-000324` (fence closure misses in-code registries; recurrence recorded in `tickets/retro/000046.md`), `box-000440` (operator prompts hard-code `./dev.py`), `box-000441` and `box-000442` (unit-test criteria that need disk pass requisition review, then fail Implement). None is a ticket yet.
- Spend to date $2,681.50. 5,090 commits since 2026-10-01.
- `CLUTCH_PLAN.md` phases P3-P6 are complete. P7 `host-review-surfaces` was refused instead of built (`config.py:308-309`). P8 `rules-render` (`core --check`, a start-command file) was dropped; `host-onboarding-doc` added the two host-contract sections.
- The CLI has 29 verbs (`clutch/__main__.py:237-287`) against the frozen plan's closed set of 16 (§18.1). Each arrived by ticket; the plan cannot be amended.

## 1. Release plan

Versions follow `pyproject.toml` (`0.3.0` today). Each release below is a minor version, named for the version `clutch release --minor` gives it: a phase is bumped and tagged at its start, so tag `v0.3.0` (`c761b213`) opened 0.3.0. These names were once one minor lower (0.3.0 was `0.2.0`), and older commits, tickets, and Suggestion Box messages use the old names. Each phase takes the next minor when it starts, so if the conditional 0.6.0 window slides, the phases after 0.3.0 are renamed to the versions they start at. `clutch release --minor|--patch` (`release-verb`, merged) bumps, commits, and tags; `./dev.py publish` still bumps the patch again before it uploads, which `release-publish` (row 92) replaces with a publish that never bumps.

| Release | Theme | Gate to start | Gate to ship |
|---|---|---|---|
| **0.3.0** | Truth, hygiene, shared infrastructure, and the roadmap driver (`docs/roadmap-driver-plan.md`) | none | every P0 and P1 row merged; evidence capture live; `docs-truth-sweep` merged so the next audit starts clean; the driver has authored and run at least three roadmap rows on this repo with no operator verdict |
| **0.4.0** | Parallel runs and the graphics kind (`docs/parallel-tickets-plan.md`, `docs/gemini-graphics-refactor-plan.md` Part B) | 0.3.0 dedup tickets merged (`active-slot-single-owner`, `merge-admission-single-owner`, `closed-sets-single-owner`); Gemini agent capture A0 committed (fact 7 decides `api-provider-client`) (unchecked); decision 19’s credential rule applies while this machine has no Gemini credential (unchecked) | parallel serve has merged the next 10 tickets with no conflict-rerun cap hit; one `generate` graphics ticket merged through the select commit; `visual_baseline` GO recorded |
| **0.5.0** | Training flywheel, stage panels, and the project index (`docs/training-data-plan.md`, `docs/stage-panels-plan.md`, `docs/annotations-index-plan.md`, evidence verbs) | evidence store has captured at least one full drain (unchecked) | `training export` produces every record kind from this repo's journal; `training eval` scores one lens; a two-member review panel has reviewed the next 10 tickets with its unique-catch count in the retro report; this repo's docs and tests carry filled meta blocks and `context suggest` returns selectors for a real ticket |
| **0.6.0** | Journal query layer (`docs/journal-sql-refactor-plan.md`) | re-measurement shows `clutch status` over 1 second or a drain start spending over 2 seconds in journal reads (unchecked) | all four port groups merged and the SQL-only gate in place; no feature ticket runs during the window |
| **0.7.0** | Document agent (`docs/document-agent-plan.md`) | isolated read-only calls proven by `isolated-readonly-call` (unchecked); the owner's lens prompts adapted (unchecked) | the three plans written on 2026-11-13 moved into doc sets and reviewed with `scope` and `buildability` |

The `start` block for 0.4.0 checks the three dedup tickets; clauses marked (unchecked) have no merged verb to check them. A release without a `start` block starts unconditionally.

Independent of release: `gemini-provider` and `upstream-issue-verb` land in 0.3.0 because they touch nothing the later releases reshape, and both wait on an agent-run capture committed as their evidence; their plans say which agent action captures which facts.

### 1.1 Why this order

- **Truth first.** The audit found 16 places where the maintained documents say something the code does not do, and a capture bug that has lost 1,662 of 3,960 raw model-call records (counted at `328d07d9`). None of the feature plans can be authored against documents that are wrong, and the training plan cannot capture data that is being overwritten.
- **Dedup before parallel.** Parallel runs change the one-run assumption in six separate trackers and the merge path in two separate implementations. Making each of those a single owner first turns the parallel tickets from a rewrite into an edit.
- **Capture early, export late.** The evidence store (0.3.0) only has value once it holds data. Export and eval (0.5.0) are useful on day one if capture started three releases earlier.
- **Journal window is conditional.** Its measured trigger (157 of 164 seconds in journal reads) predates `journal-incremental-read`. The refactor freezes features for a release; it earns that only if re-measurement shows the cost is still there.
- **Document agent last.** It is the largest new surface, depends on the isolated-call mode and the evidence record, and its first real use is reviewing the other plans, which is more useful once those plans have tickets behind them.

## 2. Analysis: duplication

Ranked by how many later tickets it blocks. Every item names the single owner that should remain.

### 2.1 Engine core

| # | Duplicated | Locations | Owner after fix | Ticket |
|---|---|---|---|---|
| 7 | Eligibility filter: `Scheduler.dispatch_next` (`scheduler.py:50-76`) and `_Drain._select` (`drain.py:508-558`) both compute `settled_dependencies`, `supersedes_maps`, `authored_at`, `parked_blob`, `reofferable`, then `order_tickets` + `write_queue`; drain adds `depends_cycle`, over-budget, storm, drought | as listed | one `eligible(events, tickets, ...)` in `drain.py`, consumed by `Scheduler` | `serve-parallel-dispatch` (it rewrites `dispatch_next` anyway) (recurred in 0.3.0) |
| 9 | `running` transition + reoffer written by three callers: `runner.run_ticket:525-526`, `drain._run_one:571-574`, `serve.py:150-154` | as listed | `runner.run_ticket` | `serve-parallel-dispatch` (recurred in 0.3.0) |
| 10 | `EngineLog` and `storm_producer` are constructed at multiple call sites (`runner.py`, `drain.py`, `serve.py`, `triage.py`, `driver.py`). | as listed | Share the construction where appropriate | `main-verb-groups` (constructor work remains) (recurred in 0.3.0) |
| 13 | Fence matching: owner `stages._in_fence` (978-979); re-implemented at `watchdog.py:60`, `drain.py:484` (different semantics: trailing-slash dirs only), raw `startswith(f"{TICKETS_DIR}/")` at `merge.py:108,248,385`, `stages.py:1224` | as listed | `_in_fence`, moved to `clutch/tickets.py` (the fence grammar's home) | `fence-overlap` (it adds the pure overlap function beside it) (recurred in 0.3.0) |

### 2.2 Closed sets with more than one home

| Set | Homes | Owner |
|---|---|---|
| Settled and retired states | `status.py:17` `SETTLED`, `drain.py:53` `RETIRED`, `stats.py:11` `SETTLED` (same name, different set), `tickets.py:711` literal; `SETTLED | {"rejected"}` spelled out 15 times, `SETTLED | RETIRED` 8 times | `status.CLOSED = SETTLED | RETIRED`; `stats.SETTLED` deleted (recurred in 0.3.0) |
| Failed-attempt terminals | `caps.py:48`, `scorecard.py:85`, `journal.py:101`, `stats.py:122` | `journal.py` (recurred in 0.3.0) |
| Surfaces | `specs/__init__.py:32` (8), `observe.py:33-44` (10), `stats.py:12` (6), `observe.py:274,814`, `providers.py:29`, `policy.py:14` | `specs/__init__.py`; observe and stats derive (recurred in 0.3.0) |
| Spike kinds | `config.py:23` owner; `clutch/docs/host-contract.md` repeats the list at lines 133, 193, 202, 206 | `config.py`; the contract lists it once (recurred in 0.3.0) |
| Box classes and policy rows | `box.py:18`, `config.py:25-49`, `policy.py:33-45`, `host-contract.md:134,213`, `specs/triage.md:20-28` | `box.py` (classes), `config.py` (rows), `policy.py` the only bridge (recurred in 0.3.0) |
| Triage verdicts | `triage.py:33`, `box.py:63,69,403` (three overlapping Literals in one file) | `box.py` (recurred in 0.3.0) |
| Control verbs | `control.py:16,72`, `__main__.py:254-257`, `lockfile.py:19`, `observe.py:835-842` | `control.py` (recurred in 0.3.0) |
| Ask kinds | `ask.py:11` owner; `__main__.py:398-421` branches per literal; `observe.py:527-529` hand-lists three menu entries | `ask.py` (recurred in 0.3.0) |
| Finding codes | `ticket_schema` at `tickets.py:30`, `author.py:39`, `rework.py:66`; `requisition_review`/`requisition_rma` at nine sites; `core_drift` at `hostfiles.py:192,205,214` | `gates.ENGINE_GATE_CODES` plus one registry for stage finding codes (recurred in 0.3.0) |
| Conduct-file routing `{claude, qwen}` -> `CLAUDE.md` | `providers.py:131`, `host-contract.md:274`, `how-clutch-works.md:756` | `providers.py`; docs cite it (recurred in 0.3.0) |

Ticket: `closed-sets-remaining`.

### 2.3 Repeated helpers and projections

- Retro-recurrence reopen boundary: `author.py:159-161,179-181`, `triage.py:263-270`. (recurred in 0.3.0)
- `requisition_verdict` signal body built by hand: `__main__.py:643-655`, `author.py:360-364`, `rework.py:169-180`, `runner.py:199`. `ticket_intake` body: `tickets.py:768` uses `INTAKE_SIGNAL`, `author.py:359` a literal. (recurred in 0.3.0)
- Scorecard table builders in `status.py` and `retro.py` duplicate the header and row formatting, though the retro table includes an extra blank line. (recurred in 0.3.0)
- Literal `"box"` instead of `BOX_DIR` at `__main__.py:80,460`, `author.py:74`, `ask.py:24`, `observe.py:757`; `f"tickets/{stem}/ticket.md"` instead of `ticket_path()` at `__main__.py:141`, `triage.py:201`, `observe.py:240,678,687`. (recurred in 0.3.0)
- Last-state fold: `status.py:58-60` canonical; re-implemented at `observe.py:395-398,604-607,552`, `__main__.py:128,160-162,431`, `providers.py:244`. `observe.journal()` returns dicts, so `observe` wraps them in `SimpleNamespace` four times to call Event-typed helpers. (recurred in 0.3.0)
- Attempt counting with three semantics: `caps.py:54-56`, `observe.py:403`, `stats.py:112`. Spend sum at `status.py:194`, `stats.py:130-131`, `retro.py:151,160`. (recurred in 0.3.0)
- Frontmatter read by regex outside the owner: `observe.py:218-224,278-281`, `retro.py:228` (duplicates `tickets.py:82` `_BUDGET`), `__main__.py:789-792`. (recurred in 0.3.0)
- `"cap spent"` produced by `caps.py:108` and parsed back by `observe.py:315`. `provider_drought` body probed at 14 sites. (recurred in 0.3.0)

The projection and constructor duplication remains after `journal-last-transition-helper` and `main-verb-groups`.

### 2.4 Provider stream parsing

`ClaudeAdapter.parse` (`providers.py:465-479`) and `CodexAdapter.parse` (493-511) read the terminal event and usage; `watchdog.CallMeter._consume` (85-126) re-parses the same fields with its own guards; `observe.live_call` (189-215) re-encodes the adapters' argv by regex over `ps` output. `docs/evidence-trail-plan.md` makes the per-provider normalizer the single parser and lists moving `CallMeter` and `Parsed` onto it as a follow-up once normalizers have run on real traffic. (recurred in 0.3.0)

### 2.5 Rules stated in more than one home

Second problems to the Box and verify at base (`hostfiles.py:55`, `CLAUDE.md:90-91`, `AGENTS.md:84-85`, `specs/implement.md:24-26,133-134`); read before write (`hostfiles.py:56`, `CLAUDE.md:92-93`, `AGENTS.md:86-87`); smallest change (`hostfiles.py:52`, `CLAUDE.md:72-73`, `AGENTS.md:68-69`, `implement.md:23-24`); never push (`hostfiles.py:44,54`, `CLAUDE.md:88-89`, `implement.md:56-58`); never hand-edit the managed block (`hostfiles.py:53`, `CLAUDE.md:82-83`, `host-contract.md:272`); the set-membership grep rule verbatim in `host-authoring.md:55` and `specs/requisition_review.md:24`; the bug-evidence refusal sentence three times (`host-authoring.md:88-92`, `how-clutch-works.md:148-151,315-318`); unit-test discipline in `implement.md:60-68`, `review.md:37-39`, `retro.md:24`, `how-clutch-works.md:225-229`. (recurred in 0.3.0)

The `CLAUDE.md` rule "a rule has one of two homes" is the fix; `conduct-files-parity` aligned the conduct files; the remaining restatements need review. Specs may restate a rule the model needs; documents may not.

### 2.6 Tests

- Several test modules double as fixture libraries; `test_drain.py:30-33` imports and calls a test function from `test_merge.py` as its body; `test_merge.py:43` reads `test_stages.py` as text and slices its `CONFIG` literal out. (recurred in 0.3.0)
- Shared clock, exec, filesystem, journal and git fakes now live in `tests/fakes.py`; other local fakes still exist (for example `tests/integration/test_mergequeue.py`). (recurred in 0.3.0)
- `tests/waiting.py` provides `until`; local fixture builders such as `repo()` and `git()` still appear in multiple test modules. (recurred in 0.3.0)
- `CONFIG` and `TICKET` literals, configuration writes and git-init sequences appear across test modules. (recurred in 0.3.0)
- The do-not-grow rule is in `CLAUDE.md` section A and `AGENTS.md` `## Engine conduct` (`contention-authoring-rules`, done). It names seven files: the five measured at `80b76d5d` (`test_daemon_composition.py`, `test_drain.py`, `test_mergequeue.py`, `test_stages.py`, `serve_rig.py`), which took 53 commits in the 13 days to 2026-11-13, and `tests/integration/test_cli.py` and `tests/integration/test_watch.py`, added when the list was re-measured at `c761b213`. (recurred in 0.3.0)

Tickets: `test-fakes-and-conftest`, `contention-authoring-rules` (done).

## 3. Analysis: gaps

### 3.1 Defects found by the audit

The listed defects were fixed by the 0.3.0 tickets.

### 3.2 Seams bypassed

`fs-seam-mkdir-remove` added the missing filesystem operations and moved the listed callers onto the seam.

### 3.3 Deferred items whose trigger has fired

| §18.2 item | Trigger | Fired | Decision |
|---|---|---|---|
| Mechanical scope-fence closure analyzer | first fence-gap escape `requisition_review` misses | twice: `box-000324` (three rejects), recurrence in `tickets/retro/000046.md` proposal 2 (`test_menu_verb_parity.py:185`) | Decided (section 6, decision 1): 0.3.0 widens the prompt rule to in-code registries (`fence-closure-registries`); a third escape schedules a spike for the mechanical analyzer in 0.4.0 (recurred in 0.3.0) |
| DuckDB analytics | first projection measured too slow as a fold | yes, 157 of 164 seconds (`tickets/journal-incremental-read/evidence/`), before the incremental reader merged | re-measure; 0.6.0 is conditional on it (recurred in 0.3.0) |
| Triage-dedup real-model eval | daemon-era entry | yes, serve has run since the daemon era | not scheduled; `training-eval` (0.5.0) covers triage records and makes this the first lens to score (recurred in 0.3.0) |
| Concurrent worker pool, dispatch overlap skip | measured starvation post-cutover | not fired; owner chose to bring it back for contention, not starvation | 0.4.0, declared in `docs/parallel-tickets-plan.md` (recurred in 0.3.0) |
| Conflict-only micro-rework | first chronically re-resolved conflict in `merge_conflict_facts` | 13 events exist; nobody has read them | `merge-model-resolve` starts by reading them (its plan's A0) (recurred in 0.3.0) |

### 3.4 Never built, no ticket

- P8 `rules-render`: `clutch core --check` and a start-command file. `doctor` has a `core` drift row (`doctor.py:67-73`); `serve`, `drain`, `run` refuse on stale blocks. Decided 2026-11-13: dropped (section 6, decision 2). (recurred in 0.3.0)
- `kind: api` provider: refused at `config.py:460-465`; stays deferred. (recurred in 0.3.0)

### 3.5 Dev surface and tests

- Engine verbs such as `covgate`, `doctor`, `retro`, and `snapshot` have no `./dev.py` subcommand; `dev-py-dev-tasks-only` leaves engine tasks to `clutch` verbs. (recurred in 0.3.0)
- `tests/vscode_task_identity.js` is referenced by the regression script `tests/regress_vscode_task_identity.py`, not a regular test. (recurred in 0.3.0)
- `vscode-clutchwork/extension.js::clutchRoot` chooses the workspace by probing for `tickets/`; `extension-argv-from-snapshot` moved verb argv to the snapshot but did not change this lookup. (recurred in 0.3.0)
- Spec frontmatter `tier` is used by retro and acceptance (`clutch/retro.py`, `clutch/acceptance.py`), while other stage calls do not use it. (recurred in 0.3.0)
- No engine caller: `heartbeat.is_fresh`, `Timers.wait_next`, `Git.branch`, `Git.init`, the `effects.effect` decorator, `gates.lint_gate`, `providers.CliAdapter.parsed_failure`, `requisition.RequisitionGate`, `requisition.base_render_chars`, `observe.uncommitted_tickets` (20+ tests monkeypatch it), `policy.baseline_identity`, `audit.audit`, `watchdog.Detector.watch`. Untested production paths: `mergequeue.retained_ticket`, `serve.Responsiveness`, `runner.PreparedDispatch`. (recurred in 0.3.0)

Tickets: `dev-surface-completeness`, `regress-scripts-guarded`, `test-gate-floors`, `lint-guide-parity`, `extension-argv-from-snapshot`, `dead-config-and-spec-fields`.

## 4. Analysis: drift

Every row is a claim the owning document makes that the code contradicts. `docs-truth-sweep` fixes each by changing the document to the code's behavior, except where the row names a code ticket.

### 4.1 `docs/how-clutch-works.md`

The listed claims were corrected by `docs-truth-sweep` and the associated code tickets.

### 4.2 Other documents

The listed claims were corrected by `docs-truth-sweep` and the associated tickets.

### 4.3 Plan documents

The listed plan-document drift was fixed in the previous audit revision.

## 5. Cross-plan decisions

Each decision settles a place where two plans overlapped or contradicted. The plans are revised to match; a plan that wants to change one of these changes it here first.

1. **One call-record store.** `<state_dir>/evidence/` (`docs/evidence-trail-plan.md`) is the only store for model-call records. The training plan adds attempt manifests, export, and eval on top of it and owns no store of its own. `spools/providers/` is replaced by the evidence store in `evidence-envelope`; the per-attempt `spools/<stem>/<attempt>/` (prompt, output, check output) stays until a later ticket moves it, which no plan schedules.
2. **Capture always on, training gated.** The envelope and raw stdout/stderr are captured for every call, as `spools/providers/` is today, because diagnosis and harvest read them. Retention is `evidence.max_gb` (default 20; evidence plan). Attempt manifests with full diffs, export, and eval are behind `training_data.enabled` (default false; training plan). `training_data.dir` is dropped: the store location is fixed.
3. **Record identity.** A record's id is the journal effect key. Ticketless calls key under their surface name (`driver.py:274`), so `stem` is nullable and `group` is the stem or, for triage, author, retro, and document lenses, the surface. Isolated calls (document agent) record `repo: null` and `process.cwd` as the scratch directory; no conduct file is loaded and the record says so.
4. **One P0 for the capture bug.** `provider-capture-overwrite` is a single bug ticket owned by this roadmap. Its cause fix, under the CORE two-ticket rule, is `evidence-envelope` (every capture path keyed by the journal identity of what it captures). Both plans cite the stems; neither owns them.
5. **CORE_TEMPLATE byte ledger.** 8,109 of 8,192 bytes used (row 103; `tests/integration/test_hostfiles.py:33`). Any further template text first compresses a rule that has gained its gate (`CLAUDE.md:57`).
6. **Names.** The document agent's config block is `documents:` (not `docs:`, which is a verb and a directory). Its lens spec is `clutch/specs/doc/lens.md` (not `review.md`, which exists at `clutch/specs/`). Its specs carry the spec frontmatter that `tests/unit/test_specs.py:24` checks on everything under `clutch/specs/`.
7. **Journal window.** 0.6.0 runs only on re-measurement. Its port tickets touch the same files as `serve-parallel-dispatch` and `conflict-discard-rerun`, so the parallel tickets land after the window, or before it if the window slides. Several runs in one process appending to the journal is compatible with the query layer's per-process offset because `journal.lock` serializes appends; the journal plan states this.
8. **Shared files between plans.** `graphics-render-check` and `conflict-discard-rerun` both bump `clutch/specs/implement.md`; `graphics-render-check` runs first (it heads the longer chain). `upstream-issue-verb` (0.3.0) and `graphics-kind` (0.4.0) both edit `hostfiles.py`, `CLAUDE.md`, `AGENTS.md`, `README.md`; releases separate them. `gemini-provider`, `evidence-envelope`, `isolated-readonly-call`, and the journal ports all fence `clutch/providers.py`; under the parallel plan's own overlap rule they serialize, which the release slots already arrange.
9. **Design-record departures are declared.** A plan that re-opens a `CLUTCH_PLAN.md` §18 item names the item, the trigger, and the owner decision in a "Departures from the design record" table. The parallel plan already did; the training, evidence, and document plans now do (audit trail and blob store, §18.1; metadata taxonomies, §18.1). The owner's decision of 2026-11-13 is the cited incident.
10. **Host-command lock.** The parallel plan's engine-wide semaphore around `run_host_command` also serializes the graphics plan's render command and the merge queue's host checks. One lock, stated in both plans.
11. **The mergequeue docstring** was fixed by `docs-truth-sweep-code-strings` (done), not by a parallel-plan ticket; that plan's row 2 now points at the roadmap's `active-slot-single-owner` and `merge-admission-single-owner`, the two 0.3.0 chores its dispatch and merge tickets depend on.
12. **Optional dependencies.** The graphics plan's image libraries ship as the extras `clutch[images]` and `clutch[images-embed]`, imported lazily by `clutch/images.py`; core clutch gains no dependency. A later plan that needs a heavy library follows the same shape. The journal plan's `duckdb` is the one core dependency a plan adds, earned by D3's named trigger.
13. **Generator and judge are different models.** Any surface that judges a model's output (`review_visual` now; a future image or audio judge) routes to a different model family than the surface that produced it; `doctor` warns and lint snags when a config breaks that. The owner's 2026-11-14 note on the Gemini models is the incident: image models answer with pictures, and a model grading its own family grades kindly.
14. **One panel mechanism.** Running a stage as several independent calls and combining them is `docs/stage-panels-plan.md`'s `clutch/panel.py`, declared per routing row. The document agent's `doc-review-runner` depends on `panel-combiners` instead of building its own; the graphics judge's `judge_samples` majority is the `majority-verdict` combiner. No plan adds a second fan-out.
15. **The index is a cache.** `<state_dir>/index.duckdb` (`docs/annotations-index-plan.md`) is derived and rebuildable, read by no gate and no dispatch. `duckdb` enters `pyproject.toml` once, with whichever of `journal-query-layer` or `index-build` lands first, under D3's named trigger. clutch ships no embedding model; vectors come from a host-declared command.
16. **The driver's authority.** The roadmap driver (`docs/roadmap-driver-plan.md`) may edit a held ticket only through a reviewed Rework-update within the supervising rules, may keep it at most `caps.supervise` times per operator lineage, authors at most `--ahead` rows past the running set, and publishes only under `release.publish: true`. Sessions never push on their own. The supervising agent loop confirms or rejects only by executing a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation (driver plan open decision 5). box-000508 was declined; row 103 (`core-template-supervisor-verdicts`) owns the change and has merged.
17. ~~**Superseded is settled.** A split's parent enters a settled state `superseded` and leaves the Reject queue by itself; the three historical parents rejected by hand are the incident.~~ Struck: the premise is false. A published Rework split never reaches the Reject queue: `clutch/runner.py::failure_terminal` journals the parent's terminal without `routed` and retires it through `reject_ticket` in the same second (box-000471). The split parents a person killed were Rework splits that did not publish, and they carry no `supersedes` signal (box-000473).

## 6. Owner decisions (decided 2026-11-13)

Decided by the owner in chat on 2026-11-13. Each plan's "Open decisions" section records its decisions; later decisions below amend them.

1. **Mechanical fence-closure analyzer** (§18.2; trigger fired twice). Decided: instructions first. `fence-closure-registries` (0.3.0) widens the reviewer prompt to in-code registries and tables. A third escape schedules a bounded spike for the mechanical checker in 0.4.0.
2. **P8 `core --check` and start-command file.** Decided: dropped. `doctor`'s `core` row and the start refusal cover drift detection; no host has asked for a start-command file. Both are recorded here as not built on purpose and are tracked nowhere else.
3. **Settled-ticket archive.** 537 directories under `tickets/`. Decided: nothing until a scan (lint with no stems, intake, the snapshot) is timed and found slow; the timing is filed as evidence when it happens.
4. **Split the do-not-grow test files.** Decided: the do-not-grow rule lands in 0.3.0 (`contention-authoring-rules`, done; it names seven files, the five measured at `80b76d5d` plus `tests/integration/test_cli.py` and `tests/integration/test_watch.py` measured at `c761b213`); splitting is chore tickets, one per file, during the 0.6.0 window if it runs, else in 0.4.0 before parallel runs start.
5. **Parallel plan.** Decided: `serve` only; longest-chain ordering below P0 only (P0 keeps the emergency lane); conflict reruns have their own cap `CONFLICT_RERUN_LIMIT = 2` and never draw `retry`.
6. **Training plan.** Decided: the export includes the full normalized tool-call trajectory (a per-run flag can trim it); Author-written tickets are included, tagged `authored_by: author`.
7. **Evidence plan.** Decided: providers' own session transcripts are not copied, only their ids are recorded; Claude thinking text is stored as a blob with `visibility: text`.
8. **Document plan.** Decided: `diverse: false` by default (same model per panel, `--diverse` per run); host-defined lenses and facets allowed as data inside the engine frame; commands only, no `doc` ticket kind in v1.
9. **Journal plan.** Decided: DuckDB; the SQL-only rule goes in `CLAUDE.md` and `AGENTS.md` with a lint gate that lands in the last port ticket and carries a named allowlist for the folds that stay Python.
10. **Upstream issue plan.** Decided: five critical classes. The proposed four plus `wrong-refusal`: clutch refuses valid input (config, ticket, intake) with a message whose paved road cannot be followed.

Decided 2026-11-14, from the plans' remaining open items:

11. **Training eval.** Ships in clutch (`training-eval`, 0.5.0); it doubles as the deferred triage-dedup eval.
12. **Per-attempt spools.** Move onto the evidence store later: `spools-onto-evidence-store` (0.5.0), after the store has run a release.
13. **One parser per provider.** `CallMeter`, `Parsed`, and `live_call` move onto the evidence normalizers after a release of real traffic: `one-parser-per-provider` (0.5.0).
14. **Document agent.** Doc sets are any `docs/<name>/` with a `docset.yaml`, found by search; panels default 3, minimum 2; the plans written 2026-11-13 become the first doc sets once `doc-facet-registry` and `docset-manifest` merge, reviewed with `scope` and `buildability`.
15. **Journal plan items 3-7** take that plan’s recommendations (decision 19).
16. **Graphics scope.** AI-generated and AI-edited images are in v1 (`mode: generate`); they are the reason for the Gemini provider. Code-rendered output stays (`mode: command`).
17. **Graphics routing and sign-off.** `Route.kinds` is built now (`route-kinds-filter`); the visual judge decides and only an undecidable result parks; Gemini plan open decision 4 settles its release; until the `visual_baseline` GO is recorded, every graphics ticket parks.
18. **Graphics grading and libraries.** Three layers: deterministic checks (`image-quality-gate`), a vision-model judge on a rubric with structured output and majority sampling (`visual-review-surface`), best-of-N where only unsure cases park (`image-candidates-select`), calibrated against labels from an AI label panel of a model family other than the judge’s (§5, decision 13), with GO at 0.85 agreement (`visual-review-baseline`; amended 2026-11-16 by decision 19). Libraries ship as `clutch[images]` (Pillow, numpy, scikit-image, imagehash, opencv-python-headless) and `clutch[images-embed]` (open_clip, torch).


Decided 2026-11-16:

19. **No human in the loop.** Every gate and cadence counts runs or merged tickets, never wall-clock time. Every gate is a command, never a judgment a person makes. A prerequisite once run by a person becomes an agent-run capture committed under the dependent row's `tickets/<stem>/evidence/`; its plan says which agent action captures which facts. Escalations go through the supervisor and the diagnose path. A held stem or Author draft is released by the supervising agent loop executing the Recommendation of `clutch prompt diagnose <stem>` or `clutch prompt drafts` (`docs/roadmap-driver-plan.md` open decision 5). The only external input is a missing credential: skip a row needing one while an agent finds a route through authenticated providers; Gemini has no credential on this machine. Calibration and GO baselines use labels from an AI label panel of a different model family than the judge (§5, decision 13), never person-made labels; the `visual_baseline` GO gate is agreement with panel labels at 0.85 or above. A plan's open decision takes its Proposed option; the journal and upstream plans call it Recommendation and it counts as Proposed. Where none is proposed, a recorded AI design panel settles it before the dependent row is authored: three independent proposals and one judge, with the record committed as that row's evidence. A decision already settled by the owner or delegate needs no panel, as for driver plan open decision 5.
20. **Marketplace publishing is manual** (owner, 2026-11-17). The release step keeps each release's VS Code package under `dist/`, one file per version, and never uploads it; the owner publishes it by hand. Row 92's `./dev.py vscode-publish` is dropped, and row 108 builds the kept package. PyPI publishing stays behind `release.publish` (default false).
21. **The journal window is deferred** (owner, 2026-11-17). `journal-incremental-read` cut its trigger's cost about 80x (`tickets/journal-query-layer/evidence/re-measure.md`: a drain start reaches admission in about 2 seconds and `status` takes about 0.4 seconds), while the share rule keeps firing because `status` is mostly a journal read by nature. The window slides behind the training release, as `docs/journal-sql-refactor-plan.md` allows, and its start gate becomes an absolute cost: it starts only when a re-measurement shows `clutch status` over 1 second or a drain start spending over 2 seconds in journal reads, and otherwise slides again. Row 111 renames the releases to the versions they now start at.
22. **Tickets are small** (owner, 2026-11-17). A ticket estimated over 30 minutes is split into more tickets when it is authored, unless the ticket states a reason it cannot be; over 60 minutes it is always split. Its stuck budget, the kill, is exactly twice the estimate. On 2026-11-16 and 2026-11-17 the medium Implement tier quit eight wide tickets within minutes, with budgets of up to 180 minutes allowed.

## 7. Plan document shape

Every plan under `docs/` has these sections in this order, so the next audit can read them mechanically: title; one-paragraph summary; `## Status` (one line: "Draft plan. Nothing in it is in effect and no ticket is authored. Written <date> at commit `<sha>`; revised <date> at commit `<sha>`."); `## Roadmap` (release slot, what it needs from other plans, what needs it, shared budgets it spends); `## Current state`; `## Departures from the design record` (when any); `## Target design`; `## Where each piece lives`; `## Ticket breakdown` with columns `# | Stem | Kind | P | Depends on | Content` and a `Runs before` sentence under the table; `## Risks`; `## Open decisions`. Stems are unique across all plans and this document, and none reuses a stem the journal already holds (`journal-sql-refactor-plan` is taken, rejected).

## 8. Master ticket table

Every proposed ticket, grouped by release and in priority order within a release. Row numbers are stable identifiers assigned in the order rows were added, not an ordering: the release sections and the `P` column order the work. "Owner" is the plan whose design the ticket implements; "roadmap" means the ticket comes from the audit above. `Depends on` lists only tickets whose merged code is needed; ordering that is not a dependency is in the `Runs before` column. Authoring follows `clutch new` and the authoring guide, and a row gains its link when it is authored (by the authoring agent today; by `roadmap author` once `docs/roadmap-driver-plan.md` lands).

A release may also have a fenced `start` block under its heading, with the same command and passing rules as a `gate` block. The driver and `clutch roadmap status` check it before readying rows; it writes no gate signal.

Each release's ship gate (section 1) is also a fenced `gate` block under that release's first heading below. It has one argv command per line, no shell syntax, and runs from the checkout root. The gate passes when every command exits 0. `clutch roadmap gate <release>` runs it and journals the result. `clutch roadmap merged` is the query the blocks use. Every block ends with `uv run clutch roadmap accept <release>`, after the `roadmap merged` checks and the suite: a model reviews the release's merged rows, taken together, against its theme and ship gate in section 1 and its owning plans' Target design, and appends a P1 row for each partial or unmet promise to the release's table (or, for a gap that should wait, to the next release's table) in a `clutch(roadmap): accept <release>` commit, so the gate fails until those rows merge. A later release's block checks only the suite, that release's rows, and the acceptance review: its other ship-gate clauses in section 1 have no command until merged code records their facts. The audit re-run before each minor release (section 9) adds to the next release's block a command for each such clause whose fact merged code now records.

### 0.3.0

Rows 94-107 come from the 0.3.0 acceptance review of 2026-11-16, which read the merged rows, taken together, against section 1 and the owning plans, and from the owner's requests made with it. Each is P0 or P1, so the gate's first command waits on them.

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
| 19 | ~~`closed-sets-single-owner`~~ | roadmap | chore | P2 | | `graphics-kind` | **Merged** (`tickets/closed-sets-single-owner/`). Section 2.2: tiers, priorities and kinds have one owner, including tier copies in `__main__.py` and `providers.py` and kind copies in `__main__.py` and `stats.py`; name a follow-up row for the remaining sets. `NonBlank`, `_Strict`, path validators and blob SHA become single helpers; preserve the final newline in `AuthorReply.ticket` despite `NonBlank` stripping whitespace. Use `stages._major`, called three times, as the one helper for the other spec-major sites; fence `serve.py`, which imports `stages.ticket_blob`. Leave the CORE_TEMPLATE `--kind` list as it is (decision 5). |
| 20 | ~~`main-verb-groups`~~ | roadmap | chore | P2 | | | **Merged** (`tickets/main-verb-groups/`). `__main__.py` verb handlers grouped (utilities, projections, authoring, control, lock holders); one lock wrapper, one `_require_engine`, one `Context`, one error printer; `Checkout`/`StageContext` carry `log` and `box`; `Driver.from_config` takes the journal. |
| 21 | ~~`shared-test-fakes`~~ | roadmap | chore | P2 | | | **Merged** (`tickets/shared-test-fakes/`). Split on 2026-11-17 (decision 22: a roadmap row maps to one stem, and the whole row did not fit 60 minutes; stem `test-fakes-and-conftest` spent its re-files on that). New `tests/fakes.py` holds one clock, exec, filesystem, journal and git fake and one `until`, and `tests/conftest.py` exposes them as fixtures; nothing migrates yet. `fakes.until` yields with the zero-wall-clock callback turn, the body of `tests/integration/test_scheduler.py::turn` (a future resolved by `loop.call_soon`) moved into `tests/fakes.py`, so the fake clock moves at the pacing `serve_rig.until` has today (declined-box-000559). Rows 118-120 migrate the users. |
| 22 | ~~`test-gate-floors`~~ | roadmap | chore | P2 | | | **Struck: replaced by row 97.** Its ticket was rejected because "measured minus 2, never below 1" cannot hold: the unit check measures `clutch/covmap.py`, `clutch/doctor.py` and `clutch/thresh.py` at 0% (declined-box-000566). |
| 23 | ~~`lint-guide-parity`~~ | roadmap | chore | P2 | | | **Merged** (`tickets/lint-guide-parity/`). Every rule `tickets.py` lints is in `host-authoring.md`; the three guide rules lint can check (spec pin fenced on a version bump, document fenced on a behavior change, `## Depends on` ticket exists) are linted. |
| 24 | ~~`extension-argv-from-snapshot`~~ | roadmap | chore | P2 | | | **Merged** (`tickets/extension-argv-from-snapshot/`). Every verb the extension runs comes from an `observe.py` table; `clutchRoot()` uses the snapshot's root. |
| 25 | ~~`dead-config-and-spec-fields`~~ | roadmap | chore | P3 | | | **Merged** (`tickets/dead-config-and-spec-fields/`). Remove `caps.poison`, `review.trigger_map`, `ReviewSurface`; spec frontmatter `consumes`/`emits`/`gates` removed or wired; `requisition_review.md` `context` input removed; `host-contract.md` inventory follows. |
| 26 | ~~`regress-scripts-guarded`~~ | roadmap | chore | P3 | | | **Merged** (`tickets/regress-scripts-guarded/`). The ten `tests/regress_*.py` without a `__main__` guard get one; a test imports each script module and asserts nothing runs. |
| 27 | ~~`host-onboarding-doc`~~ | roadmap (P8 gap) | chore | P2 | `docs-truth-sweep` | | **Merged** (`tickets/host-onboarding-doc/`). `clutch/docs/host-contract.md` gains "Onboarding a host" (checklist from install to first merge) and "Operating facts" (locks, state dir, upgrade, rollback). |
| 28 | ~~`evidence-store`~~ | evidence plan 2 | feature | P2 | `provider-capture-overwrite`, `fs-seam-mkdir-remove` | | **Merged** (`tickets/evidence-store/`). Blob store, `clutch.evidence.*` schemas, strict writer, tolerant reader, JSON Schema generation, `evidence.max_gb` prune. |
| 29 | ~~`evidence-envelope`~~ | evidence plan 3 | feature | P2 | `evidence-store` | | **Merged** (`tickets/fs-seam-read-size/`, `tickets/git-tree-id/`, `tickets/evidence-envelope/`). `start.json`/`end.json` from `CliAdapter.invoke`; arrival times and rusage through the exec seam; tree ids through `git.py`; CLI version probe; `engine.log` stage events carry `call_key`; every reader of `spools/providers/` moves; the old writer is deleted. Cause fix for row 1. |
| 30 | ~~`evidence-normalize-codex`~~ | evidence plan 4 | feature | P2 | `evidence-store` | | **Merged** (`tickets/evidence-normalize-codex/`). Codex normalizer and golden fixture; pins whether `input_tokens` includes `cached_input_tokens`. |
| 31 | ~~`evidence-normalize-claude`~~ | evidence plan 5 | feature | P2 | `evidence-store` | | **Merged** (`tickets/evidence-normalize-claude/`). Claude normalizer and fixture; qwen reuses it flagged `unverified`. |
| 32 | ~~`gemini-provider`~~ | gemini plan A1 | feature | P2 | | | **Merged** (`tickets/gemini-provider/`). `GeminiAdapter`, two settings files, watchdog branch, live view, `host-gemini.md`; after its agent capture; skipped while this machine has no Gemini credential (decision 19). |
| 33 | ~~`evidence-normalize-gemini`~~ | evidence plan | feature | P3 | `evidence-store`, `gemini-provider` | | **Merged** (`tickets/evidence-normalize-gemini/`). Gemini normalizer and fixture. |
| 34 | ~~`upstream-issue-verb`~~ | upstream plan 1 | feature | P2 | | | **Merged** (`tickets/upstream-issue-verb/`). `clutch issue` with five critical classes (decision 10), the CORE_TEMPLATE sentence (about 264 bytes), docs; after its agent capture. |
| 94 | ~~`roadmap-held-row-refile`~~ | driver plan 3 | feature | P0 | | `roadmap-status-stuck-rows` | **Merged** (`tickets/roadmap-held-row-refile/`). A row whose `roadmap_row` message Author declined, or whose linked stem was rejected, has no unattended release, against the plan's "nothing waits on a person": `clutch/roadmap.py::author_ahead` prints "reword the row's Content" and `clutch/box.py::Box.enqueue` hands back the same declined message on every pass (rows 21, 22 and 29 were held on 2026-11-16: declined-box-000559, declined-box-000572, declined-box-000573, and the rejected `test-gate-floors`). The driver re-files such a row itself: a new `roadmap_row` message whose request carries the decline's "do instead" text or the rejection reason, under a new stem when the old one was rejected, at most `caps.supervise` times per row; after that `roadmap status` names the row and its last reason. A re-file under a new stem also writes that stem into the row (or strikes the row and appends its replacement), so the gate's `roadmap merged --release R --priority P0 P1` check stops reporting the rejected stem (box-000582). |
| 95 | ~~`roadmap-status-stuck-rows`~~ | driver plan 4 | feature | P1 | | | **Merged** (`tickets/roadmap-status-stuck-rows/`). `clutch roadmap status` names every held row with a `waits:` line: a declined `roadmap_row` message, a linked row whose stem is rejected, and a linked row that is still a draft; `roadmap merged` reports a draft as a draft, not "not in the journal". At `30059a55` status printed `next: test-fakes-and-conftest, evidence-envelope` though both messages were declined, and counted rejected row 22 only as "1 blocked". Apply the repairs in `tickets/decisions/declined-box-000569-a3ea4f91.md`: fence `tests/unit/test_roadmap_table.py` and `tests/unit/test_roadmap_status.py`, give the status fixture `config.state_dir` and `fs`, and allow a skipped row whose unfinished dependency is open, linked, ready, waiting, or an unsettled journal stem. No credential wait: no row needs a credential this machine lacks. |
| 96 | ~~`supervise-every-route`~~ | driver plan 2 | feature | P1 | | | **Merged** (`tickets/supervise-every-route/`). Open decision 2 supervises `premise_failed` and spent-cap routes, but merged code supervises a spent cap only on the `gate_failed` path `runner.drive` reaches (`clutch/runner.py::failure_terminal`), never a serve merge-queue failure (`clutch/daemon.py::TicketWriter.consume_result`), and journals nothing for a supervisor attempt that escalates or is refused. Supervise the merge route through the same step, and journal a `supervisor_attempt` signal on every attempt. Narrowed on 2026-11-17 after three Implement attempts stopped during inspection and a split Rework was refused: section 6 step 1 is row 114 and the Effect-key scope it needs is row 113. |
| 97 | ~~`test-gate-floors-measured`~~ | roadmap | chore | P1 | | | **Merged** (`tickets/test-gate-floors-measured/`). Replaces row 22. `clutch/graph.py` (no floor today) and every module whose floor is 0 take their coverage under the unit check, measured with its own argv at the base commit, minus 2 as a ratchet in `test-gate.toml`; a module that measures 0% there stays at 0 with a comment saying its tests are integration tests. Measure each one: `thresh` measured 0% until `evidence-envelope` merged and 66.81% after it. |
| 98 | ~~`seams-passed-not-built`~~ | roadmap | chore | P1 | | | **Merged** (`tickets/seams-passed-not-built/`). Finishes row 14 (section 3.2), whose ticket scoped the driver and scheduler out: `scheduler.write_queue` takes the filesystem, clock and state directory from its caller instead of reading `self.journal._fs`, `_clock` and `dir.parent`; `Driver`, `Journal` and `EngineLog` receive `fs` instead of building `LocalFileSystem()`. |
| 99 | ~~`checkout-carries-journal`~~ | roadmap | chore | P1 | | | **Merged** (`tickets/checkout-carries-journal/`). Finishes row 20 (section 2.1 item 10), which `tickets/main-verb-groups/ticket.md` deferred to a ticket never filed: `Driver.from_config` takes the journal instead of building one that every caller overwrites (`driver.journal = checkout.journal; driver.effects = Effects(checkout.journal)` in `clutch/runner.py`, `clutch/triage.py` and `clutch/__main__.py`, each bind rescanning the journal), and `Checkout` and `StageContext` carry `log` and `box`. |
| 100 | ~~`cadences-count-runs`~~ | roadmap (decision 19) | chore | P1 | | | **Merged** (`tickets/cadences-count-runs/`, `tickets/checkpoint-counts-settled/`). Split in two (decision 22): `cadences-count-runs` is the retro trigger and its config, `checkpoint-counts-settled` the checkpoint push. Decision 19 counts every cadence in runs. The retro's elapsed trigger (`clutch/retro.py`, `RetroDays.every`, 7 days) and `clutch/checkpoint.py::CHECKPOINT_INTERVAL` (24 hours) become counts of settled tickets; the config inventory in `clutch/docs/host-contract.md` and `docs/how-clutch-works.md` follow. |
| 101 | ~~`eval-go-ai-panel`~~ | roadmap (decision 19) | feature | P1 | | | **Merged** (`tickets/eval-go-ai-panel/`). Decision 19 takes GO baselines from an AI panel of a different model family than the judge. `eval/harness.py::_go_report` refuses GO without a person's `--approve-author-graph`; that judgment comes instead from a model of a different family than the review judge, recorded in the GO report. |
| 102 | ~~`release-start-gates`~~ | driver plan 4 | feature | P1 | | | **Merged** (`tickets/release-start-gates/`). Section 1's "Gate to start" column has no command and `clutch/roadmap.py::choose` never reads it (declined-box-000518, whose reopen condition, the parser and gate blocks merged, is met). Each release heading gains a fenced `start` block under the `gate` block's rules; the driver readies a release's rows only when its start block passes, and `roadmap status` shows a failing one as a wait. A start clause no merged verb can check is named in section 1 as unchecked. |
| 103 | ~~`core-template-supervisor-verdicts`~~ | roadmap (decision 16) | chore | P1 | | | **Merged** (`tickets/core-template-supervisor-verdicts/`). `clutch/hostfiles.py::CORE_TEMPLATE` tells every host's supervising session it "may not confirm or reject", while `clutch/specs/ask/drain-loop.md` has the supervising agent loop run `confirm --yes` and `reject --yes` when a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation says so (decision 19): one rule, two homes that disagree (box-000508 was declined; `driver-loop` merged without the change). The template allows that confirm or reject, and the ticket edits such a Recommendation names on any ticket; it drops "rewrite a ticket the engine authored" from the session's forbidden list, because every ticket is written by an AI agent, so the distinction protects nothing. It compresses a gated rule to stay under its 8,192-byte limit (8,109 bytes today); `clutch core` refreshes `CLAUDE.md` and `AGENTS.md`. |
| 104 | ~~`docs-truth-after-driver`~~ | roadmap | chore | P1 | | `release-audit-030` | **Merged** (`tickets/docs-truth-after-driver/`). The documents the 0.3.0 merges made stale again: the Status and Current state of `docs/roadmap-driver-plan.md` ("nothing in it is in effect", `./dev.py publish`, a drain-loop that never confirms) and of `docs/evidence-trail-plan.md` (`_seq` resets, fixed by row 1); in this document, section 3.2 (`FileSystem` has `mkdir` and `remove`), the decision 5 ledger (CORE_TEMPLATE is 8,109 bytes), decision 16 (box-000508 was declined; row 103 owns the change), and row 92 (Marketplace publishing is the owner's manual step, decision 20; row 108 keeps the package). |
| 105 | ~~`release-audit-030`~~ | roadmap | chore | P1 | rows 94-104, `closed-sets-single-owner`, `shared-test-fakes`, `serve-rig-shared-fakes`, `tests-shared-fakes-a`, `tests-shared-fakes-b`, `regress-scripts-guarded`, `evidence-envelope`, `evidence-normalize-codex`, `evidence-normalize-claude`, `evidence-normalize-gemini`, `release-acceptance-review`, `plan-drain-prompts` | | **Merged** (`tickets/release-audit-030/`). Section 9's audit before each minor release has no actor once the driver ships unattended. Re-run the six passes of sections 2-4 at the base commit: remove fixed items, mark recurring ones "recurred in 0.3.0", add to the next release's gate block a command for each section 1 ship clause that merged code now records, and add the same audit row, with its own stem, as the last row of the next release's table so every release ends with one. Section 9 says rows stay struck in their release's table instead of moving to a "Shipped" section. |
| 106 | ~~`release-acceptance-review`~~ | roadmap | feature | P1 | | | **Merged** (`tickets/roadmap-accept/`, `tickets/release-acceptance-review/`). The owner's end-of-phase check (2026-11-16): `clutch roadmap accept <release>` reviews a release's merged rows, taken together, against its section 1 theme and ship gate and its owning plans, and appends a P1 row for each partial or unmet promise; every release's gate block ends with it. |
| 107 | ~~`plan-drain-prompts`~~ | roadmap | feature | P1 | | | **Merged** (`tickets/plan-drain-prompts/`). The owner's request (2026-11-16): the prompts that ran this release from plan to merged tickets by draining become `clutch prompt` types under `clutch/specs/ask/`, so any host can render, commit, and regenerate them: the run kickoff (environment and credential checks, the delegation, no person in the loop, the drift-sized authoring window, authoring that never holds the drain), the hand-authoring brief and procedure for one ticket, and the adversarial audit of an approved ticket against the code and every confirmed, unmerged ticket. Named for the plan-ticket-drain process; a plan-ticket-serve process comes later. |
| 108 | ~~`release-packages-kept`~~ | driver plan 5 | feature | P1 | | | **Merged** (`tickets/release-packages-kept/`). Decision 20: Marketplace publishing is the owner's manual step. When `ship` tags a release, the release's VS Code package is built and kept as `dist/vscode-clutchwork-<version>.vsix`, one file per version, never overwritten and never committed, and nothing uploads it. Today only `./dev.py vscode-package` builds it, by hand, so the tags since 0.2.7 have none. The engine names no `./dev.py`: the host declares its package commands (this repo: the VSIX build), and `ship` runs them after the tag and names each kept path in its digest. |
| 109 | ~~`release-changelog`~~ | driver plan 5 | feature | P1 | | | **Merged** (`tickets/release-changelog/`). Owner request (2026-11-17): `clutch release`, and so the driver's `ship`, writes `CHANGELOG.md` at the checkout root before its release commit, so the tag carries it. It adds a new top section for the version with the release date, listing each ticket merged since the previous `v*` tag on one line with its stem and a one-sentence summary; earlier sections stay untouched. This repo's `pyproject.toml` `[project.urls]` gains `Changelog`, pointing at the file. PyPI renders only the README, so the changelog is linked, not shown (decision 20 keeps publishing manual). |
| 111 | ~~`defer-journal-window`~~ | roadmap (decision 21) | chore | P1 | | | **Merged** (`tickets/defer-journal-window/`). Decision 21: the journal window slides behind the training release. Section 1 says the later releases are then renamed to the versions they start at: parallel runs and the graphics kind become 0.4.0, training, panels and the index 0.5.0, the journal window 0.6.0 (its table moves after the training release's table), and the document agent stays 0.7.0. Rename them in the section 1 table and its prose, the section 8 headings and their `gate` blocks (every `--release` and `roadmap accept` argument), the phase names in sections 5 and 6 and in row Content, and the release names in the owning plans (`docs/journal-sql-refactor-plan.md`, `docs/parallel-tickets-plan.md`, `docs/gemini-graphics-refactor-plan.md`, `docs/evidence-trail-plan.md`, `docs/training-data-plan.md`, `docs/stage-panels-plan.md`, `docs/annotations-index-plan.md`, `docs/document-agent-plan.md`). The journal window's "Gate to start" cell becomes decision 21's absolute cost. Must merge before 0.3.0 ships, or the driver starts the journal window as 0.4.0. |
| 112 | `closed-sets-remaining` | roadmap | chore | P3 | `closed-sets-single-owner` | | **Authored** (`tickets/closed-sets-remaining/`). Unify settled and retired states, failed-attempt terminals, surfaces, spike kinds, box classes, triage verdicts, control verbs, ask kinds, finding codes, conduct-file routing, the kind tuple in `author.py`, and the version split in `artifacts.py`. |
| 113 | ~~`supervisor-effect-scope`~~ | driver plan 2 | feature | P1 | | | **Merged** (`tickets/supervisor-effect-scope/`). Split from row 96. Section 6 step 1 runs the supervisor step outside a run under its own Effect keys, but every key the step mints comes from the stem and the integer attempt: `ticket-plane/{stem}/{attempt}/rework` in `clutch/daemon.py::apply_rework`, the LLM keys of `clutch/rework.py::rework`, `clutch/requisition.py::review_ticket` and `clutch/driver.py::Driver._run` through `clutch/llmeffect.py::llm_key`, the rework state tree, and the lift key in `clutch/stages.py::lift_outbox`. A step that journals no terminal leaves `run_seq` unchanged, so reusing an attempt number mints the next run's keys and that run replays the step's cached results. Give these one optional key scope, threaded from `apply_rework` to every key it mints, so a caller gets keys disjoint from every run's; with no scope every key is unchanged. Three requisition reviews of the split's idle-point half found these files on 2026-11-17. |
| 114 | ~~`supervise-at-idle-point`~~ | driver plan 2 | feature | P1 | `supervise-every-route`, `supervisor-effect-scope` | | **Merged** (`tickets/supervise-at-idle-point/`). Split from row 96: section 6 step 1. At the serve idle point after each settle and between drain tickets, each Reject-queue stem with no `supervisor_attempt` after its last operator keep gets the supervisor step in a detached worktree from main's HEAD at that idle point, under a key scope from row 113, and journals `supervisor_attempt`; the worktree is removed through `git.py` (`worktree remove`, `prune`) on approve and on escalate. Move the step out of `clutch/runner.py::failure_terminal` into one helper that both call and that never journals a terminal: merged `failure_terminal` always appends one, and its gate needs `routed: reject_queue`, which a drain `reject_arrival` lacks. Skip `ticket_changed` and `abandoned` stems; `caps.supervise` bounds it. Unit tests drive the drain and serve hooks with fakes, since both files are floored. |
| 116 | ~~`refile-carries-diagnosis`~~ | driver plan 3 | feature | P1 | | | **Merged** (`tickets/refile-carries-diagnosis/`). Row 94's re-file promises the rejection reason as the request, but no `reject_verdict` the engine writes carries a `reason` (`clutch/runner.py::reject_ticket`; 0 of 40 kill verdicts in the journal on 2026-11-17), so `clutch/roadmap.py::rejection_reason` always returns the literal "rejected", and `tests/unit/test_roadmap_refile.py` passes only because it journals a hand-made `reason` field. A re-filed row's request carries the rejected stem's last Reject-queue reason and its last Diagnose lessons, read from the events the engine writes, and the test journals those events. |
| 117 | ~~`ticket-budget-limits`~~ | roadmap (decision 22) | feature | P0 | | | **Merged** (`tickets/ticket-budget-limits/`). Decision 22. `clutch lint` refuses an open ticket whose `## Time budget` `expected` is over 60 minutes (road: split it into more tickets), whose `stuck` is not exactly twice `expected`, or whose `expected` is over 30 minutes without a one-line reason in `## Time budget` saying why it is not split; settled and rejected tickets are exempt, as they are from the evidence rule. `clutch/docs/host-authoring.md` states the rule: over 30 minutes, split when possible or give the reason; over 60, always split, each part its own stem; never raise the budget instead. Author follows the guide, so the driver's roadmap tickets split the same way. |
| 118 | ~~`serve-rig-shared-fakes`~~ | roadmap | chore | P2 | `shared-test-fakes` | | **Merged** (`tickets/serve-rig-shared-fakes/`). `tests/integration/serve_rig.py` uses the clock, exec, filesystem and `until` from `tests/fakes.py` instead of its own, with every serve test's pacing and result unchanged. |
| 119 | ~~`tests-shared-fakes-a`~~ | roadmap | chore | P2 | `shared-test-fakes` | | **Merged** (`tickets/tests-shared-fakes-a/`). The five largest test modules that define their own clock, exec, filesystem, journal or git fake use `tests/fakes.py` instead, and `tests/integration/test_merge.py` stops parsing another test's source to build its fixture. |
| 120 | ~~`tests-shared-fakes-b`~~ | roadmap | chore | P2 | `shared-test-fakes` | | **Merged** (`tickets/tests-shared-fakes-b/`). The next five largest test modules that define their own clock, exec, filesystem, journal or git fake use `tests/fakes.py` instead (after row 119's five). |

```gate
uv run clutch roadmap merged --release 0.3.0 --priority P0 P1
uv run clutch roadmap merged docs-truth-sweep evidence-envelope
uv run clutch roadmap merged --since v0.3.0 --at-least 3 --source box:roadmap_row --unattended
./dev.py test
uv run clutch roadmap accept 0.3.0
```

### 0.3.0, last group: the roadmap driver

Runs after the rows above; it is what runs every later release (`docs/roadmap-driver-plan.md`).

| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |
|---|---|---|---|---|---|---|---|
| 88 | ~~`superseded-settles`~~ | driver plan 1 | bug | P1 | | | **Struck: premise false.** A published Rework split never reaches the Reject queue: `clutch/runner.py::failure_terminal` retires the parent through `reject_ticket` in the same second, so a `superseded` state would release nothing (box-000471, box-000472). The split parents a person killed by hand (`specs-in-package`, `vscode-help`, `vscode-help-registry`) were Rework splits that did not publish; they carry no `supersedes` signal (box-000473). |
| 89 | ~~`supervisor-rework`~~ | driver plan 2 | feature | P1 | | | **Merged** (`tickets/rework-supervise-gate/`, `tickets/supervise-cap-lineage/`). Rework-update on `premise_failed` and spent-cap terminals with the diagnosis lessons; allowed-edit gate (no goal or scope change); `caps.supervise`; supervisor keep that starts a new lineage; `rework.md` lifted on escalation. |
| 90 | ~~`roadmap-author`~~ | driver plan 3 | feature | P1 | | | **Merged** (`tickets/roadmap-row-message/`, `tickets/roadmap-table-parser/`, `tickets/roadmap-author/`). `roadmap_row` box message and policy row; `clutch/roadmap.py` table parser; `roadmap author --ahead N`; Author data blocks for the row and its plan; row linking and striking; capture refusal. |
| 91 | ~~`release-gates-as-commands`~~ | driver plan 4 | chore | P2 | | | **Merged** (`tickets/release-gates-as-commands/`). Fenced `gate` blocks per release in this document (every gate is a command); `clutch roadmap status`. |
| 92 | ~~`release-publish`~~ | driver plan 5 | feature | P2 | `release-verb` | | **Merged** (`tickets/release-publish/`). Publishing never bumps the version: `clutch publish` (PyPI, token env name in config) uploads the `pyproject.toml` version only when its `v<version>` tag is on HEAD, and refuses otherwise (box-000480). `clutch release` (merged in `release-verb`) gains the `release` journal signal. PyPI uploads require `release.publish: true`; Marketplace publishing is manual (decision 20), and row 108 keeps the package. |
| 93 | ~~`driver-loop`~~ | driver plan 6 | feature | P1 | rows 89-92 | | **Merged** (`tickets/driver-loop/`). The idle-point sequence in serve and drain (supervise, author ahead, release when the gate passes, digest); the rewritten `drain-loop` prompt; how-clutch-works "Roadmap driver". |

### 0.4.0

```start
uv run clutch roadmap merged closed-sets-single-owner active-slot-single-owner merge-admission-single-owner
```

| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |
|---|---|---|---|---|---|---|---|
| 42 | `parallel-config` | parallel plan 3 | feature | P2 | | | `scheduler.parallel` model, doctor warning, config table. |
| 43 | `fence-overlap` | parallel plan 4 | feature | P2 | | | `fences_overlap`, run-alone rule, `_in_fence` moved to `tickets.py`. |
| 44 | `chain-order` | parallel plan 5 | feature | P2 | | | `chain()`, parallel order, slot filling, starvation guard. |
| 45 | `serve-parallel-dispatch` | parallel plan 6 | feature | P2 | `parallel-config`, `fence-overlap`, `chain-order`, `active-slot-single-owner` | | Run set, slots, one eligibility filter, one `running` writer, host-command lock, idle checks. |
| 46 | `merge-model-resolve` | parallel plan 7 | feature | P2 | `merge-admission-single-owner` | | after its agent capture `tickets/merge-model-resolve/evidence/merge-conflict-facts.md`: `specs/resolve.md`, bounds, re-review of the resolution delta, `model` step value. |
| 47 | `conflict-discard-rerun` | parallel plan 8 | feature | P2 | `merge-model-resolve` | | Delete the Rework handoff; retire and re-offer; `prior-diff` lift; `implement.md` and `rework.md` bumps; rerun cap. |
| 48 | `status-hot-paths` | parallel plan 9 | feature | P3 | | | Hot-paths table in the snapshot and extension. |
| 49 | `graphics-kind` | gemini plan B1 | feature | P2 | `closed-sets-single-owner` | | `kind: graphics` with `mode: command|generate`, `## Render`, `--reference` and `--input`, lint, authoring guide, CORE_TEMPLATE `|graphics` (9 bytes). |
| 50 | `graphics-render-check` | gemini plan B2 | feature | P2 | `graphics-kind` | `conflict-discard-rerun` | `command` mode render protocol at Check; `implement.md` block for both modes. |
| 51 | `route-kinds-filter` | gemini plan B3 | feature | P2 | | | `Route.kinds`, kind-aware `resolve()`, judge-independence warning in `doctor` and lint. |
| 52 | `image-quality-gate` | gemini plan B4 | feature | P2 | `graphics-kind` | | Layer 1: `clutch/images.py`, gate `image_quality`, the `images` and `images-embed` extras, side-by-side and heatmap artifacts. |
| 53 | `visual-review-surface` | gemini plan B5 | feature | P2 | `graphics-render-check`, `route-kinds-filter`, `image-quality-gate` | | Layer 2: `review_visual` spec with rubric, JSON schema, `graphics.judge_samples` majority. |
| 54 | `image-candidates-select` | gemini plan B6 | feature | P2 | `visual-review-surface` | | Layer 3: candidates in Implement, ranking, the select commit, `visual_undecided` park, its release (Gemini plan open decision 4). |
| 55 | `visual-review-baseline` | gemini plan B7 | feature | P2 | `visual-review-surface` | | `eval/visual/` fixtures labelled by an AI label panel of a model family other than the judge’s (§5, decision 13), `./dev.py visual-baseline`, the `visual_baseline` GO gate at 0.85 or above agreement with the panel’s labels. |
| (56) | `api-provider-client` | gemini plan (conditional) | feature | P2 | `gemini-provider` | `image-candidates-select` | Only if A0 fact 7 shows the CLI cannot generate images headlessly: the deferred `kind: api` client, scoped to image models. Row number is provisional. |
| 122 | `release-audit-040` | roadmap | chore | P1 | | | Re-run the six passes of sections 2-4 at the base commit: remove fixed items, mark recurring ones "recurred in 0.4.0", add to the next release's gate block a command for each section 1 ship clause that merged code now records, and add the same audit row, with its own stem, as the last row of the next release's table so every release ends with one. |

The ship clauses for ten parallel merges without a conflict-rerun cap hit, a generated graphics ticket merged through the select commit, and `visual_baseline` GO remain unchecked: no merged verb records those conditions.

```gate
uv run clutch roadmap merged --release 0.4.0
./dev.py test
uv run clutch roadmap accept 0.4.0
```

### 0.5.0

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
| 110 | `index-box-neighbors` | annotations plan | feature | P2 | `index-build` | | Owner request (2026-11-17): Suggestion Box messages, roadmap rows, and the decision records under `tickets/decisions/` join the index with their own chunks and embeddings from the host embed command, rebuilt incrementally like files. Triage and Author receive, as data, the nearest existing messages, rows, open tickets, and decision records for each message, so a recurring report, a duplicate of a roadmap row that has no ticket yet, or a re-filed declined idea is matched by meaning, not only by the exact summary `clutch/box.py::Box.enqueue` compares. On 2026-11-16 one flaky test was reported four times (box-000457, box-000529, box-000531, box-000574), and box-000582 duplicated row 94, which triage cannot see. With no embed command, full-text search is the floor, as the index plan says. |
| 73 | `context-suggest` | annotations plan 5 | feature | P2 | `index-build` | | `clutch context suggest <stem>` and the Author data block. |
| 74 | `index-consumers` | annotations plan 6 | feature | P3 | `context-suggest` | | `index.implement_hint`, `doc draft --from <topic>`, the training export join. |

```gate
uv run clutch roadmap merged --release 0.5.0
./dev.py test
uv run clutch roadmap accept 0.5.0
```

### 0.6.0 (conditional)

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
uv run clutch roadmap merged --release 0.6.0
./dev.py test
uv run clutch roadmap accept 0.6.0
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
uv run clutch roadmap accept 0.7.0
```

### Agent tasks (not tickets)

- For Gemini A0, an agent runs headless `gemini` per settings file with an empty `HOME`, saving stdout, stderr, exit code and live process argv for facts 1-8, and resolves the `images` and `images-embed` extras on Python 3.14 in a scratch venv, saving resolver output for fact 9. Commit the nine facts to `tickets/gemini-provider/evidence/`; skip the credential-dependent capture while the credential is missing.
- For GitHub prefill, an agent opens prefilled links of increasing body length in a headless browser, saving statuses and rendered fields for facts 1-2, then builds and installs the wheel non-editable in a scratch venv and saves metadata for fact 3. Commit to `tickets/upstream-issue-verb/evidence/`.
- For parallel A0, an agent reads the 13 `merge_conflict_facts` events from the journal and commits them as `tickets/merge-model-resolve/evidence/merge-conflict-facts.md`.
- For row 35, an agent profiles a drain start and `clutch status` at the end of the truth release, recording the share of wall time spent in journal reads, and commits `tickets/journal-query-layer/evidence/re-measure.md`.

## 9. Keeping this document true

- A ticket authored from a row links its stem in that row; merged rows stay struck in their release's table. Once `roadmap-author` lands, the driver makes these edits as ticket-plane commits; until then the agent that authors the row does.
- The audit (sections 2-4) is re-run before each minor release with the same six passes; rows that are fixed are removed, rows that recur are marked with the release that was supposed to fix them.
- Shared budgets (section 5, decision 5) and shared files (decision 8) are updated whenever a plan adds a ticket that touches them.
