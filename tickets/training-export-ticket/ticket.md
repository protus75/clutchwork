---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
---

## Depends on
- `training-export-kinds`

## Context
- clutch/training.py
- clutch/tickets.py::Source
- tests/unit/test_main_training_group.py
- tests/unit/test_training_export.py
- docs/training-data-plan.md#3. Export: training records

## On-demand
- clutch/__main__.py

## Goal / Why
`clutch training export` writes `implement`, `preference`, `review` and `diagnosis` records today and refuses `ticket`. After this ticket `--kinds ticket` writes `ticket.jsonl`, one record per authored ticket, so a host can tune a small local model on its own ticket authoring. Each record carries `authored_by` (`human` or `author`) so a host can filter, as training plan decision 3 requires. The ticket also fixes two rules the plan left open.

**Call-to-stem link.** Author calls are keyed with no ticket stem: `llm/author/<run_seq>/author/<attempt>/<call>` (`clutch/driver.py` keys ticketless surfaces under the surface name). The call's reply is `{"stem": ..., "ticket": ...}`. The reply text is built from the normalized `message` events with role `assistant` in that call's stream, by adapter: for Claude and Codex it is the `text_blob` of the last assistant `message` event, unchanged; for Gemini, whose stream-json sends the reply as many `delta` chunks (one `message` event per stream line), it is the `text_blob`s of every assistant `message` event joined in order with no separator. The stream is read as `_trajectory` reads it: the normalizer is chosen by `start.provider.adapter` (Claude, Codex or Gemini), the stdout comes from `store.get_blob(end.raw.stdout)`, and the normalizer is called with a `put_blob` that captures each blob's bytes into a dict keyed by the returned id, so the text is recovered from that dict (the hash-only `put_blob` in `_trajectory` loses it). The closing `result` or `usage` event's `text_blob` is not used. A call belongs to stem S when that reply text parses as JSON whose `stem` equals S and `tickets/S/ticket.md` is readable. Among the matching calls for S, the one with the highest `(run_seq, attempt, call)` is the record's call. A call is skipped and counted when its adapter is unknown, its `end` record is missing or SKIP, it has no assistant `message` event, its reply does not parse, it names no readable ticket, or its blob cannot be read.

**Source mapping.** `authored_by` comes from the `source:` frontmatter of the ticket file as read: `box:<class>` maps to `author`, `human` maps to `human`, and `seed` is skipped and counted (no model call produced it). Any other value is skipped and counted. Human tickets with no linked author call have no prompt and yield no record; this is stated in the host docs line, not hidden.

Record shape: the common identity fields (`stem`, `group`, `run_seq`, `attempt`, `call_keys`, `engine_version`, `spec`, `spec_version`, `label`), plus `authored_by` and `messages` (user: the call's prompt blob text; assistant: the committed `tickets/<stem>/ticket.md` text read through the passed reader). Label is `merged` when the stem is a merged ticket, otherwise `neutral`. Requisition and lint label sources are not used; the plan's later label refinements stay out.

## Boundary contract
### Training export record kinds
- disposition: extend
- owner: clutch/training.py::render
- consumers: `clutch training export` in clutch/__main__.py, the operator who tunes a model on `ticket.jsonl`
- observable change: `--kinds` accepts `ticket`; `ticket.jsonl` holds records with `authored_by`; `report` prints a `ticket` count; the `counts` dict gains a `ticket` key; the default kinds list is unchanged at four entries, so a plain export does not write `ticket.jsonl`
- compatibility: existing kinds, files and the default export are unchanged; `counts` gains the `ticket` key and every existing key is unchanged; `report` reads `counts['ticket']` directly with no `get` fallback; `render` gains `ticket` as an allowed member of `kinds` only
- acceptance: only calls on surface `author` that link to a readable ticket with a mapped source produce records; every other author call is skipped and counted, never partly written; each record passes the same `_safe` scrub as the other kinds and is dropped and counted when it fails
- tests: tests/unit/test_training_ticket_kind.py with a fake store and fake reader; tests/unit/test_training_export.py for the `report` counts
- post-merge source of truth: clutch/training.py

## Scope in / Scope out
Scope in:
- `clutch/training.py`: add the `ticket` kind to `render` with the link and mapping above; add a `ticket` key to the counts built in `render` and a `ticket` count to `report`'s counts line.
- `clutch/__main__.py`: add `ticket` to the `--kinds` choices (not to the default list); update the training export help `does`/examples text to name it.
- `tests/unit/test_main_training_group.py`: the one expectation that may change is the choices/parse assertion that rejects `ticket`; update it to accept `ticket` and keep the four-entry default.
- `tests/unit/test_training_export.py`: add `ticket=0` to the two hand-built counts dicts passed to `training.report` (around lines 118 and 142) and to the report text the line-142 assertion compares; nothing else changes there.
- `tests/unit/test_training_ticket_kind.py`: new tests.
- `clutch/docs/host-running.md` and `docs/how-clutch-works.md`: update the `training export` verb row to name `ticket` and the `authored_by` filter.

Scope out: the `conflict` kind (`training-export-conflict`), the `triage` kind, `training eval`, the host training guide, `clutch/evidence/`, changes to how Author keys its calls, and any label source beyond merged or neutral.

## Scope fence
- clutch/training.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_training_ticket_kind.py
- tests/unit/test_main_training_group.py
- tests/unit/test_training_export.py

## Acceptance criteria
1. A store holding two author calls whose last assistant `message` text_blob replies name stem `a-ticket` (the later with the higher attempt) and a committed ticket with `source: box:retro_finding` yields exactly one record with `authored_by == "author"` built from the later call, not two and not the earlier one; checked by `./dev.py test tests/unit/test_training_ticket_kind.py`.
2. A ticket file with `source: human` and a linked author call yields `authored_by == "human"`; a `source: seed` ticket yields no record and increments the skipped count, not `None` or an empty `authored_by`; checked by `./dev.py test tests/unit/test_training_ticket_kind.py`.
3. An author call whose reply is not JSON, whose adapter is unknown, whose `end` record is missing, or whose stem has no readable `tickets/<stem>/ticket.md` writes no record and is counted skipped; `ticket.jsonl` has zero lines for it; checked by `./dev.py test tests/unit/test_training_ticket_kind.py`.
4. A ticket record whose text contains a credential shape (`AKIA` plus 16 characters) is dropped and counted in `dropped`, not written; checked by `./dev.py test tests/unit/test_training_ticket_kind.py`.
5. A held-out stem (`holdout` selecting it) produces no ticket record; checked by `./dev.py test tests/unit/test_training_ticket_kind.py`.
6. `--kinds ticket` parses with exit 0 while `--kinds bogus` exits 2, and the default `--kinds` list still has four entries without `ticket`; checked by `./dev.py test tests/unit/test_main_training_group.py`.
7. A call with surface `implement` or `review` is never read as a ticket record; with `kinds=("implement",)` `render` returns no `ticket.jsonl` key; checked by `./dev.py test tests/unit/test_training_ticket_kind.py`.
8. `training.report` called with a counts dict holding `ticket=2` prints `ticket: 2` in its counts line, and raises `KeyError` when the `ticket` key is absent, not a silent zero; checked by `./dev.py test tests/unit/test_training_ticket_kind.py`.
9. A Gemini author call whose stream splits the JSON reply across two assistant `delta` `message` events (the first holding `{"stem": "a-ticket", ` and the second the rest of the object) yields exactly one record for `a-ticket`, not a skipped call from parsing only the last fragment; a Claude call with two assistant `message` events uses only the last one; checked by `./dev.py test tests/unit/test_training_ticket_kind.py`.

## Verification
```
./dev.py test tests/unit/test_training_ticket_kind.py tests/unit/test_main_training_group.py tests/unit/test_training_export.py tests/unit/test_training_export_kinds.py
```

## Definition of rejected
The branch exports `ticket` by default, writes a record for an unlinked, unreadable, `seed`, or held-out stem, invents an `authored_by` value outside `human` and `author`, reads the reply from the closing `result` event instead of the assistant `message` events, changes how Author keys its calls, adds a `./dev.py` wrapper, uses a `counts.get` fallback in `report`, or edits a file outside the fence.

## Time budget
- expected: 15m
- stuck: 30m
