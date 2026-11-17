---
state: confirmed
source: box:roadmap_row
priority: P1
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/release.py
- clutch/git.py::Git.first_parent_squashes
- clutch/git.py::Git.tag
- clutch/merge.py::squash_message
- clutch/roadmap.py::ship
- clutch/seams.py::FileSystem
- tests/unit/test_release.py
- pyproject.toml

## Goal / Why
When `clutch release` runs, and so when the driver's `ship` runs, a `CHANGELOG.md` at the checkout root gets a new top section for the released version, and the `release: <version>` commit carries that file, so the `v<version>` tag contains it. The section heading names the version and the release date. Under it is one line per ticket merged since the previous `v*` tag, each with its stem and a one-sentence summary. Sections for earlier versions stay byte-identical. This repo's `pyproject.toml` `[project.urls]` gains a `Changelog` entry that points at the file. PyPI renders only the README, so the changelog is linked and not shown (roadmap decision 20 keeps publishing manual). Today a release carries no record of what changed, and the owner wants one without hand-writing it.

## Scope in / Scope out
In:
- New `clutch/changelog.py`, pure with no I/O. It parses a squash commit subject `clutch(<stem>): <goal line>` into `(stem, first sentence of the goal line)`, renders a section `## <version> - <YYYY-MM-DD>` followed by one `- <stem>: <sentence>` line per ticket, and inserts that section into existing text directly under the `# Changelog` title. When the text is empty or missing it creates the title first. Text below the insertion point is left untouched.
- `clutch/git.py`: two new `Git` methods. `previous_release_tag(dir)` returns the nearest `v*` tag reachable from HEAD, or `None` when there is none. `merged_subjects(dir, since)` returns subjects of first-parent commits whose message has a `clutch-ticket:` trailer, in the range `since..HEAD`, or all of HEAD when `since` is `None`. Review and run-record commits (`clutch(<stem>): review`, `checks`, and so on) carry no trailer and are never listed.
- `clutch/release.py::release` gains `fs` and `today` parameters and the new signature is `release(repo, git, exec_, fs, env, part, today)`. `today` is an ISO date string. The function reads the previous tag and the subjects before the version bump commit, writes `CHANGELOG.md` through `fs`, and commits `pyproject.toml`, `uv.lock` and `CHANGELOG.md` together as `release: <version>`. The dirty-file refusal also covers `CHANGELOG.md`, so a hand-edited changelog is never swept into the release commit. The version is still computed first, and the existing-tag refusal still happens before any write.
- Update both call sites, `clutch/__main__.py::handle_release` and `clutch/roadmap.py::ship`, to pass `checkout.fs` and `checkout.clock().date().isoformat()`.
- `pyproject.toml`: add `Changelog = "https://github.com/protus75/clutchwork/blob/main/CHANGELOG.md"` under `[project.urls]`.
- `docs/how-clutch-works.md`: update only the `release --minor|--patch` row of the verb table, so it says the three files are committed and that `CHANGELOG.md` gets a new section.
- `clutch/docs/host-running.md`: update only the `release` verb row, which says release commits `pyproject.toml` and `uv.lock`, so it says release also writes a new `CHANGELOG.md` section and commits the three files.
- Update the existing tests the signature and trace change force: the exact call trace and the `release.release` call in `tests/unit/test_release.py`, the `release` call args pinned in `tests/unit/test_roadmap_ship.py`, and any assertion in `tests/integration/test_release.py` or `tests/integration/test_roadmap_ship.py` that lists the files in the release commit.

Out: no `CHANGELOG.md` is written into the repo by this ticket, since the first real release creates it. No backfill of past versions. No publish change. No `--major`. No change to the journal `release` signal. No tag message change.

## Scope fence
- clutch/changelog.py
- clutch/release.py
- clutch/git.py
- clutch/__main__.py
- clutch/roadmap.py
- pyproject.toml
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- tests/unit/test_changelog.py
- tests/unit/test_release_changelog.py
- tests/integration/test_changelog_url.py
- tests/unit/test_release.py
- tests/unit/test_roadmap_ship.py
- tests/integration/test_release.py
- tests/integration/test_roadmap_ship.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_changelog.py` passes. It asserts that inserting a section for `0.4.0` into text that already holds a `## 0.3.0` section returns text whose part from `## 0.3.0` onward equals the old text from that point byte for byte, and not a rewritten or reordered one.
2. `./dev.py test tests/unit/test_changelog.py` passes. It asserts that the subject `clutch(a-b): Does X. Also Y.` yields `("a-b", "Does X.")`, not the full line, and that a subject that does not match `clutch(<stem>): <text>` is skipped, not raised.
3. `./dev.py test tests/unit/test_changelog.py` passes. It asserts that missing or empty existing text yields `# Changelog` followed by the new section, and that a release with no merged tickets yields a heading with no bullet lines and no error.
4. `./dev.py test tests/unit/test_release_changelog.py` passes. With a fake exec and fake fs, `release()` writes `CHANGELOG.md` before the commit and the commit argv names `pyproject.toml`, `uv.lock` and `CHANGELOG.md`, not only the first two. The `since` range comes from the previous `v*` tag and is `None` when there is no tag.
5. `./dev.py test tests/unit/test_release_changelog.py` passes. A dirty `CHANGELOG.md` in the status output raises `Refusal` and no write and no `uv version --bump` call happens. An existing `v<version>` tag still refuses before `CHANGELOG.md` is written.
6. `./dev.py test tests/integration/test_changelog_url.py` passes. It parses `pyproject.toml` with `tomllib` and asserts `project.urls.Changelog` ends with `/CHANGELOG.md` and `Repository` is unchanged.
7. `./dev.py test tests/unit/test_release.py tests/unit/test_roadmap_ship.py tests/integration/test_release.py tests/integration/test_roadmap_ship.py` passes with the updated expectations.
8. `./dev.py test` exits 0 for the whole suite.
9. `./dev.py test tests/unit/test_release_changelog.py` passes. It drives the real `Git.merged_subjects` with a fake exec whose log output holds two commits: one `clutch(a-b): Does X.` commit with a `clutch-ticket: a-b` trailer and one `clutch(a-b): review` commit with no trailer. It asserts that only `clutch(a-b): Does X.` is returned, not both, and that the argv uses the `since..HEAD` form when `since` is a tag and the whole-HEAD form when `since` is `None`.

## Verification
```
./dev.py test tests/unit/test_changelog.py tests/unit/test_release_changelog.py tests/unit/test_release.py tests/unit/test_roadmap_ship.py tests/integration/test_changelog_url.py tests/integration/test_release.py tests/integration/test_roadmap_ship.py
```

## Definition of rejected
The branch writes `CHANGELOG.md` outside `release()` or after the release commit, so the tag lacks it. Or it rewrites or reorders earlier sections. Or it lists non-squash commits (review, checks, run-record) as merged tickets. Or it calls `datetime` or opens a file directly instead of using the clock and `fs` seams. Or it publishes or pushes anything.

## Time budget
- expected: 40m
- stuck: 80m
- reason: one cohesive release path (pure renderer, two git reads, one writer); splitting would leave a signature change without its callers.
