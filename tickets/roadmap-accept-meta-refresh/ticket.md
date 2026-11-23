---
state: confirmed
source: box:suggestion
priority: P0
kind: feature
---

## Depends on
none

## Context
- clutch/acceptance.py::accept
- clutch/meta.py::refresh
- clutch/meta.py::check
- tests/unit/test_roadmap_accept.py::checkout

## Goal / Why
`clutch roadmap accept` appends gap rows to `docs/roadmap.md` and commits with `only=[roadmap.ROADMAP]` without refreshing the file's meta header. The header hash then no longer matches the body, so the next release gate's `clutch meta check docs ...` reports `docs/roadmap.md drifted` (0.5.0 gate, 2026-11-22) and costs a gate cycle plus a manual fix. Merged `roadmap-meta-resync` fixed one instance by hand and did not change the accept path. After this ticket, the commit accept makes after adding rows contains a roadmap whose meta header is current, so `meta.check` reports no `drifted` finding for it. Neighbours `meta-fill-drifted-no-model`, `meta-path-selects-nothing` and `implement-spec-meta-untouched-not-reported` cover other meta gaps and are not re-solved. The mechanical `meta.refresh` is used, with no model call.

## Boundary contract
### Roadmap accept commit
- disposition: extend
- owner: clutch/acceptance.py
- consumers: `clutch roadmap accept`, release gates running `clutch meta check`
- observable change: when accept adds rows, it computes the refreshed header with the functions used by `meta.refresh` before writing `docs/roadmap.md` inside the exact-path commit callback, so the one commit holds rows and a current header; with no added rows nothing is written or committed, as before
- compatibility: the commit message, the `only=[roadmap.ROADMAP]` pathspec, refusals and the printed summary stay unchanged; the existing metadata functions are reused with no new meta API
- acceptance: a unit test reads the committed roadmap text and runs `meta.check` on it; the result has no finding for `docs/roadmap.md`
- tests: tests/unit/test_roadmap_accept.py
- post-merge source of truth: clutch/acceptance.py

## Scope in / Scope out
Scope in: In `clutch/acceptance.py`, use `checkout.git.commit_edit` for the exact roadmap path, with the second clean check, the pre-write header check and the write in its callback. Compute the refreshed text in memory with the same `meta.parse`, `meta.generated` and `meta.compose` functions that `meta.refresh` uses. Read the tracked paths and HEAD before writing inside the callback. A malformed configured header raises `Refusal` with the existing roadmap path and the road `fix the meta block, then run clutch roadmap accept <release> again` before any write. Preserve the metadata path selection used by `meta.refresh` and write the finished text once. In `tests/unit/test_roadmap_accept.py`, extend the `checkout` fixture so its config carries `meta.paths` covering `docs` and its git fake answers `ls_files`, `rev_parse` and `commit_edit`; this is the only fixture edit, and the new tests go in that file because it covers the edited unit. Scope out: `clutch/roadmap.py`, the roadmap author commit, `clutch/meta.py`, and every document, since no documented behavior changes.

## Scope fence
- clutch/acceptance.py
- tests/unit/test_roadmap_accept.py

## Acceptance criteria
1. After accept adds a gap row, the roadmap text of the recorded commit is meta-clean: `./dev.py test tests/unit/test_roadmap_accept.py -k meta_header` shows `meta.check` returning `[]`, not a `(docs/roadmap.md, "drifted")` finding, with a roadmap that starts with a stale meta header.
2. The refresh runs before the commit and the commit still uses `only=[roadmap.ROADMAP]`: the same test asserts the recorded `only` equals `[roadmap.ROADMAP]` and the recorded text already holds the refreshed hash, not the stale one.
3. When no promise has a `new_row`, accept makes no commit and does not enter the commit edit: `./dev.py test tests/unit/test_roadmap_accept.py -k passes` asserts `git.commits == []`, not one commit.
4. A malformed meta block makes accept raise `Refusal` before changing any roadmap bytes: `./dev.py test tests/unit/test_roadmap_accept.py -k meta_malformed` asserts the original bytes remain and `git.commits == []`.
5. The existing accept tests still pass: `./dev.py test tests/unit/test_roadmap_accept.py`.

## Verification
```
./dev.py test tests/unit/test_roadmap_accept.py tests/unit/test_meta_refresh.py
```

## Definition of rejected
The branch calls a model for the refresh, adds a new meta API or flag, edits `clutch/meta.py`, or leaves the committed roadmap with a `drifted` finding.

## Time budget
- expected: 15m
- stuck: 30m
