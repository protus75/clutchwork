---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- shared-git-fake-unit-6

## Context
- clutch/git.py::Git

## Goal / Why
`shared-git-fake` created `tests/git_fake.py::GitFake` and `tests/integration/test_git_fake_adoption.py`, whose `PENDING` list names the files still holding a hand-built `Git` stand-in. This ticket migrates 2 of them (2 stand-ins) onto `GitFake` and removes them from `PENDING`, so those tests no longer break when `Git` gains a method. Read `tests/git_fake.py` in the worktree for the override and `calls` contract before editing; it is a merged dependency.

This is the last ticket of the chain. It also deletes `PENDING` and its two checks from the adoption test, leaving the pattern scan over every file under `tests/unit` and `tests/integration` with only the exemptions named in Scope in.

## Boundary contract
none
- reason: tests encoding an existing contract; the stand-ins move to the existing `tests/git_fake.py::GitFake` with the same assertions and no production, document or behavior change

## Scope in / Scope out
In: migrate each stand-in in the files below onto `GitFake` from `tests/git_fake.py`, keeping every existing assertion and test name (an `assert_awaited_with` on a stand-in becomes an assertion on `fake.calls`). Add only the import `GitFake` needs and nothing else changes in a file. Remove each migrated file from `PENDING` in `tests/integration/test_git_fake_adoption.py`; that is the only edit allowed there. A test using a real `Git` on a fake process executor is not a stand-in and stays as is.

Files migrated here (stand-ins counted):
tests/integration/test_covmap.py (1)
tests/integration/test_harvest_cost_source.py (1)

Out: production code under `clutch/`; `tests/git_fake.py` (when a stand-in needs a capability `GitFake` lacks, give the fake the capability through an override callable in the test, and name the gap in the run record); `tests/fakes.py`; the five `tests/regress_*.py` files; every file not listed above.

Also in: delete `PENDING` and both of its checks from `tests/integration/test_git_fake_adoption.py`, so the scan covers every file with the two exempt files named in the test's own header.

## Scope fence
- tests/integration/test_git_fake_adoption.py
- tests/integration/test_covmap.py
- tests/integration/test_harvest_cost_source.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_git_fake_adoption.py` passes with `PENDING` gone: every file under `tests/unit` and `tests/integration` other than the two exempt files has zero matches for the three patterns, and the scan fails (not passes) when a temporary file under a `tmp_path` copy of the scan root contains `git = SimpleNamespace(`.
2. `./dev.py test tests/integration/test_covmap.py tests/integration/test_harvest_cost_source.py` passes with the migrated tests keeping their names and assertions, so a test that asserted a Git call still asserts the same call (now via `fake.calls`), not a weaker one.

## Verification
```
./dev.py test tests/integration/test_git_fake_adoption.py
./dev.py test tests/integration/test_covmap.py tests/integration/test_harvest_cost_source.py
```

## Definition of rejected
A change under `clutch/`; a migrated test whose assertion is dropped, weakened or turned into one that also passes when the call never happens; a stand-in left in a migrated file; a file outside the Scope fence edited; `GitFake` members that differ from `Git` in name or signature.

## Time budget
- expected: 12m
- stuck: 24m
