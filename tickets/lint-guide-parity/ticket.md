---
state: confirmed
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/tickets.py::lint_findings
- clutch/docs/host-authoring.md
- tests/unit/test_ticket_lint_rules.py

## Goal / Why
The authoring guide and `clutch lint` state the same rules. Today `_parse_ticket` in `clutch/tickets.py` enforces rules the guide never states, and the guide states rules lint never checks. After this change every rule `tickets.py` lints is in `clutch/docs/host-authoring.md`. The two guide rules that lint can decide mechanically are linted: a ticket that bumps a prompt spec version fences a test pin, and a ticket that names a document in Scope in fences it. The third rule the roadmap row names, that each `## Depends on` ticket exists, is already linted (`_parse_ticket` refuses a stem with no `tickets/<stem>/ticket.md`); this ticket only adds it to the guide and pins it with a test. This is roadmap row 23 (`docs/roadmap.md`). Why it matters: Author embeds only the guide, so a lint rule absent from the guide is learned by a failed run, and a guide rule absent from lint is caught only by an LLM reviewer.

## Scope in / Scope out
In, `clutch/tickets.py`: `lint_findings` gains two findings, each with a paved road and each reported once per ticket.
- Spec pin: when the fence holds a path equal to or under `clutch/specs/` that ends `.md`, the `## Scope in / Scope out` text contains the word `version` (case-insensitive, whole word), and no fence entry is equal to or under `tests/`, report that a bumped prompt spec needs a fenced test pin. Road: fence the test that pins the spec file.
- Named document: for each token ending `.md` in the part of `## Scope in / Scope out` before its first `Out:` (the whole text when `Out:` is absent), when the token is an existing repo file, is not under `tickets/`, and is not equal to or under any fence entry, report it. Road: fence the document and say which part to update, or drop the mention.

In, `clutch/docs/host-authoring.md`: state each rule `_parse_ticket` and `lint_findings` enforce that the guide lacks. Add only these sentences, in the section that owns each: `## Depends on` and `## Runs before` stems name existing tickets, never the ticket itself, and never close a cycle; `Context` never lists a `clutch/specs/*.md` prompt spec (list it under `On-demand` and fence it); an `On-demand` path is fenced and is not also in `Context`; the words `improved`, `better` and `cleaner` are refused in `Acceptance criteria`; every criterion names a check in backticks; `stuck` must exceed `expected`; `## Regression` appears only in a `kind: bug` ticket. Add one sentence each for the two new lint rules above. Edit nothing else in the guide.

In, tests: new `tests/unit/test_lint_guide_parity.py` builds tickets under `tmp_path` and calls `tickets.parse_ticket` and `tickets.lint_findings`; no process and no repo file is read, so it covers the new `tickets.py` lines (`clutch/tickets.py` has a positive floor in `test-gate.toml`). New `tests/integration/test_lint_guide_parity.py` reads the real guide, because it needs a repo file.

Out: no change to `_parse_ticket` grammar, to `## Depends on` resolution, to any other lint rule, to prompt specs, or to `tests/unit/test_ticket_lint_rules.py` (read for fixture style only). No `clutch/specs/*.md` is edited, so no spec version bump happens in this ticket. Existing tickets are not rewritten.

## Scope fence
- clutch/tickets.py
- clutch/docs/host-authoring.md
- tests/unit/test_lint_guide_parity.py
- tests/integration/test_lint_guide_parity.py

## Acceptance criteria
1. In `tests/unit/test_lint_guide_parity.py`, a chore ticket whose fence holds `clutch/specs/author.md` and `clutch/x.py`, with the word `version` in Scope in, yields exactly one finding from `tickets.lint_findings` whose message names the spec pin. An empty list is the wrong result.
2. The same ticket with `tests/unit/test_specs.py` added to the fence yields `[]`, and so does a ticket that fences a spec but never uses the word `version` in Scope in (a Scope in with `versions` or `conversion` only). A non-empty list is the wrong result.
3. A ticket whose Scope in text before `Out:` names an existing `docs/guide.md` (created under `tmp_path`) that is not fenced yields exactly one finding naming `docs/guide.md`. An empty list is the wrong result.
4. The same ticket with `docs/guide.md` fenced yields `[]`; with the name moved after `Out:` it yields `[]`; with the name pointing at a file that does not exist it yields `[]`. A non-empty list is the wrong result.
5. A ticket whose `## Depends on` names a stem with no `tickets/<stem>/ticket.md` under `tmp_path` raises `tickets.TicketInvalid` from `tickets.parse_ticket` with a finding naming that stem. Returning a `Ticket` is the wrong result.
6. In `tests/integration/test_lint_guide_parity.py`, the text of `clutch/docs/host-authoring.md` contains each of these exact, case-sensitive phrases, one per added sentence: `never close a cycle` (Depends on / Runs before); `never list a prompt spec in `Context`` (Context rule); `an `On-demand` path is fenced and never also in `Context`` (On-demand rule); `refused as unmeasurable` (criterion words); `every criterion names a check in backticks` (backticks rule); `` `stuck` must exceed `expected` `` (time budget rule); `` `## Regression` appears only in a `kind: bug` ticket `` (Regression rule); `a bumped prompt spec needs a fenced test pin` (spec-pin lint rule); `a document named in `Scope in` is fenced` (named-document lint rule); and `a stem with no `tickets/<stem>/ticket.md` is refused` (Depends on existence). Each phrase is absent from the guide at base, so deleting or rewording any one added sentence makes the test fail. A guide missing any phrase is the wrong result, and a check built from words already in the guide (`kind: bug`, `version`, `test pin`) alone is not accepted.
7. `tests/unit/test_ticket_lint_rules.py` passes unchanged, so no existing fixture gains a finding.
8. `clutch lint lint-guide-parity` exits 0 on this ticket's own text.

## Verification
```
./dev.py test tests/unit/test_lint_guide_parity.py tests/integration/test_lint_guide_parity.py tests/unit/test_ticket_lint_rules.py tests/unit/test_host_authoring.py
```

## Definition of rejected
A branch that changes any `_parse_ticket` grammar rule, adds a lint rule beyond the two named, edits a file outside the fence, makes the document rule fire on a path after `Out:` or on a non-existent file, or leaves a rule in `tickets.py` unstated in the guide.

## Time budget
- expected: 40m
- stuck: 90m
