---
priority: P0
kind: feature
agent_tier: medium
agent_effort: medium
source: box:suggestion
state: draft
---

## Depends on
none

## Runs before
- roadmap-named-stem-refile

## Context
- clutch/roadmap.py::author_ahead
- clutch/roadmap.py::refile_row
- clutch/roadmap.py::link
- clutch/roadmap.py::strike
- tests/unit/test_roadmap_author.py

## Goal / Why
`author_ahead` reads `docs/roadmap.md` once, then writes that in-memory text back for every strike, link and refile. The post-authoring link step runs after `author_messages`, which can take minutes. Any commit that touches `docs/roadmap.md` in that window is silently reverted. On 2026-11-17 commit 3d7f806e restored row 114's old stem and undid the hand fix b773e418. The row then stayed 're-files spent', which blocks the driver and the release gate. After this ticket, each roadmap write re-reads the file from disk immediately before editing and applies only its row-level change to that fresh text. If the row it edits has changed since it was parsed, the write is skipped and reported, and nothing is overwritten.

## Scope in / Scope out
In `clutch/roadmap.py`, add one private async helper used by all four write sites in `author_ahead`: the strike, the link, the refile, and the post-authoring link. The helper does these things:
- It re-reads the roadmap file from disk and parses it.
- It finds the row with the same number as the row it was given.
- It skips the write if that row's `stem` or `content` differs from the row it was given.
- Otherwise it applies the edit function (`strike`, `link` or `refile_row`) to the fresh row and fresh text, writes the result, and commits only the roadmap file.
- It returns the new text, or `None` when it skipped.

A skip appends a line to the returned report lines, in the form `roadmap: row N STEM changed on disk; skipped <action>`, where STEM is the stem the row had when it was parsed. The local `text` variable in `author_ahead` is replaced by the helper's returned text after each write, so later parses see the current file.

Out of scope: the decline logic (`roadmap-named-stem-refile`), the `Refusal` for an uncommitted roadmap at the start of the pass, and any other module. The first-read uncommitted check stays as is. No document changes: the roadmap file is read and written at runtime only, and no document describes the stale write.

New tests go in a new file. Do not add tests to existing files.

## Scope fence
- clutch/roadmap.py
- tests/unit/test_roadmap_fresh_write.py

## Acceptance criteria
1. When the row's stem changed on disk between parse and write, the write is skipped. A test changes row 114's stem on disk inside the fake `author_messages`, then runs `author_ahead`. Afterward the roadmap file holds the new stem and does not hold the stale one, no commit named `clutch(roadmap): author <old stem>` exists, and the report contains `roadmap: row 114 <old stem> changed on disk; skipped link`. The test rules out the stale text being written back. Checked by `./dev.py test tests/unit/test_roadmap_fresh_write.py`.
2. When the row's `content` changed on disk between parse and write, no write or commit happens for that row, and the report contains `changed on disk; skipped`. The test asserts the file bytes are unchanged from the on-disk edit and no commit was made, not that the stale text was written. Checked by `./dev.py test tests/unit/test_roadmap_fresh_write.py`.
3. When a different row's cell changed on disk and the edited row is unchanged, the link is applied and the other row's change is kept. Checked by `./dev.py test tests/unit/test_roadmap_fresh_write.py`.
4. The existing roadmap author tests still pass. Checked by `./dev.py test tests/unit/test_roadmap_author.py tests/integration/test_roadmap_author.py tests/unit/test_roadmap_refile.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_fresh_write.py tests/unit/test_roadmap_author.py tests/integration/test_roadmap_author.py tests/unit/test_roadmap_refile.py
```

## Definition of rejected
Any write path in `author_ahead` that still writes text parsed before an `await`. A lock or retry loop that does not re-read before editing. A change that makes a stale-row write succeed. Edits outside the fence.

## Time budget
- expected: 30m
- stuck: 60m
