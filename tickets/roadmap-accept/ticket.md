---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Runs before
- evidence-envelope

## Context
- clutch/roadmap.py
- clutch/driver.py::LlmStage
- clutch/driver.py::Driver.from_config
- clutch/driver.py::Driver.run
- clutch/retro.py::validate_recurrences
- clutch/triage.py::triage_pass
- clutch/providers.py::resolve
- clutch/providers.py::candidates
- clutch/box.py::RoadmapRow
- clutch/box.py::Message
- clutch/box.py::Box.messages
- clutch/status.py::last_states
- clutch/tickets.py::stem_findings
- clutch/stages.py::findings_text
- clutch/specs/__init__.py::ENGINE_LLM_SURFACES
- clutch/specs/__init__.py::load_spec
- clutch/specs/__init__.py::render
- clutch/artifacts.py::NonBlank
- clutch/artifacts.py::StageResult
- clutch/gates.py::GateReport
- clutch/llmeffect.py::llm_key
- tests/unit/test_roadmap_author.py::FakeGit
- tests/unit/test_roadmap_author.py::test_main_roadmap_author
- tests/unit/test_roadmap_gate.py::test_main_roadmap_gate
- tests/unit/test_roadmap_table.py::HEADER
- tests/unit/test_roadmap_table.py::row
- tests/unit/test_retro_recurrence.py::MemoryJournal
- tests/integration/test_specs_json_reply_specs.py
- tests/integration/test_closed_sets.py::test_specs_closed_sets_and_constants
- docs/roadmap.md#1. Release plan
- docs/roadmap.md#5. Cross-plan decisions
- docs/how-clutch-works.md#2.1 Verbs
- docs/how-clutch-works.md#8.2 Routing
- docs/how-clutch-works.md#8.4 Prompt specs and the driver

## On-demand
- clutch/__main__.py

## Goal / Why
Each roadmap row passes its own acceptance criteria, but nothing checks that the rows of a release, taken together, deliver what the release promised. The owner asked for that check on 2026-11-16: "it is one thing for each ticket to pass its acceptance criteria, however the sum of the tickets need to have satisfied the plan of the feature/phase of roadmap". Today `clutch/roadmap.py::ship` tags a release as soon as its `gate` block passes, and every block checks only that rows merged and the suite passes.

This ticket adds the check as a verb, `clutch roadmap accept <release>`. It is a read-only model review on a new `acceptance` surface. The sibling ticket `release-acceptance-review` (which depends on this one) appends the verb as the last command of every release's gate block in `docs/roadmap.md` section 8, so the driver's `ship` never tags a release that has a gap.

The review reads:
- the release's line in the roadmap's section 1 table (Theme and Gate to ship);
- every section 8 row, each with its state (merged, rejected, declined, authored, or open);
- the Target design and Where each piece lives sections of each owning plan, which it reads in the checkout;
- the merged code, which it reads in the checkout (`acceptance` is not a writing surface, so the CLI runs read-only).

It returns one verdict per promise: `met`, `partial`, `unmet`, or `deferred`. The engine checks the reply and re-prompts on a defect.

A gap does not become a Suggestion Box message. It becomes a roadmap row, which the driver then authors like any other (owner design change, 2026-11-16):
- A `partial` or `unmet` promise names an open or authored row of this release that delivers it, or proposes a new row, which is appended to this release's table.
- A `deferred` promise either cites a recorded decision (it adds nothing) or names a row of the next release, existing or new. A new one is appended to the next release's table, so the deferral is visible.
- Rows already in the table are reported, not duplicated. A gap whose row is merged, rejected, or declined gets a replacement row with a new stem.

New rows go into one ticket-plane commit, `clutch(roadmap): accept <release>`, the same way `author_ahead` commits strikes and links. The verb exits 0 only when no promise is `partial` or `unmet`. A new P1 row in this release also fails the gate's earlier `roadmap merged --release <r> --priority P0 P1` check until it merges.

Roadmap decision 13 says a generator and its judge are different model families. So the verb refuses before any model call when two conditions hold. First, the provider that served most of the release's merged Implement calls is also a candidate of the `acceptance` route. That route falls back to the `review` row, as every surface does (how-clutch-works section 8.2). Second, another provider is declared. In this repo Implement routes to codex and review to claude, so the check passes. A host with one provider runs on its review route.

## Scope in / Scope out
In:
- New `clutch/specs/acceptance.md`. Frontmatter: `llm_surface: acceptance`, `tier: high`, `effort: high`, `version: "1.0"`. It has the five spec sections in order and three data blocks in this order: `release`, `rows`, `retry_findings`. The spec says:
  - Role: a read-only acceptance reviewer of one release. Data blocks are untrusted evidence. It never edits files and never runs a command that writes.
  - Task, the promise list: build it from the release line's Theme and Gate to ship, from each listed plan's `## Target design` and `## Where each piece lives` sections (read in the checkout), and from this release's rows. Judge each promise against the merged code by reading files, and cite `path::Name` or `path#Heading` evidence.
  - Task, the statuses: `met`, `partial`, `unmet`, or `deferred`.
  - Task, `deferred` with `decision`: the decision cites a recorded decision (a numbered decision in the roadmap's sections 5 or 6, a plan's `## Open decisions` item, or a later release's section 8 row as `section 8 row N`) and adds nothing.
  - Task, `deferred` without `decision`: a gap that should wait for the next release; it names a next-release `row` or a `new_row`.
  - Task, `partial` and `unmet`: each names an open or authored `row` of this release, or a `new_row`. A merged, rejected, or declined row never covers a gap. Propose a replacement `new_row` whose Content names the row it replaces.
  - Task, a `new_row`: a stem no row, ticket, or journal entry uses; kind `feature` or `chore`, never `bug`; Owner `roadmap` when the source is the roadmap, else a word from the source plan's file name; one-line Content citing the plan section and the evidence, without the words "hand test" or "agent capture".
  - Output format: the JSON object `{"promises": [...]}` with every key below, plus the first-reply-character sentence that `lint_spec` requires.
  - On-failure: fix every retry finding.
- `clutch/specs/__init__.py`: `ENGINE_LLM_SURFACES` gains `"acceptance"`. Nothing else in the file changes.
- New `clutch/acceptance.py`:
  - It imports `NonBlank` from `clutch.artifacts`, and `SPECS_DIR` and `Refusal` from `clutch.runner`. It defines no `NonBlank`, `_Strict`, or `Strict`, which keeps it compatible with the sibling `closed-sets-single-owner`.
  - `ACCEPT_STUCK_S = 1800.0`.
  - The reply models use `ConfigDict(strict=True, extra="forbid")`:
    - `GapRow`: `stem: NonBlank`, `kind: Literal["feature", "chore"]`, `owner: NonBlank`, `content: NonBlank`.
    - `Promise`: `promise: NonBlank`, `source: NonBlank`, `status: Literal["met", "partial", "unmet", "deferred"]`, `evidence: list[NonBlank]` with at least one item, `decision: NonBlank | None`, `row: int | None` (at least 1), and `new_row: GapRow | None`. An after-validator enforces three rules. `met` has none of `decision`, `row`, or `new_row`. `partial` and `unmet` have no `decision` and exactly one of `row` or `new_row`. `deferred` has exactly one of `decision`, `row`, or `new_row`.
    - `AcceptanceReply`: `promises: list[Promise]` with at least one item.
  - `async def accept(checkout, driver, release) -> tuple[bool, list[str]]`. In order:
    1. Refusals, before any model call. `roadmap.ROADMAP` missing gives `f"missing {ROADMAP}"`. Uncommitted edits (`checkout.git.status_porcelain(repo, "--", ROADMAP)` non-empty) give `f"uncommitted {ROADMAP}"`. No parsed row with `release_name(row.release) == release` gives `no release <release>`. No line starting `` | **<release>** | `` gives `no section 1 row for <release>`. Each refusal carries a road.
    2. Inputs. `files` is the same `ls-files --cached --others --exclude-standard -z` set `author_ahead` reads, and `states = last_states(journal events)`. Each row gets one state, checked in this order:
       - `merged`: the row is struck or in `choose(rows, states=states, files=files).strike`.
       - `rejected`: its stem's state is `rejected`.
       - `declined`: the highest-`seq` `roadmap_row` message in `Box(config.state_dir / BOX_DIR, fs)` whose `roadmap_row.stem` is the row's stem is resolved with kind `declined`.
       - `authored`: the row is linked, or `tickets/<stem>/ticket.md` is in `files`.
       - `open`: none of the above.
    3. The plan list is `ROADMAP` plus each distinct non-None `plan_path(row.owner, files)` of this release's rows, sorted. The next release is the first release name that follows `release` in section 8 order, or None.
    4. The judge check uses the spec's `tier`. The stems are each merged row of this release plus every `tickets/<stem>/` named in its Content. The implementer is the provider named in `cost.provider` of the most `effect_completion` events whose key splits into six `/` parts, `llm/<stem>/<seq>/implement/<attempt>/<call>`, with a stem in that set. Ties go to the provider counted first. The check raises when three things hold: an implementer exists, any `providers.candidates(config, tier, "acceptance")` candidate is that provider, and another provider is declared. The message is `acceptance judge <p> implemented most of release <r>`. The road names the routing row `{tier: <tier>, surface: acceptance, candidates: [{provider: <other>}]}`, where `<other>` is the first other declared provider.
    5. One `driver.run` call, with `LlmStage(surface="acceptance", emits=AcceptanceReply, gates=[], render=..., review=...)`, `ticket=None`, `run_seq=len(<events read at the start>)`, `attempt=1`, `workspace=checkout.repo`, `tier`/`effort` from the spec's meta, `stuck_budget=ACCEPT_STUCK_S`, `expected_budget="surface"`, and `scope_fence=()`.
       - The spec is `load_spec((SPECS_DIR / "acceptance.md").read_text())`.
       - The render fills three blocks. `release` is the JSON object `{"release", "next_release", "release_plan" (the section 1 line verbatim), "plans"}`. `rows` is a JSON list in table order of `{"number", "release", "stem", "owner", "kind", "priority", "depends", "content", "state"}`, with `release` given as `release_name`. `retry_findings` is `findings_text(findings)`.
    6. The review returns `GateReport(code="acceptance_reply", ...)`, failing with one finding (code `acceptance_reply`, with a road) per defect:
       - a `source` whose part before the first `#` is not in the plan list;
       - a `row` that names no section 8 row;
       - a `row` in the wrong release: it must be this release for `partial` or `unmet`, and the next release for `deferred`;
       - a `row` whose state is `merged`, `rejected`, or `declined`;
       - a `deferred` `row` or `new_row` when there is no next release;
       - a `new_row` stem that `stem_findings` refuses (that finding's message and road), or that is already a section 8 stem, a key of `states`, the prefix of a `tickets/<stem>/` path in `files`, or another `new_row` stem in the reply;
       - an owner containing `|` or a newline, or whose `plan_path(owner, files)` is not the source's path;
       - Content containing a newline.
    7. When the outcome is not `ok`, raise `Refusal("acceptance review ended <outcome>", ...)` with a road to run `clutch roadmap accept <release>` again.
    8. When any `new_row` exists:
       - check `status_porcelain` again and refuse `f"uncommitted {ROADMAP}"`;
       - re-read the file;
       - in reply order, number each new row `max(parsed numbers) + 1` and upward;
       - add each with `roadmap.append_row(text, target, line)`, where `line` is `` | <n> | `<stem>` | <owner> | <kind> | P1 | | | <content> | `` and the target is this release for `partial`/`unmet`, the next release for `deferred`;
       - write the text with `checkout.fs.write`, then make one `checkout.git.commit(repo, "clutch(roadmap): accept <release>", only=[ROADMAP])`.
    9. Return `(ok, lines)`. `ok` is true only when no promise is `partial` or `unmet`.
       - Each promise prints `accept <r>: <status>: <promise> [<source>]`. The suffix is ` -- <decision>`, ` -- row <n> <stem>`, ` -- new row <n> <stem> in <target>`, or nothing for `met`.
       - The last line is `accept <r>: passed`, or `` accept <r>: failed: <k> of <m> promises partial or unmet -- `clutch roadmap author` files the rows above; the gate passes once they merge ``.
- `clutch/roadmap.py`: new `append_row(text: str, release: str, line: str) -> str`. Its target is the release's first table: the smallest `_table` among parsed rows whose `release_name` is `release`. It inserts `line` plus that table's last parsed row's line ending after the table's last line, the last consecutive line starting with `|`, which may be an unparsed row such as `(56)`. Every other line stays byte-identical. A release with no parsed row raises `Refusal("no release <release>", ...)`. Nothing else in the file changes.
- `clutch/__main__.py`:
  - The `roadmap` sub-parser gains `accept` with one positional `release`.
  - `handle_roadmap` takes no writer lock for it. It builds `build_control(checkout).providers`, then `_preflighted_llm`, then `Driver.from_config(config, llm=..., env=env, clock=clock, sleep=checkout.sleep, fs=checkout.fs)` with `driver.journal = checkout.journal` and `driver.effects = Effects(checkout.journal)`, the same way `_review` does. It then awaits `acceptance.accept(checkout, driver, args.release)` and closes the session in `finally`.
  - It prints the lines and returns 0 when `ok`, else 1. A `Refusal` exits 2 through the existing handler.
- `docs/how-clutch-works.md`:
  - Section 2.1 gains a row after `roadmap gate <release>`: `` `roadmap accept <release>` ``, lock `commit only`, describing the review, the refusals, the appended rows and their commit, and exits 0, 1, and 2.
  - The section 8.4 table gains an `acceptance.md` row: judging a release's merged rows together against its theme, ship gate, and plans; the reply is promises `met`/`partial`/`unmet`/`deferred` with gap rows.
- `clutch/docs/host-running.md`: the `roadmap` row gains one sentence on `roadmap accept <release>`: it reviews, appends gap rows in one commit, exits 0 only with no partial or unmet promise, takes no writer lock, and works while serve runs.
- `tests/integration/test_closed_sets.py::test_specs_closed_sets_and_constants`: the `ENGINE_LLM_SURFACES` pin gains `"acceptance"`. No other assertion changes.
- New tests in two new files: `tests/unit/test_roadmap_accept.py` and `tests/integration/test_acceptance_spec.py`. The unit file may import `FakeGit` from `tests/unit/test_roadmap_author.py`, `HEADER` and `row` from `tests/unit/test_roadmap_table.py`, and `MemoryJournal` from `tests/unit/test_retro_recurrence.py`, all unchanged. Its tests read and write disk only under `tmp_path`: they monkeypatch `clutch.acceptance.SPECS_DIR` to a `tmp_path` directory holding a hand-written test spec with the same three data blocks, and drive `accept` through a fake driver. The fake's `run(stage, consumed, **kwargs)`:
  1. records its kwargs;
  2. for each scripted reply text, renders `stage.render(consumed, findings)` and records the prompt;
  3. validates the reply with `stage.emits.model_validate_json` and awaits `stage.review(reply, n)`;
  4. returns `StageResult(outcome="ok", artifact=reply, ...)` for the first reply that passes. A failing review feeds its findings to the next render, and the outcome is `gate_failed` when the replies run out. A scripted outcome string is returned as-is.

  These unit tests keep `clutch/acceptance.py` and `clutch/roadmap.py` at or above the 90% `coverage.default` floor.

Out:
- The gate blocks and the section 8 intro of the roadmap, and how-clutch-works section 7.5: `release-acceptance-review` changes them.
- A journal signal, a Suggestion Box message, a config field, a new routing default, `observe.STEP_NAMES`, `clutch/help.py`, the extension, and `stats.SURFACES`. Unknown surfaces already render as `stage` there.
- `roadmap merged`, `run_gate`, `ship`, `author_ahead`, `choose`, `link`, and `strike`.
- Passing provider keys to gate commands. `run_gate` strips configured secrets from every gate command, so a host whose judge needs an `auth` key cannot run `roadmap accept` from a gate. That is filed as a suggestion, not built here.

## Scope fence
- clutch/acceptance.py
- clutch/specs/acceptance.md
- clutch/specs/__init__.py
- clutch/roadmap.py
- clutch/__main__.py
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/integration/test_closed_sets.py
- tests/unit/test_roadmap_accept.py
- tests/integration/test_acceptance_spec.py

## Acceptance criteria
1. `tests/unit/test_roadmap_accept.py::test_append_row` builds a document with these parts, in order:
   - `### 1.0.0` with a table of rows 1 and 2, a blank line, and a `gate` block;
   - `### 1.0.0, last group` with row 3;
   - `### 2.0.0` with row 4, then the unparsed row `` | (5) | `cond-row` | roadmap | feature | P2 | | | c | ``, then a blank line.

   It asserts the following.
   - `append_row(text, "1.0.0", line)` puts `line` directly after row 2, before the blank line.
   - `append_row(text, "2.0.0", line)` puts it directly after the `(5)` line.
   - Every other line is byte-identical.
   - `parse` of the result returns the new row with its number and stem, priority `P1`, empty `depends`, `linked` and `struck` false, and the target table's heading as its release.
   - `append_row(text, "9.9.9", line)` raises `Refusal` matching `no release 9.9.9`.

   Ruled out: appending to the release's last table or the end of the file, and splitting a table at its unparsed last row.
2. `tests/unit/test_roadmap_accept.py::test_accept_passes`. The setup:
   - a `tmp_path` roadmap with a section 1 line `| **1.0.0** | Theme one | none | Ship one |`, `### 1.0.0` rows 1-2, and `### 2.0.0` row 3;
   - a `MemoryJournal` holding 4 events;
   - a reply of one `met` promise and one `deferred` promise with `decision`.

   It asserts:
   - the return is `(True, [<the two promise lines>, "accept 1.0.0: passed"])`, exactly;
   - no commit;
   - the recorded run kwargs include `ticket=None`, `run_seq=4`, `attempt=1`, `workspace=repo`, `stuck_budget=1800.0`, `expected_budget="surface"`, and `scope_fence=()`;
   - the stage has surface `acceptance` and emits `AcceptanceReply`;
   - the rendered release JSON has `next_release` `"2.0.0"`, the section 1 line verbatim, and `plans` `["docs/roadmap.md"]`.

   Ruled out: a constant `run_seq`, which would replay the first run's recorded reply on every later run, and a pass reported as a failure.
3. `tests/unit/test_roadmap_accept.py::test_row_states` asserts the `state` of each row in the rendered `rows` JSON:
   - `merged` for a struck row, and for a row whose stem is journaled `merged`;
   - `rejected` for a stem journaled `rejected`;
   - `declined` for a row whose `roadmap_row` box message (a real `Box` under `tmp_path`) is resolved `declined`;
   - `authored` for a linked row, and for one whose `tickets/<stem>/ticket.md` is in the fake `ls-files`;
   - `open` otherwise.

   Ruled out: a rejected or declined row shown as open, which would let a gap point at a dead row.
4. `tests/unit/test_roadmap_accept.py::test_gaps_append_rows`. The reply in order:
   - a `partial` promise with a `new_row` of stem `gap-one`;
   - an `unmet` promise whose `row` is open row 2 of this release;
   - a `deferred` promise with a `new_row` of stem `gap-two`.

   It asserts:
   - the return is `(False, lines)`, and the last line is exactly `` accept 1.0.0: failed: 2 of 3 promises partial or unmet -- `clutch roadmap author` files the rows above; the gate passes once they merge ``;
   - there is exactly one commit, `("clutch(roadmap): accept 1.0.0", ["docs/roadmap.md"], text)`;
   - in `text`, `gap-one` is row 4 at the end of the `1.0.0` table, and `gap-two` is row 5 at the end of the `2.0.0` table, each with priority `P1`;
   - the promise lines end ` -- new row 4 gap-one in 1.0.0`, ` -- row 2 b-row`, and ` -- new row 5 gap-two in 2.0.0`.

   A second case replies with only the `deferred` `new_row`. It returns `True` and still makes one commit. Ruled out: one commit per row, a deferred gap failing the gate, a gap row in the wrong table, and a row reported as covering a gap and duplicated anyway.
5. `tests/unit/test_roadmap_accept.py::test_reply_checks_reprompt`. The fake driver's first reply has one of each defect from Scope step 6, and its second is valid. It asserts:
   - the first review fails with exactly one `acceptance_reply` finding per defect, each with a non-empty `paved_road`;
   - the second render's prompt contains those findings;
   - the run ends `ok`.

   A separate case uses release `2.0.0`, the last release, with a `deferred` `new_row`, and asserts the `no next release` finding. Ruled out: any defect accepted silently, and findings that never reach the re-prompt.
6. `tests/unit/test_roadmap_accept.py::test_refusals_before_the_model` asserts these refusals, raised before the fake driver's `run` is called and with no commit:
   - a missing roadmap gives `missing docs/roadmap.md`;
   - a dirty roadmap gives `uncommitted docs/roadmap.md`;
   - release `9.9.9` gives `no release 9.9.9`;
   - a roadmap without the section 1 line gives `no section 1 row for 1.0.0`;
   - a run outcome of `timeout` gives `acceptance review ended timeout`.

   Ruled out: a model call spent on a request that is refused anyway.
7. `tests/unit/test_roadmap_accept.py::test_judge_family`. The journal holds `implement` effect completions:
   - two by `claude` and one by `codex` for the stems of merged rows of release `1.0.0`;
   - two by `codex` for a stem named only in a merged row's `tickets/<stem>/` Content;
   - five by `claude` for a stem outside the release.

   The implementer is therefore `codex` (3 calls against 2). Dropping the Content stems, or counting the outside stem, makes it `claude`.

   The config declares `claude` and `codex`. It asserts:
   - with only a `high`/`review` route to `codex`, `accept` raises `Refusal` matching `acceptance judge codex implemented most of release 1.0.0`, with a road containing `surface: acceptance` and `provider: claude`;
   - adding a `high`/`acceptance` route to `claude` lets the run proceed;
   - a config declaring only `codex` proceeds.

   Ruled out: counting another release's calls, refusing a one-provider host, and ignoring an `acceptance` routing row.
8. `tests/unit/test_roadmap_accept.py::test_main_roadmap_accept` monkeypatches `load_config`, `child_env`, `Journal`, `build_control`, `_preflighted_llm`, `Driver.from_config`, and `clutch.acceptance.accept`. Its `Lockfile` fails the test when constructed. It asserts that `cli.main(["roadmap", "accept", "1.0.0"], ...)` exits 0 for `(True, ["a"])`, 1 for `(False, ["b"])`, and 2 with stderr starting `clutch roadmap:` for a `Refusal`. In every case `accept` received the release `1.0.0` and the session was closed. Ruled out: the writer lock taken (the drain holds it while its gate runs this verb), a hard-coded exit code, and a leaked session.
9. `tests/integration/test_acceptance_spec.py::test_acceptance_spec` reads the real `clutch/specs/acceptance.md` and asserts:
   - `lint_spec(text) == []`;
   - `load_spec(text).meta.model_dump()` is `{"llm_surface": "acceptance", "tier": "high", "effort": "high", "version": "1.0"}`;
   - `spec.inputs == ("release", "rows", "retry_findings")`, and `render` with three JSON strings succeeds;
   - the Output format section contains, in backticks, every field name of `AcceptanceReply`, `Promise`, and `GapRow`, and each of the four status values.

   Ruled out: a spec the driver cannot render, and spec keys that drift from the reply model.
10. `./dev.py test tests/integration/test_closed_sets.py tests/integration/test_specs_json_reply_specs.py tests/integration/test_vocabularies.py tests/unit/test_host_running.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_table.py tests/unit/test_roadmap_gate.py` exits 0. The only assertion changed is the `ENGINE_LLM_SURFACES` pin, which now includes `acceptance`.
11. The `uv run python -c` check in `## Verification` exits 0. It requires:
    - `docs/how-clutch-works.md` holds a line starting ``| `roadmap accept <release>` | commit only |``, and a line starting ``| `acceptance.md` |``;
    - `clutch/docs/host-running.md` holds `roadmap accept <release>`.
12. `./dev.py test` exits 0, including the unit coverage gate for `clutch/acceptance.py` and `clutch/roadmap.py`. One known intermittent test is not a premise failure: if the only failure is `tests/integration/test_kill_cli_activation.py::test_killed_run_is_terminal_or_restart_reconcilable[True]`, and it passes on the base commit and passes when rerun alone on the candidate, it is intermittent for this ticket even though the test imports `clutch/__main__.py`. Its `[True]` case runs `clutch.drain.drain` and calls only the unchanged `build_control` from that file, never the `roadmap accept` parser or handler. Commit, reply `ok`, and report it in `second_problems` and `surprises`. Ruled out: a finished diff thrown away for one out-of-fence intermittent failure.

## Verification
```
./dev.py test tests/unit/test_roadmap_accept.py
./dev.py test tests/integration/test_acceptance_spec.py
./dev.py test tests/integration/test_closed_sets.py tests/integration/test_specs_json_reply_specs.py tests/integration/test_vocabularies.py tests/unit/test_host_running.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_table.py tests/unit/test_roadmap_gate.py
uv run python -c "import pathlib; b = chr(96); h = pathlib.Path('docs/how-clutch-works.md').read_text().splitlines(); r = pathlib.Path('clutch/docs/host-running.md').read_text(); assert any(l.startswith('| ' + b + 'roadmap accept <release>' + b + ' | commit only |') for l in h); assert any(l.startswith('| ' + b + 'acceptance.md' + b + ' |') for l in h); assert 'roadmap accept <release>' in r"
./dev.py test
```

## Definition of rejected
The branch is rejected if any of these hold:
- `roadmap accept` takes the writer lock;
- it writes anything other than `docs/roadmap.md`, in more than one commit per run, or edits an existing row;
- it files a Suggestion Box message, journals a new signal, or adds a config field;
- `acceptance` joins `WRITING_SURFACES`, or the model is called outside `Driver.run`;
- an appended row has a priority other than `P1` or kind `bug`;
- a gap is counted `ok` while it is `partial` or `unmet`;
- the module defines its own `NonBlank`;
- a test is added to `tests/integration/test_cli.py` or another hot test file;
- any existing assertion other than the `ENGINE_LLM_SURFACES` pin changes.

## Time budget
- expected: 130m
- stuck: 180m
