---
state: draft
source: human
priority: P1
kind: chore
---

## Depends on
- snapshot-duckdb-under-one-second

## Context
- docs/journal-sql-refactor-plan.md#Problem
- docs/journal-sql-refactor-plan.md#Release protocol
- docs/roadmap.md#7. Plan document shape
- clutch/roadmap.py::gates
- tests/integration/test_roadmap_gate.py
- tickets/journal-query-layer/evidence/re-measure.md

## Goal / Why
A release checkpoint must measure the command users wait on. The November 16 journal re-measurement timed drain startup and status; decision 21 used them to defer the journal window. Neither measured the extension's view snapshot. Its later profile shows 31.49 s, including only 0.182 s reading the journal. Make end-to-end snapshot latency part of the documented checkpoint and an executable release check, so a fast reader cannot mask slow processing after the read.

## Boundary contract
### Journal performance checkpoint
- disposition: extend
- owner: docs/journal-sql-refactor-plan.md and the release gate blocks in docs/roadmap.md
- consumers: roadmap driver, release acceptance and operator taking the measurement
- observable change: record status, drain startup and full snapshot as separate measurements. An incident-scale snapshot at or above one second fails the ship check even with passing status and drain measurements. A missing or invalid measurement cannot certify the checkpoint.
- compatibility: retain existing evidence, current status and drain thresholds, release identity, gate order and acceptance last. Keep the broad SQL migration's conditional schedule.
- acceptance: a dedicated release check runs the actual end-to-end benchmark delivered by the dependency and propagates nonzero results
- tests: run that benchmark and review parsed release blocks
- post-merge source of truth: docs/journal-sql-refactor-plan.md for measurement procedure and docs/roadmap.md for executable gates

## Scope in / Scope out
Update the journal plan's status, checkpoint, problem and ticket-breakdown measurement instructions to distinguish the old evidence from the three required readings. Specify host, source revision, cardinalities, command, raw samples, median, and separate journal-load versus end-to-end time. In docs/roadmap.md update the current release criteria, re-measure row, agent task and decision cross-references consistently. Preserve dated decisions as history with a superseding note. Credit the P0 snapshot port in rows 36 and 40 so a later release reuses its owner and ports the remaining consumers. Keep unrelated rows and the historic capture intact.

Use the carried tests/regress_snapshot_latency.py and its fixture from the dependency as the executable acceptance check on the current open release and subsequent already-planned releases, before roadmap accept. Use a checkout-root argv invoking the project Python environment, with the same exit semantics as the regression protocol. Reuse the existing gate reader and runner. A checkpoint failure identifies the snapshot command, scale and timing, and calls for profiling that path before recording the disposition. Scope excludes implementing a second benchmark, changing the roadmap parser or setting host-wide performance policy.

## Scope fence
- docs/journal-sql-refactor-plan.md
- docs/roadmap.md

## Acceptance criteria
1. One-time review of `docs/journal-sql-refactor-plan.md` finds status, drain startup and the fresh-process snapshot listed independently, the one-second snapshot threshold, representative-scale requirement, sample/report fields, and how to handle invalid or slow results even when the other two measurements pass.
2. One-time review of `docs/roadmap.md` using the existing gate parser finds the benchmark argv in each current/future planned release's ship block ahead of the final acceptance command. The existing merged checks, suite commands, and completed release blocks are preserved. Measurement and ownership prose describes the remaining journal work without commissioning a second snapshot reader. No standing test pins the live roadmap text.
3. `python tests/regress_snapshot_latency.py` runs the dependency's actual CLI benchmark on its prepared representative checkout and exits 0 for pass. In one-time review, verify the gate runner propagates a nonzero benchmark exit as failure; a missing fixture or malformed snapshot cannot count as passing evidence.

## Verification
```
python tests/regress_snapshot_latency.py
./dev.py test tests/integration/test_roadmap_gate.py tests/integration/test_roadmap_table.py
```

## Definition of rejected
Reject a documentation-only promise without an executable ship check, a benchmark of status or SQL alone, a repeated benchmark implementation, or a retroactive rewrite of the November capture.

## Time budget
- expected: 12m
- stuck: 24m
