---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
---

## Depends on
- closed-sets-single-owner

## Context
- clutch/tickets.py::Kind
- clutch/tickets.py::template
- clutch/tickets.py::lint_findings
- clutch/tickets.py::evidence_findings
- clutch/tickets.py::missing_evidence_findings
- clutch/__main__.py::_new
- tests/unit/test_closed_sets_single_owner.py::test_owner_constants
- tests/integration/test_hostfiles.py::test_core_golden_uses_branch_template
- docs/gemini-graphics-refactor-plan.md#B1. Grammar and authoring (`graphics-kind`)

## Goal / Why
A ticket can be `kind: graphics`. Today `kind` is the closed set `feature|bug|chore` in `clutch/tickets.py`, so visual work (rendered pages, SVG, flowcharts, or model-generated images) has no ticket shape. After this ticket:
- `Kind` and `KINDS` in `clutch/tickets.py` gain `graphics`. `--kind` choices, the stats kind loop and the Author skeleton list follow, because they derive from `KINDS`.
- `## Render` is an optional section that is required on `graphics` and refused on every other kind. It carries `- mode: command|generate`, `- artifact:` paths, and `- input:` (generate only), `- reference:` and `- candidates:` (generate only, 1 to 5, default 3). In `command` mode it also carries one fenced render command plus `- carries:` prefixes.
- `clutch ticket new <stem> --kind graphics [--reference FILE...] [--input FILE...]` copies those files to `tickets/<stem>/reference/`, as `--evidence` does for bugs.
- Lint enforces the structure the plan gives: each `- visual: <artifact>: <observable>` criterion names a declared artifact, a graphics ticket has at least one non-visual (mechanical) criterion, and a `generate` ticket names at least one `input:` or has text in `## Goal / Why` (the prompt).
- The authoring guide gains a Graphics tickets section, and CORE_TEMPLATE's kind list gains `|graphics` (9 bytes).

This is the grammar and authoring row only. Render checking, routing, image gates, the visual judge and candidates belong to later rows of the plan.

## Boundary contract
### Ticket kind set and Render grammar
- disposition: extend
- owner: clutch/tickets.py
- consumers: `clutch ticket new`, lint and intake, the Author skeleton list in `clutch/author.py`, `clutch/stats.py` kind rows, `--kind` choices in `clutch/__main__.py`
- observable change: `graphics` is a valid kind with its own template. `## Render` is refused on non-graphics kinds and required on graphics. A malformed Render block or an undeclared visual artifact yields a finding with a paved road.
- compatibility: feature, bug and chore tickets parse and lint exactly as before. No existing ticket uses `## Render`.
- acceptance: criteria 1 to 7 below
- tests: new `tests/unit/test_graphics_kind.py`; the flipped assertions in `tests/unit/test_closed_sets_single_owner.py` and the closed-set tuples in `tests/integration/test_closed_sets.py`
- post-merge source of truth: clutch/tickets.py

### ticket new reference and input files
- disposition: extend
- owner: clutch/__main__.py (`_new`)
- consumers: operators and Author authoring a graphics ticket
- observable change: `--reference` and `--input` copy regular non-symlink files with distinct names into `tickets/<stem>/reference/`. They are refused for any other kind. `--input` is refused unless the kind is graphics.
- compatibility: `--evidence` behavior for bug tickets is unchanged.
- acceptance: criterion 8
- tests: new `tests/unit/test_graphics_new.py`
- post-merge source of truth: clutch/__main__.py

### Authoring guide and CORE_TEMPLATE kind list
- disposition: extend
- owner: clutch/docs/host-authoring.md for ticket content; `CORE_TEMPLATE` in clutch/hostfiles.py for the agent-conduct kind list
- consumers: authors reading the guide; every host's managed block in CLAUDE.md and AGENTS.md rendered by `clutch host core`
- observable change: the guide documents graphics tickets. The template reads `feature|bug|chore|graphics`. The managed blocks are re-rendered, and the `GOLDEN` render pinned in `tests/integration/test_hostfiles.py` is regenerated.
- compatibility: the template stays within the 8192-byte cap in `tests/integration/test_hostfiles.py`.
- acceptance: criterion 9
- tests: existing `tests/integration/test_hostfiles.py` size, golden and drift checks
- post-merge source of truth: clutch/docs/host-authoring.md and clutch/hostfiles.py

## Scope in / Scope out
In:
- `clutch/tickets.py`: add `graphics` to `Kind`. Add `Render` to the optional sections. Parse and validate `## Render` (mode, artifact, input, reference, candidates, optional fenced command and carries). Refuse it on non-graphics kinds and require it on graphics. Add the lint rules above. The `template()` error text names all four kinds, and graphics gets a `## Render` placeholder.
- `clutch/tickets.py` backtick rule: on `kind: graphics`, an acceptance item of the form `- visual: <artifact>: <observable>` whose `<artifact>` matches a declared `artifact:` counts as naming its check, because the artifact is the check, so it is exempt from the 'names no check' backtick refusal in `validate_ticket`. Every other criterion on a graphics ticket, and every criterion on every other kind, keeps the backtick rule unchanged. A `- visual:` item whose artifact is not declared is not exempt; it gets the undeclared-artifact finding. The guide's Graphics section states this, and keeps the phrase 'every criterion names a check in backticks' in `host-authoring.md` as it is, because `tests/integration/test_lint_guide_parity.py` pins it.
- `clutch/__main__.py`: add `--reference` and `--input` to `ticket new` and copy them in `_new`. Update the command help and examples for the new flags.
- `clutch/hostfiles.py`: change the kind list in CORE_TEMPLATE to `feature|bug|chore|graphics` and nothing else. Re-render the managed blocks in `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` with `uv run clutch host core`, never by hand.
- `tests/integration/test_hostfiles.py`: after the CORE_TEMPLATE edit, regenerate only the `GOLDEN` line with `uv run python -m tests.integration.test_hostfiles` (the module's `__main__` rewrite). Change nothing else in that file.
- `clutch/docs/host-authoring.md`: change the kind list in Workflow step 1, and add a Graphics tickets section after Bug tickets. It covers both modes, the Render block, artifacts, inputs and references, the visual and mechanical criterion forms, and preferring a mechanical criterion where a test can decide it.
- `docs/how-clutch-works.md`: update only the section that names `--kind feature|bug|chore`.
- `tests/unit/test_closed_sets_single_owner.py`: `graphics` is now valid. Change only the loop that uses it as the invalid kind (use another value such as `epic`), the `KINDS` equality assertion, and the `template("graphics")` ValueError assertion (use an invalid kind).
- `tests/integration/test_closed_sets.py`: add `Render` to the `OPTIONAL_SECTIONS` tuple (line 314) and to the full `SECTIONS` tuple (lines 328-342), and add `graphics` to `FRONTMATTER_VOCABULARIES['kind']` (line 366, with the matching kind assertion near line 380). Change nothing else in that file.
- New tests in `tests/unit/test_graphics_kind.py` and `tests/unit/test_graphics_new.py`.

Out:
- Render command execution at Check (`graphics-render-check`).
- Routing by kind, the image gate, the visual judge, candidates and select commit, the visual baseline, and the `requisition_review.md`, `implement.md` and `review.md` spec blocks.
- Per-row threshold syntax in criteria (open decision 1 of the plan).
- Capping `input:` count at the routed model's limit. This ticket uses the plan's interim cap of 3.
- The `--kind` list in `README.md` and `vscode-clutchwork/README.md`, which do not name it.
- A `clutch host core --check` option, which `docs/roadmap.md` records as dropped.

## Scope fence
- clutch/tickets.py
- clutch/__main__.py
- clutch/hostfiles.py
- clutch/docs/host-authoring.md
- docs/how-clutch-works.md
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- tests/integration/test_hostfiles.py
- tests/unit/test_closed_sets_single_owner.py
- tests/integration/test_closed_sets.py
- tests/unit/test_graphics_kind.py
- tests/unit/test_graphics_new.py

## Acceptance criteria
1. `tickets.KINDS == ("feature", "bug", "chore", "graphics")` and `tickets.template("graphics")` contains a `## Render` section, checked by `./dev.py test tests/unit/test_graphics_kind.py`. A feature template has no `## Render`.
2. A graphics ticket with a valid `mode: generate` Render block (one input, one artifact, `candidates: 3`) parses, checked by `./dev.py test tests/unit/test_graphics_kind.py`. `mode: other`, `candidates: 0` and `candidates: 6` each raise `TicketInvalid`, not parse.
3. `## Render` on a `kind: feature` ticket raises `TicketInvalid`, and a `kind: graphics` ticket without `## Render` raises `TicketInvalid`, checked by `./dev.py test tests/unit/test_graphics_kind.py`.
4. A `mode: command` block follows the `## Regression` rules, checked by `./dev.py test tests/unit/test_graphics_kind.py`. Parse-time `TicketInvalid`: zero fenced commands, two fenced commands, no `carries:` bullet, or an `input:` or `candidates:` bullet in command mode. Lint findings: the one fenced command names no path under any `carries:` prefix, or a `carries:` prefix is not inside `## Scope fence`. Passing fixture: command `uv run python tests/render/home.py`, `carries: tests/render`, and `tests/render` in the fence, which parses and yields no Render finding. Failing fixtures: (a) two fenced commands raise `TicketInvalid`; (b) command `uv run python scripts/home.py` with `carries: tests/render` yields a finding, not a pass; (c) command under `tests/render` with `tests/render` absent from the fence yields a finding, not a pass.
5. On a `kind: graphics` ticket declaring `artifact: assets/hero.png`, the backtick-free criterion `- visual: assets/hero.png: the product sits at the left third` parses without `TicketInvalid` and yields no finding, while `- visual: other.png: the product sits at the left third` (artifact not declared) yields an undeclared-artifact finding, checked by `./dev.py test tests/unit/test_graphics_kind.py`. The identical backtick-free `- visual: assets/hero.png: ...` item on a `kind: feature` ticket still raises `TicketInvalid` with 'names no check', not a pass.
6. A graphics ticket whose criteria are all `- visual:` items with declared artifacts yields a finding, and adding one non-visual criterion that names a check in backticks (for example `1. ` followed by a backticked `./dev.py test tests/unit/test_x.py`) clears it, checked by `./dev.py test tests/unit/test_graphics_kind.py`.
7. A `generate` ticket with no `input:` and an empty prompt yields a finding, and with one `input:` (or a Goal / Why prompt) it does not. Four `input:` lines yield a finding, checked by `./dev.py test tests/unit/test_graphics_kind.py`.
8. `ticket new hero --kind graphics --reference a.png --input b.png` writes `tickets/hero/reference/a.png` and `tickets/hero/reference/b.png` and exits 0. `--input` with `--kind feature` exits 2 and writes nothing. Duplicate names and symlinks exit 2, checked by `./dev.py test tests/unit/test_graphics_new.py`.
9. `len(hostfiles.CORE_TEMPLATE) <= 8192`, the regenerated `GOLDEN` matches `hostfiles.render(b"")`, and the drift checks in `tests/integration/test_hostfiles.py` pass for CLAUDE.md, AGENTS.md and hosts/fixture/CLAUDE.md, checked by `./dev.py test tests/integration/test_hostfiles.py tests/unit/test_hostfiles_supervisor_verdicts.py`.
10. The full suite passes, including `tests/unit/test_closed_sets_single_owner.py`, `tests/integration/test_closed_sets.py`, `tests/unit/test_main_help.py` and `tests/integration/test_tickets.py`, checked by `./dev.py test`.

## Verification
```
./dev.py test
```

## Definition of rejected
A kind other than graphics gains `## Render` behavior. A visual criterion is judged by a denylist of words instead of the declared-artifact rule. Existing feature, bug or chore tickets stop linting. CORE_TEMPLATE exceeds 8192 bytes, the managed blocks drift, or `tests/integration/test_hostfiles.py` changes beyond the `GOLDEN` line.

## Time budget
- expected: 30m
- stuck: 60m