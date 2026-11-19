---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- projection-helpers-single-owner

## Context
- docs/roadmap.md#2.3 Repeated helpers and projections
- clutch/tickets.py::split_frontmatter
- clutch/tickets.py::_load_frontmatter
- clutch/tickets.py::_sections
- clutch/tickets.py::_bullets
- clutch/tickets.py::_BUDGET
- clutch/observe.py::frontmatter
- clutch/observe.py::depends
- clutch/observe.py::capability
- clutch/retro.py::production_evidence
- clutch/__main__.py::_stats
- clutch/specs/__init__.py::load_spec
- tests/unit/test_menu_admission.py
- tests/unit/test_verdict_menu_parity.py

## Goal / Why
Roadmap row 144 (`docs/roadmap.md` §2.3, the bullet "Ticket metadata still read outside the owner", left out of row 125 by `projection-helpers-single-owner`). At HEAD three modules read ticket metadata by hand, because they must read tickets that fail validation, where `tickets.parse_ticket` raises:

- `clutch/observe.py::frontmatter` splits on `---` and applies a `key: value` regex; `clutch/observe.py::depends` splits the text on `## Depends on` and applies a `^- (\S+)` regex. They feed the blocked rows of `clutch watch` / `view snapshot` (`queue`, `snapshot`'s row `base`) and the ticket tier in `capability`.
- `clutch/retro.py::production_evidence` reads `expected` from ticket text at old merge commits with `re.search(r"^- expected: (\d+)m$", ...)`.
- `clutch/__main__.py::_stats` calls `tickets.split_frontmatter` and then `yaml.safe_load` itself to read `kind`.

`observe.frontmatter` also reads prompt-spec frontmatter (`clutch/specs/resolve.md`, `clutch/specs/requisition_review.md`) in `capability`; the row says those reads stay with `clutch/specs/`, so they move to `clutch.specs.load_spec(...).meta`, the spec owner's reader, and `observe.frontmatter` then reads only tickets.

After this change `clutch/tickets.py` owns one tolerant reader, `read_tolerant(text: str) -> TolerantTicket`, that returns what parses from ticket text without raising, and all three modules use it. Why: each hand-written reader is a place a format change (a frontmatter key, a section rule, the budget bullet) must be found by hand, and the three already disagree with the strict parser (the old `depends` regex keeps backticks that `_bullets` strips).

## Boundary contract
### Tolerant ticket reader
- disposition: create
- owner: clutch/tickets.py
- consumers: `observe.frontmatter`, `observe.depends`, `retro.production_evidence`, `__main__._stats`
- observable change: new frozen dataclass `TolerantTicket(frontmatter: dict[str, object], depends: tuple[str, ...], expected_minutes: int | None)` and function `read_tolerant(text: str) -> TolerantTicket`. Inputs: ticket text. Outputs: `frontmatter` is the YAML mapping between the `---` fences (via `split_frontmatter`), or `{}` when the fences are missing, the YAML is invalid, or it is not a mapping. The body is the text after the frontmatter, or the whole text when there is none; it is split with `_sections` (findings ignored). `depends` is the `## Depends on` bullets as `_bullets` returns them (backticks stripped), `()` when the section is absent or `none`. `expected_minutes` is the integer of the first `## Time budget` bullet matching `_BUDGET` with key `expected`, else `None`. Failures: none; it never raises on any `str` input. Side effects: none; no I/O.
- compatibility: `parse_ticket`, `validate_ticket` and every strict reader are unchanged; nothing existing is removed from `clutch/tickets.py`.
- acceptance: acceptance criteria 1-3
- tests: tests/unit/test_tickets_tolerant_reader.py
- post-merge source of truth: clutch/tickets.py::read_tolerant
- closest existing: `tickets.parse_ticket` / `validate_ticket` raise `TicketInvalid` on a ticket that fails validation, which is exactly the input these callers must read; `split_frontmatter` and `_load_frontmatter` cover only the frontmatter half and `_load_frontmatter` returns findings the callers would each have to discard by hand.
- earning reason: consolidation of evidenced duplicates: three hand-written readers in `observe.py`, `retro.py` and `__main__.py`, listed in roadmap §2.3.

### observe ticket metadata readers
- disposition: extend
- owner: clutch/observe.py
- consumers: `observe.capability`, `observe.queue`, the snapshot row builder `base` in `observe.snapshot`, and the tests that monkeypatch `observe.frontmatter` and `observe.depends` (`tests/unit/test_menu_admission.py`, `tests/unit/test_verdict_menu_parity.py`, `tests/integration/test_menu_verb_parity.py`)
- observable change: `observe.frontmatter(path)` and `observe.depends(path)` keep their names and `Path` parameter and delegate to `tickets.read_tolerant(path.read_text())` (`.frontmatter`, `.depends`). `frontmatter` still returns `{}` on `OSError`. Values are now YAML-typed (a quoted or plain string stays a string), invalid YAML yields `{}` instead of whatever lines the regex matched, and `depends` strips backticks as the strict parser does.
- compatibility: valid tickets give the same `state`, `priority`, `agent_tier`, `agent_effort` strings and the same depends list as before, so `clutch watch` text and the snapshot are unchanged for them; the monkeypatching tests need no edit.
- acceptance: acceptance criteria 4-5
- tests: tests/unit/test_tickets_tolerant_reader.py
- post-merge source of truth: clutch/tickets.py::read_tolerant

### Capability spec reads
- disposition: reuse
- owner: clutch/specs/__init__.py::load_spec
- consumers: `observe.capability` for surfaces `resolve` and `requisition_review`
- observable change: none; `capability` reads `tier` and `effort` from `load_spec(<spec text>).meta` instead of `observe.frontmatter`, giving the same `tier/effort` text for the shipped specs.
- compatibility: `clutch watch`'s "asked for tier/effort" line is unchanged.
- acceptance: acceptance criterion 6
- tests: tests/integration/test_tolerant_reader_callers.py
- post-merge source of truth: clutch/specs/__init__.py::load_spec

### Retro calibration and stats kinds
- disposition: reuse
- owner: clutch/tickets.py::read_tolerant
- consumers: `retro.production_evidence` (`predicted_seconds`), `__main__._stats` (`kinds` passed to `stats.project_stats`)
- observable change: none for valid tickets; `predicted_seconds` and the kinds map are preserved. `_stats` still skips a ticket whose file is unreadable or whose `kind` is not in `KINDS`.
- compatibility: retro report and `clutch view stats` output unchanged for every ticket the old code read.
- acceptance: acceptance criteria 7-8
- tests: tests/unit/test_tickets_tolerant_reader.py, tests/integration/test_retro.py
- post-merge source of truth: clutch/tickets.py::read_tolerant

## Scope in / Scope out
In:
- `clutch/tickets.py`: add `TolerantTicket` and `read_tolerant` as in the boundary contract, next to `split_frontmatter`, reusing `split_frontmatter`, `_sections`, `_bullets` and `_BUDGET`; YAML errors are caught there (`yaml.YAMLError`).
- `clutch/observe.py`: `frontmatter` and `depends` bodies delegate to `read_tolerant` (import it from `clutch.tickets`); `frontmatter`'s return annotation becomes `dict[str, object]`. In `capability`, the two spec reads use `load_spec((Path(__file__).parent / "specs" / f"{surface}.md").read_text()).meta` (import `load_spec` from `clutch.specs`); the ticket read stays `frontmatter(...)`. The `re` import stays (still used elsewhere in the module).
- `clutch/retro.py`: in `production_evidence`, replace the `re.search(r"^- expected: ...")` with `read_tolerant(text).expected_minutes`; `predicted_seconds` stays `minutes * 60` or `None`. The `re` import stays (`_REPORT`).
- `clutch/__main__.py`: in `_stats`, replace `split_frontmatter` + `yaml.safe_load` with `read_tolerant(...).frontmatter.get("kind")`; the `except` becomes `except OSError, UnicodeError:`. Remove `import yaml` from `__main__.py` (no other use at HEAD); keep the `split_frontmatter` import (`_verdict` still uses it).
- `docs/roadmap.md`: delete only the §2.3 bullet beginning "Ticket metadata still read outside the owner"; no row and no other text changes.
- New tests: `tests/unit/test_tickets_tolerant_reader.py` (pure text and `tmp_path` only) and `tests/integration/test_tolerant_reader_callers.py` (repo files).

Out: `_verdict`'s strict frontmatter read in `__main__.py` (it must refuse invalid frontmatter, not tolerate it); `clutch/specs/` code (only called); prompt specs; the strict parser; roadmap row 144 itself (the driver strikes it on merge); the rows `storm-producer-one-builder` and `projection-leftovers` (their own stems); `tests/unit/test_menu_admission.py`, `tests/unit/test_verdict_menu_parity.py` and `tests/integration/test_menu_verb_parity.py` (names and signatures they patch stay, so they are not edited). Unmerged `document-agent-roadmap-prompt` (confirmed, blocked) and draft `box-issue-process-gap-class` also fence `clutch/__main__.py`, but edit `_parser`, the `ask` path and help only; neither touches `_stats` or the `yaml` import, so either merge order applies cleanly. No unmerged ticket fences `clutch/tickets.py`, `clutch/observe.py` or `clutch/retro.py`.

## Scope fence
- clutch/tickets.py
- clutch/observe.py
- clutch/retro.py
- clutch/__main__.py
- docs/roadmap.md
- tests/unit/test_tickets_tolerant_reader.py
- tests/integration/test_tolerant_reader_callers.py

## Acceptance criteria
1. `tests/unit/test_tickets_tolerant_reader.py::test_valid_ticket`: for a hand-written valid ticket text with frontmatter `kind: chore`, `## Depends on` bullets `` - `alpha` `` and `- beta`, and a `## Time budget` of `- expected: 20m` / `- stuck: 40m`, `read_tolerant` returns `frontmatter["kind"] == "chore"`, `depends == ("alpha", "beta")` (not `` ("`alpha`", "beta") ``), and `expected_minutes == 20` (not `None`).
2. `tests/unit/test_tickets_tolerant_reader.py::test_invalid_ticket_reads_what_parses`: a ticket whose frontmatter has a key outside `Frontmatter` (so `tickets.parse_ticket` raises `TicketInvalid`, asserted in the test) still yields its `state` and its depends; a ticket whose YAML is invalid (`state: [`) yields `frontmatter == {}` while its `depends` and `expected_minutes` still parse; `## Depends on` of `none` yields `()`, not `("none",)`.
3. `tests/unit/test_tickets_tolerant_reader.py::test_never_raises`: `read_tolerant` on `""` and on text whose frontmatter is a YAML list returns `TolerantTicket({}, (), None)` without raising, and on text with no fences but a `## Depends on` bullet `- gamma` returns `frontmatter == {}` and `depends == ("gamma",)`.
4. `tests/unit/test_tickets_tolerant_reader.py::test_observe_readers_delegate`: `observe.frontmatter` and `observe.depends` on a `tmp_path` ticket file equal `read_tolerant(text).frontmatter` and `list(read_tolerant(text).depends)`; `observe.frontmatter` on a missing path returns `{}`, not an exception.
5. `./dev.py test tests/unit/test_menu_admission.py tests/unit/test_verdict_menu_parity.py tests/integration/test_menu_verb_parity.py` exits 0 with those files unedited.
6. `tests/integration/test_tolerant_reader_callers.py::test_capability_spec_reads`: `observe.capability(ctx, [], stem, "resolve")` and `(..., "requisition_review")` with a `ctx` whose root has no ticket file return `"<tier>/<effort>"` built from `load_spec` of the shipped `clutch/specs/resolve.md` and the ticket default tier with the `requisition_review.md` effort; the test computes the expected strings from `load_spec`, not literals.
7. `tests/unit/test_tickets_tolerant_reader.py::test_stats_reads_kind_from_invalid_ticket`: `__main__._stats` with a fake checkout whose `repo` is `tmp_path`, events for two stems (one ticket with `kind: bug` plus an extra unknown frontmatter key, one with `kind: nonsense`) and `clutch.stats.project_stats` monkeypatched to capture its `kinds` argument, passes `{"<first stem>": "bug"}`: the invalid-but-readable ticket is kept and the unknown kind is dropped.
8. `./dev.py test tests/integration/test_retro.py` exits 0; its existing `calibration_divergence` assertion (`predicted_seconds: 600`) still holds.
9. `tests/integration/test_tolerant_reader_callers.py::test_no_hand_readers`: a source scan of `clutch/observe.py`, `clutch/retro.py` and `clutch/__main__.py` finds no `yaml.safe_load`, no `"## Depends on"` literal, no `expected: (` regex and no `split("---"`; the pre-change tree fails it.
10. `./dev.py test` exits 0; review checks that the §2.3 bullet "Ticket metadata still read outside the owner" is gone from `docs/roadmap.md` and nothing else in that file changed (no standing test pins roadmap text).

## Verification
```
./dev.py test tests/unit/test_tickets_tolerant_reader.py tests/integration/test_tolerant_reader_callers.py tests/unit/test_menu_admission.py tests/unit/test_verdict_menu_parity.py tests/integration/test_menu_verb_parity.py tests/integration/test_retro.py
./dev.py test
```

## Definition of rejected
`parse_ticket` or `validate_ticket` behavior changes; `read_tolerant` raises on any input or does I/O; a hand-written frontmatter, depends or expected reader remains in `observe.py`, `retro.py` or `__main__.py`; `_verdict`'s strict read is made tolerant; `observe.frontmatter` or `observe.depends` is renamed or loses its `Path` parameter (breaking the monkeypatching tests); the spec reads in `capability` use the ticket reader; any `docs/roadmap.md` change beyond the one §2.3 bullet; an existing test is weakened or edited.

## Time budget
- expected: 25m
- stuck: 50m
