---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
none

## Context
- clutch/git.py::Git

## Goal / Why
Since about merge 675 the most frequent cause of failed Implement attempts is a fence miss: a ticket changes the `clutch.git.Git` seam and tests that stand in for it with hand-built objects break outside the fence, because each stand-in implements only the few methods its author needed ("fakes only Git.commit", "Git stand-ins lacking main_write"). Today 73 files under `tests/unit` and `tests/integration` hold 97 such stand-ins (`SimpleNamespace`/`NS`/`Mock` bound to a `git` name, local `Git`/`FakeGit` classes). Owner decision 2026-11-21: one shared fake.

After this ticket `tests/git_fake.py` defines `GitFake`, which has every public member of `Git` with the same signature, so a Git seam change edits one fake. A unit test fails when `Git` gains, loses or re-signs a public member without the fake following. This ticket migrates the first 9 stand-in files and adds an adoption test that scans every file under `tests/unit` and `tests/integration` for the stand-in patterns below, with a `PENDING` list of the files that sibling tickets migrate next. The chain `shared-git-fake-unit-2` .. `shared-git-fake-unit-6`, then `shared-git-fake-integration`, empties `PENDING`.

Design of `GitFake` (the minimum that lets the 97 stand-ins move over):
- `GitFake(**overrides)`: each keyword names a `Git` member or `_run`. A non-callable value is returned by that method. A `BaseException` instance is raised. A callable is called with the method's arguments (including `dir`) and its result is awaited when awaitable. Unknown keyword names raise `TypeError`.
- A method with no override returns a default chosen from the real signature's return annotation: `str` gives `""`, `list[...]` gives `[]`, `None` gives `None`, `str | None` gives `None`, `Path` gives `dir / ".git"`.
- Every call is appended to `fake.calls` as `(name, args, kwargs)`, so tests assert call order and arguments from one list in place of `assert_awaited_with`.
- `main_write()` returns one `asyncio.Lock` per fake (as `Git` does). `_commit_lock` is an `asyncio.Lock`. `_run` is an override-only async method (default `""`) because 52 production call sites reach `git._run`; this ticket does not change that.

`tests/fakes.py::FakeGit` stays as it is (Scope out).

## Boundary contract
### Shared Git test fake
- disposition: create
- owner: tests/git_fake.py
- consumers: the unit tests that currently build a `Git` stand-in by hand (9 migrated here, 64 by the chained tickets)
- observable change: tests gain `GitFake`; no production behavior, CLI, journal or document changes
- compatibility: production code and `clutch.git.Git` are unchanged; `tests/fakes.py::FakeGit` and its `fake_git` fixture are unchanged
- acceptance: `GitFake` mirrors the public members and signatures of `Git`, and the adoption test fails on any unlisted hand-built stand-in
- tests: `tests/unit/test_git_fake.py` and `tests/integration/test_git_fake_adoption.py`
- post-merge source of truth: tests/git_fake.py
- closest existing: `tests/fakes.py::FakeGit` answers any attribute from a preset dict and raises `KeyError` for a method without a preset, with no signature, no defaults and no lock, so it cannot meet the parity or default requirements; the 97 hand-built stand-ins each cover a few methods
- earning reason: consolidation of evidenced duplicates (97 stand-ins in 73 files, counted by the patterns in the Acceptance criteria) behind the `Git` external-effect seam, so one edit follows a Git seam change

## Scope in / Scope out
In: create `tests/git_fake.py` with `GitFake` as designed in Goal; create `tests/unit/test_git_fake.py`; create `tests/integration/test_git_fake_adoption.py`; migrate each stand-in in the 9 files below onto `GitFake`, keeping every existing assertion and test name (an `assert_awaited_with` on a stand-in becomes an assertion on `fake.calls`). Migrate a file only through its stand-ins: add the import of `GitFake` it needs and nothing else changes. A test that uses a real `Git` on a fake process executor is not a stand-in and stays as is.

Patterns the adoption test scans for (each line of each `*.py` under `tests/unit` and `tests/integration`, except `tests/integration/test_git_fake_adoption.py` and `tests/unit/test_git_fake.py`):
- `\bgit\s*=\s*(SimpleNamespace|NS|Mock|MagicMock|AsyncMock)\(` (a `git` name or keyword bound to a hand-built object, which also matches `git=` inside a `SimpleNamespace(...)` and `.git = NS(`);
- `^\s*class\s+(Fake|Empty|Diff)?Git\b` (a local class defining a Git stand-in);
- `spec=Git\b|create_autospec\(Git` (a mock specced on the real class).

The adoption test has two checks. (1) A file not in `PENDING` has zero matches. (2) Each `PENDING` entry exists and still has at least one match, so a migrated file left in the list fails. `PENDING` is a tuple of repo-relative paths initially holding the 64 files that the sibling tickets `shared-git-fake-unit-2` through `shared-git-fake-unit-6` and `shared-git-fake-integration` migrate (each lists its files in its Scope fence).

Files migrated here (stand-ins counted):
tests/unit/test_admission_facts.py (1)
tests/unit/test_artifacts_harvest_cost_source.py (1)
tests/unit/test_author.py (5)
tests/unit/test_author_calibration.py (1)
tests/unit/test_author_context_block.py (1)
tests/unit/test_author_decline_findings.py (1)
tests/unit/test_author_neighbors_block.py (1)
tests/unit/test_author_roadmap_row.py (2)
tests/unit/test_author_stem_claimed.py (1)

Out: production code under `clutch/`; `tests/fakes.py` and its `fake_git` fixture (its 10-odd users are not migrated); the five `tests/regress_*.py` files with a stand-in (frozen regression reproducers run against the merge base); `tests/unit/test_git_*.py` real-`Git` tests; any other test file. Files for later tickets are `shared-git-fake-unit-2` through `shared-git-fake-unit-6` and `shared-git-fake-integration`.

## Scope fence
- tests/git_fake.py
- tests/unit/test_git_fake.py
- tests/integration/test_git_fake_adoption.py
- tests/unit/test_admission_facts.py
- tests/unit/test_artifacts_harvest_cost_source.py
- tests/unit/test_author.py
- tests/unit/test_author_calibration.py
- tests/unit/test_author_context_block.py
- tests/unit/test_author_decline_findings.py
- tests/unit/test_author_neighbors_block.py
- tests/unit/test_author_roadmap_row.py
- tests/unit/test_author_stem_claimed.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_git_fake.py` passes a parity test: the set of public async-method names plus `main_write` on `GitFake` equals that on `clutch.git.Git`, and for each name `inspect.signature` parameters (names, kinds, defaults) are equal. The test fails (checked by monkeypatching a new `async def` onto a copy of `Git`) when `Git` gains a method the fake lacks, not only when the sets are equal.
2. `./dev.py test tests/unit/test_git_fake.py` passes override tests: `GitFake(rev_parse="sha")` returns `"sha"` from `await fake.rev_parse(Path("/r"), "HEAD")`; a `ValueError` instance override raises it; a callable override receives `(dir, *args)` and is awaited when it returns an awaitable; `GitFake(nope=1)` raises `TypeError`, not silently accepts.
3. `./dev.py test tests/unit/test_git_fake.py` passes default tests: an unconfigured `status_porcelain` returns `""` and `ls_files` returns `[]`, not `None`; `previous_release_tag` returns `None`; `git_common_dir(Path("/r"))` returns `Path("/r/.git")`; `main_write()` returns the same `asyncio.Lock` object on two calls; `fake.calls` equals `[("rev_parse", (Path("/r"), "HEAD"), {})]` after one such call.
4. `./dev.py test tests/integration/test_git_fake_adoption.py` passes: the 9 files named in Scope in have zero matches for the three patterns and are absent from `PENDING`, and the test fails (not passes) when a `PENDING` entry has no remaining match or an unlisted file contains `git = SimpleNamespace(`.
5. `./dev.py test tests/unit/test_admission_facts.py tests/unit/test_artifacts_harvest_cost_source.py tests/unit/test_author.py tests/unit/test_author_calibration.py tests/unit/test_author_context_block.py tests/unit/test_author_decline_findings.py tests/unit/test_author_neighbors_block.py tests/unit/test_author_roadmap_row.py tests/unit/test_author_stem_claimed.py` passes with the migrated tests keeping their names and assertions, so a test that asserted a Git call still asserts the same call (now via `fake.calls`), not a weaker one.

## Verification
```
./dev.py test tests/unit/test_git_fake.py
./dev.py test tests/integration/test_git_fake_adoption.py
./dev.py test tests/unit/test_admission_facts.py tests/unit/test_artifacts_harvest_cost_source.py tests/unit/test_author.py tests/unit/test_author_calibration.py tests/unit/test_author_context_block.py tests/unit/test_author_decline_findings.py tests/unit/test_author_neighbors_block.py tests/unit/test_author_roadmap_row.py tests/unit/test_author_stem_claimed.py
```

## Definition of rejected
A change under `clutch/`; a migrated test whose assertion is dropped, weakened or turned into one that also passes when the call never happens; a stand-in left in a migrated file; a file outside the Scope fence edited; `GitFake` members that differ from `Git` in name or signature. A `PENDING` entry that is not a real file with a match.

## Time budget
- expected: 30m
- stuck: 60m
