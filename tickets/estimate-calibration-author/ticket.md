---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- estimate-calibration

## Context
- clutch/author.py::author
- clutch/docs/host-authoring.md#What each section is for
- docs/how-clutch-works.md#9.3 Author and starting state
- tests/integration/test_author.py::test_author_spec_requires_criteria_to_name_wrong_results
- tests/unit/test_closed_sets_remaining.py::test_author_skeletons_follow_kinds
- tests/fakes.py

## On-demand
- clutch/specs/author.md

## Goal / Why
Roadmap row 142 (`estimate-calibration`, owner request 2026-11-17), part 3 of 3. Part 1 (`estimate-calibration`) adds `clutch engine calibrate` and `clutch/calibration.py`. The command journals one `estimate_calibration` signal holding a table: per provider and model, the run count, the median estimate, and the median and 90th-percentile actual Implement minutes of recent runs. The row asks that Author's prompt show the current table, so new estimates are in AI minutes, as decision 22 (`docs/roadmap.md` section 6) requires. On 2026-11-17 the actual minutes were about a tenth of the estimates (`codex/gpt-6.1-terra`: estimate p50 30m, actual p50 4.9m, actual p90 9.8m over the last 100 runs).

`CLAUDE.md` "One authoring process" puts ticket content rules only in `clutch/docs/host-authoring.md`, which every authoring surface reads (the Author stage, and chat sessions through `clutch prompt author`). The prompt spec embeds the guide rather than restating it. So the instruction to estimate from the table goes in the guide's `Time budget` bullet, and the spec gains only the data block.

When this ticket is done:
- The Author stage's rendered prompt has a `calibration` data block. It holds the latest `estimate_calibration` signal's table, rendered by part 1's `render`, or `none` before the first calibration.
- The guide's `Time budget` bullet tells every author to estimate from that table, and says where to find it: `clutch engine calibrate` prints it, and Author's prompt carries it.

## Scope in / Scope out
In:
- `clutch/calibration.py`, which part 1 creates (read it first): append `latest(events) -> list[dict]` after `render`. It returns the `rows` of the last `signal` event whose `signal` is `ESTIMATE_CALIBRATION`, or `[]` when there is none. Nothing else in the file changes.
- `clutch/author.py::author`: add `from clutch import calibration` to the imports. Right after `open_tickets = await list_open_tickets(checkout)`, compute `estimates = calibration.render(calibration.latest(checkout.journal.read()))` once. In `render_author`, add the input `"calibration": estimates` after `"skeletons"`. Nothing else in the file changes. The name `render` in `author.py` stays `clutch.specs.render`.
- `clutch/specs/author.md`: in `## Inputs`, after the `skeletons` block, a new block introduced by the line `Estimate calibration (the guide's Time budget table):`, then `<<clutch-data:begin calibration>>`, `{{calibration}}` and `<<clutch-data:end calibration>>`. Bump `version` to the next minor above the version on main. No other text in the spec changes; the rule lives in the guide.
- `clutch/docs/host-authoring.md`, `## What each section is for`, the `Time budget` bullet: after the sentence "Both `expected` and `stuck` are AI time: ...", insert the line "Estimate from the latest calibration table, which `clutch engine calibrate` journals and prints and Author's prompt carries as its `calibration` block: per provider and model, the median estimate and the median and 90th-percentile actual Implement minutes of recent runs." Nothing else in the guide changes.
- `docs/how-clutch-works.md`, section 9.3: "The Author prompt embeds the authoring guide and skeletons, and each re-prompt" becomes "The Author prompt embeds the authoring guide, the skeletons, and the latest `estimate_calibration` table (`engine calibrate`, section 2.1; `none` before the first), and each re-prompt". Nothing else in the file changes.
- `tests/integration/test_author.py::test_author_spec_requires_criteria_to_name_wrong_results`: its `spec.meta.version` pin becomes the bumped version. Nothing else in the file changes.
- New `tests/unit/test_author_calibration.py` (criteria 1-2). It drives `author.author` with the same stand-ins as `tests/unit/test_closed_sets_remaining.py::test_author_skeletons_follow_kinds`, a `tests.fakes.FakeJournal` holding the signals, and `render` patched to capture inputs. It reads no repo file.

A scratch prototype of part 1 plus exactly this change on `6e6d9154` touched part 1's files and these 7. The full unit suite (922 tests), `ruff check`, `ruff format --check` and the full integration suite (3,410 tests) passed. `./dev.py test tests/integration/test_author.py tests/integration/test_specs_json_reply_specs.py` also passed (64 tests). That includes `test_author_prompt_contains_guide_and_skeletons`, which renders the real spec with the new block. Existing Author unit tests pass unchanged, because `FakeJournal` holds no signal and the block renders `none`.

Merge order. Part 2 (`estimate-calibration-idle`) also fences `clutch/calibration.py` and `docs/how-clutch-works.md`. It inserts `due` and `calibrate_when_due` before `calibrate`, and edits sections 7.1, 7.2 and 11. This ticket appends after `render` and edits section 9.3, so either order merges and every criterion holds. `cli-group-provider` (running) and `evidence-record-doc-section` (confirmed) edit sections 2.1, 8.1 and a new 10.4 of `docs/how-clutch-works.md`, not 9.3. No other confirmed, unmerged ticket fences the other files.

Out:
- `engine calibrate`, the calculation and the signal (part 1); the idle-point cadence (part 2).
- `clutch/specs/ask/author.md` and the other operator prompts. Chat authors read the guide in full (`clutch ticket new` prints its path), so the guide line reaches them, and they run `clutch engine calibrate`.
- Any rule text in `clutch/specs/author.md`, the guide's other sections, lint's time budget rules, and the 30- and 60-minute limits.
- `CORE_TEMPLATE`, `CLAUDE.md` and `AGENTS.md`.

## Scope fence
- clutch/calibration.py
- clutch/author.py
- clutch/specs/author.md
- clutch/docs/host-authoring.md
- docs/how-clutch-works.md
- tests/integration/test_author.py
- tests/unit/test_author_calibration.py

## Acceptance criteria
1. `tests/unit/test_author_calibration.py::test_latest_reads_the_newest_calibration`: a journal with two `estimate_calibration` signals, each followed by an unrelated signal, gives `latest(events) == <the second table's rows>`, and an empty journal gives `[]`. Ruled out: the oldest table, and an exception before the first calibration.
2. `tests/unit/test_author_calibration.py::test_author_prompt_carries_the_latest_table`, parametrized. With an older table and then a newer one with the row `codex`/`m1`, 2 runs, estimates p50 45.0, actual p50 6.0 and p90 8.4, `author.author` renders inputs whose `calibration` is exactly `codex/m1: 2 runs, estimate p50 45.0m, actual p50 6.0m, actual p90 8.4m\n`. With no signal it is exactly `none\n`. Ruled out: the older table, a missing input, and an empty block before the first calibration.
3. `./dev.py test tests/integration/test_author.py` exits 0. The version pin equals the bumped `clutch/specs/author.md` version, which is one minor above main's. `test_author_prompt_contains_guide_and_skeletons` renders the real spec, whose inputs must match its data blocks exactly (`clutch/specs/__init__.py::render`).
4. `grep -c '<<clutch-data:begin calibration>>' clutch/specs/author.md` prints `1`, `grep -c 'clutch engine calibrate. journals and prints' clutch/docs/host-authoring.md` prints `1`, and `grep -c 'latest .estimate_calibration. table' docs/how-clutch-works.md` prints `1`.
5. `./dev.py test tests/unit/test_author.py tests/unit/test_closed_sets_remaining.py tests/unit/test_specs.py tests/unit/test_host_authoring.py tests/unit/test_lint_guide_parity.py` exits 0 with those files unchanged.
6. `./dev.py test` exits 0. Check's `unit` (with the coverage gate) and `integration` mechanical checks in `config.yaml` run both full suites.

## Verification
```
./dev.py test tests/unit/test_author_calibration.py tests/unit/test_author.py tests/unit/test_closed_sets_remaining.py tests/unit/test_specs.py tests/unit/test_host_authoring.py tests/unit/test_lint_guide_parity.py
./dev.py test tests/integration/test_author.py tests/integration/test_specs_json_reply_specs.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- The spec restates the estimating rule instead of the guide carrying it, or the guide changes beyond the one `Time budget` line.
- Author computes its own calibration, reads `engine.log` or the ticket files for the table, or shows a table other than the latest journaled one.
- The spec version is not bumped, or its pin is not updated to the bumped value.
- `engine calibrate`, `calibrate`, the signal body, drain, serve, or a file outside the fence changes, or an existing assertion is dropped or loosened.

## Time budget
- expected: 15m
- stuck: 30m
