---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/issue.py
- tests/unit/test_issue_link.py
- clutch/__main__.py::_parser
- clutch/docs/host-running.md#Reporting a critical clutch bug
- docs/upstream-issue-plan.md#Not the Suggestion Box
- docs/upstream-issue-plan.md#Open decisions
- tests/integration/test_hostfiles.py

## Goal / Why
A host session can send a clutch process gap upstream through `clutch box issue --class process-gap`. A process gap is a flaw in a clutch prompt spec, gate, or process that cost a real host run an Implement attempt, a review cycle, or an escalation. The five critical classes stay as they are and are still the only issues titled `[critical:<class>]`. A process-gap issue is titled `[process-gap] <title>`, so the owner can sort it below the critical ones.

Today the `CORE_TEMPLATE` rule in `clutch/hostfiles.py` allows only a critical bug upstream. A non-critical clutch problem may only be "named to the user in one line" and may not go into the host's Suggestion Box. It reaches clutch only when the owner carries it over by hand. On 2026-11-18 a host (Fungo) found that a retry fixed only the four defects the previous review named and resubmitted. The next review then found two more unmet requirements, which cost an extra review-and-retry cycle. The host's session correctly declined to file it as a critical issue. It reached clutch only because the owner relayed it (box-000757-c6238f23), and other hosts' owners will not. The owner decided on 2026-11-18 to add one evidence-bound class rather than open the tracker to ideas. A bare improvement idea with no run that paid for it still goes nowhere.

## Boundary contract
### Upstream issue classes
- disposition: extend
- owner: clutch/issue.py
- consumers: `clutch box issue`, the CORE_TEMPLATE host rule, the host-running guide
- observable change: `--class process-gap` is accepted and titled `[process-gap] <title>`
- compatibility: the five critical classes and their `[critical:<class>]` titles are unchanged
- acceptance: process-gap links carry the new prefix; critical links are unchanged
- tests: tests/unit/test_issue_link.py
- post-merge source of truth: clutch/issue.py

## Scope in / Scope out
Scope in:
- `clutch/issue.py`:
  - Rename the current five-class tuple to `CRITICAL = ("state-loss", "secret-leak", "bad-merge", "engine-stuck", "wrong-refusal")`.
  - Define `CLASSES = CRITICAL + ("process-gap",)`.
  - `link` accepts any member of `CLASSES`. The title prefix is `[critical:<class>]` for a member of `CRITICAL` and `[process-gap]` for `process-gap`.
  - The unknown or missing class refusal keeps the message `--class must be one of: <CLASSES joined by ", ">`. Its paved road becomes `only a critical bug, or a process gap that cost a real run an attempt or review cycle, is filed upstream; name anything else to the user in chat instead`.
  - Nothing else in the module changes.
- `clutch/__main__.py`, `_parser`, `box` group and `issue` subcommand only:
  - The group description becomes `File ideas into the Suggestion Box, settle its messages, and link critical clutch bugs and process gaps upstream.`
  - The `issue` summary becomes `print a prefilled upstream issue link`.
  - `does` becomes `Print a prefilled GitHub new-issue link for a critical clutch bug or a process gap; submit nothing.`
  - Add a second example: `clutch box issue --class process-gap "<title>" --body body.md`.
  - The `--class` help still joins `issue.CLASSES`.
- `clutch/hostfiles.py` `CORE_TEMPLATE`, the "Outside clutch's own repo" rule only: replace `Only a bug in a `clutch box issue` critical class goes upstream:` with `A critical bug or process gap that cost a run a cycle goes upstream:` (68 bytes for 64; `CORE_TEMPLATE` was 8,186 bytes at authoring, leaving 8,190). Measure the byte budget against `CORE_TEMPLATE` on main when Implement runs, not at authoring. `boundary-contract-authoring` (merged at `a79b00e4`) already spent most of the remaining budget. The edit must leave the template at or under the 8,192-byte cap in `tests/integration/test_hostfiles.py`. If the replacement does not fit, shorten only this rule's new wording; the phrase `process gap that cost a run a cycle` must stay. Never reword another rule. Then run `uv run clutch host core` to refresh the managed blocks in `CLAUDE.md` and `AGENTS.md`. Run it again from `hosts/fixture` to refresh `hosts/fixture/CLAUDE.md`. Never hand-edit any of these blocks. Then regenerate `GOLDEN` in `tests/integration/test_hostfiles.py` with `uv run python -m tests.integration.test_hostfiles`, the file's own `__main__` generator, and change nothing else in that file.
- `clutch/docs/host-running.md`:
  - The `box issue` verb-table row says it prints a link for a critical clutch bug or a process gap.
  - Rename the section heading `## Reporting a critical clutch bug` to `## Reporting a clutch problem upstream`.
  - Its channel table's upstream row carries "a critical clutch bug or a process gap, confirmed by the person".
  - After the critical class list, add a `process-gap` bullet: a clutch prompt spec, gate, or process flaw that cost a real run an Implement attempt, a review cycle, or an escalation. The body names the clutch file at fault and the run's evidence (attempt count and the review findings that show the gap), and leaves out the same host-private material as the critical body. A bare idea with no run that paid for it is named to the user in chat and goes nowhere else.
  - Change the sentence "Name a clutch problem outside these classes to the user in chat" only as far as needed to stay true.
- `docs/how-clutch-works.md`: the section 12 bullet that says only a critical-class bug goes upstream now names critical bugs and process gaps, and its link anchor becomes `#reporting-a-clutch-problem-upstream`. The section 2.1 `box issue` row stays unless its text becomes false.
- `README.md`: the `uv run clutch box issue` comment becomes `# link to report a critical clutch bug or process gap upstream`.
- `docs/upstream-issue-plan.md`:
  - The opening "Only critical bugs go upstream" paragraph and the "Not the Suggestion Box" non-critical bullet name the process-gap exception.
  - Open decision 1 records that `process-gap` was added on 2026-11-18 (`docs/roadmap.md` §6, decision 23).
- `docs/roadmap.md` §6: add a `Decided 2026-11-18:` line and decision 23, which records the `process-gap` class, its evidence bar, its `[process-gap]` title prefix, and that it amends decision 10.
- `tests/unit/test_issue_link.py::test_classes_are_closed`: update it to the new `CRITICAL` and `CLASSES` tuples and the new paved-road text.
- New `tests/unit/test_issue_process_gap.py` with the process-gap tests named in the acceptance criteria.

Scope out:
- No GitHub label, issue template, API call, or `gh` use. The link still prefills title and body only.
- No change to the body footer, secret scrubbing, the 3,000-byte limit, the lock, or the integration tests in `tests/integration/test_issue_verb.py`, which keep passing unchanged.
- No autonomous surface (triage, retro, Author, harvest) prepares an upstream issue. That ban in the plan and in host-running.md stands.
- The retry re-audit improvement itself (box-000757-c6238f23) is separate work.

## Scope fence
- clutch/issue.py
- clutch/__main__.py
- clutch/hostfiles.py
- tests/integration/test_hostfiles.py
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md
- docs/upstream-issue-plan.md
- docs/roadmap.md
- tests/unit/test_issue_link.py
- tests/unit/test_issue_process_gap.py

## Acceptance criteria
1. `tests/unit/test_issue_link.py::test_classes_are_closed` checks three things. `issue.CRITICAL` equals the five critical classes in order. `issue.CLASSES == issue.CRITICAL + ("process-gap",)`. `link("minor-annoyance", ...)` and `link(None, ...)` each raise `runner.Refusal` whose text contains all six class names and the new paved road. It rules out a seventh or missing class, and the old "only critical bugs are filed upstream" road.
2. `tests/unit/test_issue_process_gap.py::test_process_gap_title_prefix` checks that `link("process-gap", "retry skips re-audit", "body", str)` builds a URL whose `title` query value is exactly `[process-gap] retry skips re-audit`. It rules out `[critical:process-gap] ...` and an unprefixed title.
3. `tests/unit/test_issue_process_gap.py::test_critical_prefix_unchanged` checks that every member of `issue.CRITICAL` still yields the title `[critical:<class>] t`. It rules out a critical class losing its prefix.
4. `tests/unit/test_issue_process_gap.py::test_main_accepts_process_gap` checks that `cli.main(["box", "issue", "--class", "process-gap", "t", "--body", "body.md"], ...)` with load_config faked returns 0 and prints one link. It rules out argparse or the verb refusing the new class.
5. `tests/integration/test_hostfiles.py` passes against main's template at Implement time, so `CORE_TEMPLATE` stays at or under 8,192 bytes, still contains `is never copied or patched into host files`, and matches the regenerated `GOLDEN` (`test_core_golden_uses_branch_template`). `tests/integration/test_core_supervisor_verdicts.py` and `tests/integration/test_fixture_host.py` pass, so `hosts/fixture/CLAUDE.md`'s managed block equals the template. The `## Verification` grep checks that `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` each contain `process gap that cost a run a cycle`.
6. The `## Verification` docs check passes. `clutch/docs/host-running.md` has a `## Reporting a clutch problem upstream` section that names `process-gap` and all five critical classes. `docs/how-clutch-works.md` links `#reporting-a-clutch-problem-upstream` and no longer links `#reporting-a-critical-clutch-bug`. `README.md` mentions `process gap` on its `clutch box issue` line.

## Verification
```
./dev.py test tests/unit/test_issue_link.py tests/unit/test_issue_process_gap.py tests/integration/test_issue_verb.py tests/integration/test_hostfiles.py tests/integration/test_core_supervisor_verdicts.py tests/integration/test_fixture_host.py tests/unit/test_main_help.py
uv run python -c "import pathlib; r = lambda p: pathlib.Path(p).read_text(); h = r('clutch/docs/host-running.md').split('## Reporting a clutch problem upstream', 1)[1]; assert all(w in h for w in ('process-gap', 'state-loss', 'secret-leak', 'bad-merge', 'engine-stuck', 'wrong-refusal')); w = r('docs/how-clutch-works.md'); assert '#reporting-a-clutch-problem-upstream' in w and '#reporting-a-critical-clutch-bug' not in w; assert any('clutch box issue' in l and 'process gap' in l for l in r('README.md').splitlines()); assert all('process gap that cost a run a cycle' in r(p) for p in ('CLAUDE.md', 'AGENTS.md', 'hosts/fixture/CLAUDE.md'))"
```

## Definition of rejected
- A critical-class issue title is no longer `[critical:<class>] <title>`, or any existing `tests/integration/test_issue_verb.py` assertion changes.
- `CORE_TEMPLATE` exceeds 8,192 bytes, or another `CORE_TEMPLATE` rule is reworded or dropped to make room.
- The `CLAUDE.md`, `AGENTS.md`, or `hosts/fixture/CLAUDE.md` managed block is edited by hand instead of refreshed with `clutch host core`.
- The class list becomes open, such as a free-form class or a catch-all like `improvement`.
- Any autonomous surface gains a path to prepare an upstream issue.

## Time budget
- expected: 20m
- stuck: 40m
