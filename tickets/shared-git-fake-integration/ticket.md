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
`shared-git-fake` created `tests/git_fake.py::GitFake` and `tests/integration/test_git_fake_adoption.py`, whose `PENDING` list names the files still holding a hand-built `Git` stand-in. This ticket migrates the last 7 of them (8 stand-ins) onto `GitFake` and removes them from `PENDING`, so those tests no longer break when `Git` gains a method. Read `tests/git_fake.py` in the worktree for the override and `calls` contract before editing; it is a merged dependency.

It also retires the older shared fake `tests/fakes.py::FakeGit` and its `fake_git` fixture in `tests/conftest.py`: `FakeGit` answers any attribute, so it never catches a call to a method `Git` lacks, and keeping it beside `GitFake` leaves two Git fakes with different behavior. Its 9 users move to `GitFake`.

This is the last ticket of the chain. It also deletes `PENDING` and its two checks from the adoption test, leaving the pattern scan over every file under `tests/unit` and `tests/integration` with only the exemptions named in Scope in.

## Boundary contract
none
- reason: tests encoding an existing contract; the stand-ins move to the existing `tests/git_fake.py::GitFake` with the same assertions and no production, document or behavior change

## Scope in / Scope out
In: migrate each stand-in in the files below onto `GitFake` from `tests/git_fake.py`, keeping every existing assertion and test name (an `assert_awaited_with` on a stand-in becomes an assertion on `fake.calls`). Add only the import `GitFake` needs and nothing else changes in a file. Remove each migrated file from `PENDING` in `tests/integration/test_git_fake_adoption.py`. The adoption test changes only as this Scope in states: these removals, deleting `PENDING` and its two checks, and adding the fourth pattern below. A test using a real `Git` on a fake process executor is not a stand-in and stays as is.

Files migrated here (stand-ins counted):
tests/integration/test_covmap.py (1)
tests/integration/test_harvest_cost_source.py (1)
tests/integration/test_retry_keeps_branch.py (1)
tests/integration/test_serve_verdict_orphan_sweep.py (1)
tests/unit/test_check_meta_fill.py (2)
tests/unit/test_runner_verdict_reread.py (1)
tests/unit/test_serve_verdict_owned.py (1)

Also in: retire `FakeGit`. Migrate every use of `FakeGit` or the `fake_git` fixture in these files onto `GitFake`, keeping test names and assertions (a `FakeGit.calls` or `results` assertion becomes the equivalent `GitFake` override or `calls` assertion):
tests/unit/test_git_commit.py
tests/unit/test_hostfiles.py
tests/unit/test_intake_plan.py
tests/unit/test_release_changelog.py
tests/unit/test_requisition_prior_review.py
tests/unit/test_roadmap_accept.py
tests/unit/test_roadmap_author.py
tests/unit/test_roadmap_merged.py
tests/unit/test_roadmap_merged_parallel.py
Then delete `class FakeGit` from tests/fakes.py, the `fake_git` fixture from tests/conftest.py, and in tests/unit/test_shared_fakes.py drop `fake_git`/`FakeGit` from `test_fixtures` (its parameter and loop entry) and delete the test that exercises `FakeGit` directly; nothing else changes there. Add a fourth pattern to the adoption scan: any `FakeGit` or `fake_git` reference outside tests/git_fake.py fails.

Out: production code under `clutch/`; `tests/git_fake.py` (when a stand-in needs a capability `GitFake` lacks, give the fake the capability through an override callable in the test, and name the gap in the run record); the rest of `tests/fakes.py`; the five `tests/regress_*.py` files; every file not listed above.

Also in: delete `PENDING` and both of its checks from `tests/integration/test_git_fake_adoption.py`, so the scan covers every file with the two exempt files named in the test's own header.

## Scope fence
- tests/integration/test_git_fake_adoption.py
- tests/integration/test_covmap.py
- tests/integration/test_harvest_cost_source.py
- tests/integration/test_retry_keeps_branch.py
- tests/integration/test_serve_verdict_orphan_sweep.py
- tests/unit/test_check_meta_fill.py
- tests/unit/test_runner_verdict_reread.py
- tests/unit/test_serve_verdict_owned.py
- tests/fakes.py
- tests/conftest.py
- tests/unit/test_shared_fakes.py
- tests/unit/test_git_commit.py
- tests/unit/test_hostfiles.py
- tests/unit/test_intake_plan.py
- tests/unit/test_release_changelog.py
- tests/unit/test_requisition_prior_review.py
- tests/unit/test_roadmap_accept.py
- tests/unit/test_roadmap_author.py
- tests/unit/test_roadmap_merged.py
- tests/unit/test_roadmap_merged_parallel.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_git_fake_adoption.py` passes with `PENDING` gone: every file under `tests/unit` and `tests/integration` other than the two exempt files has zero matches for the four patterns (the three existing ones plus the `FakeGit`/`fake_git` pattern this ticket adds), and the scan fails (not passes) when a temporary file under a `tmp_path` copy of the scan root contains `git = SimpleNamespace(`.
2. `./dev.py test tests/integration/test_covmap.py tests/integration/test_harvest_cost_source.py` passes with the migrated tests keeping their names and assertions, so a test that asserted a Git call still asserts the same call (now via `fake.calls`), not a weaker one.
3. `./dev.py test tests/integration/test_git_fake_adoption.py` proves no file under `tests/unit` or `tests/integration` other than tests/git_fake.py references `FakeGit` or `fake_git` (tests/fakes.py and tests/conftest.py lose theirs through the deletions in Scope in), and the scan fails on a `tmp_path` copy holding `from tests.fakes import FakeGit`.
4. `./dev.py test tests/unit/test_git_commit.py tests/unit/test_hostfiles.py tests/unit/test_intake_plan.py tests/unit/test_release_changelog.py tests/unit/test_requisition_prior_review.py tests/unit/test_roadmap_accept.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_merged_parallel.py tests/unit/test_shared_fakes.py` passes with every former `FakeGit` user on `GitFake` and test names unchanged.

## Verification
```
./dev.py test tests/integration/test_git_fake_adoption.py
./dev.py test tests/integration/test_covmap.py tests/integration/test_harvest_cost_source.py
./dev.py test tests/unit/test_git_commit.py tests/unit/test_hostfiles.py tests/unit/test_intake_plan.py tests/unit/test_release_changelog.py tests/unit/test_requisition_prior_review.py tests/unit/test_roadmap_accept.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_merged.py tests/unit/test_roadmap_merged_parallel.py tests/unit/test_shared_fakes.py
```

## Definition of rejected
A change under `clutch/`; a migrated test whose assertion is dropped, weakened or turned into one that also passes when the call never happens; a stand-in left in a migrated file; a file outside the Scope fence edited; `GitFake` members that differ from `Git` in name or signature.

## Time budget
- expected: 25m
- stuck: 50m
