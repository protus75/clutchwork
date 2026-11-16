---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- roadmap-author
- release-gates-as-commands
- release-publish

## Context
- docs/roadmap-driver-plan.md#6. The loop
- docs/roadmap.md#1. Release plan
- clutch/roadmap.py
- clutch/release.py
- tests/unit/test_roadmap_status.py::fixture
- tests/unit/test_roadmap_author.py::setup
- tests/unit/test_roadmap_gate.py::checkout
- tests/unit/test_release_publish.py::setup
- tests/integration/test_release.py::repository
- tests/integration/test_roadmap_status.py
- tests/integration/test_cli.py::CONFIG
- tests/integration/test_cli.py::ENV
- tests/unit/test_retro_recurrence.py::MemoryJournal
- docs/how-clutch-works.md#2.1 Verbs

## On-demand
- clutch/__main__.py

## Goal / Why
Roadmap row 93 (`driver-loop`, owning design `docs/roadmap-driver-plan.md` section 6, step 3) needs a release step: when the current release's ship gate passes, `release` runs, then `publish` only when `release.publish` is true, and the next release becomes current. This ticket builds that step as one function, `clutch/roadmap.py::ship`, and fixes the ordering defect that would stall the driver right after a release. `driver-loop` calls `ship` at serve's and drain's idle points; nothing calls it before then.

The stall. `clutch/roadmap.py::choose` returns ready rows only from the first master table that still has an open, ready, or waiting row. A release ships when its gate passes, and the 0.3.0 gate (`docs/roadmap.md` section 8) requires only its P0 and P1 rows merged. So P2 rows can be left unfinished when 0.3.0 ships: `gemini-provider` has no credential on this machine, and a row whose capture evidence is missing waits. While one of them is unfinished, `choose` holds every later table, and `roadmap author` never authors a 0.4.0 row again.

The design, chosen as the smallest that keeps the 0.4.0 journal window's feature freeze ("no feature ticket runs during the window", `docs/roadmap.md` section 1): the release boundary is the version. `clutch release --minor` names each release for the version it opens (tag `v0.3.0` opened 0.3.0), so the current release is the `pyproject.toml` version read as `<major>.<minor>.0`. `choose` orders tables in three groups:
1. the current release's tables;
2. tables of earlier, shipped releases, so their leftover rows come after the current release's rows;
3. later releases.

The first group with an unfinished row is the only one whose rows are ready, as today. Leftovers never hold the current release, so the stall is gone. They never run beside it, so the freeze holds. They run once the current release has no unfinished row, ahead of the release after it. With no version, or a version no heading names, every table counts as group 1, which is today's order. The alternative, moving leftover rows into the next release's table as `docs/roadmap.md` section 9 describes for shipped rows, puts 0.3.0's leftover features into the 0.4.0 window. It also needs a table-rewriting edit of `docs/roadmap.md`, a file that authoring agents edit by hand.

Release and publish run back to back on a clean tree. `clutch/release.py::publish` refuses when any tracked file is dirty or the token is unset, and it refuses once HEAD has moved past the tag. Its road then says to release again, which would skip the tagged version. So when `release.publish` is true, `ship` runs publish's own preconditions, extracted as `release.publishable`, before it tags anything. A dirty main checkout then delays the release to the next idle point instead of leaving a tagged version that is never uploaded. Release and publish then run with no commit between them, so the tag is on HEAD when publish checks it. With `release.publish` false (the default), `ship` tags and bumps locally and runs no build and no upload (owner decision 5 of 2026-11-16).

## Scope in / Scope out
Scope in:
- `clutch/roadmap.py`:
  - New `current_release(repo: Path) -> str | None`. It reads `repo / "pyproject.toml"` with `tomllib` and takes `[project].version`. When that version's first two dot-separated parts are decimal integers `M` and `N`, it returns `f"{M}.{N}.0"`. Otherwise it returns None: a missing file, invalid TOML, no `project.version`, or a version like `dev`.
  - `choose(rows, *, states, files, current=None)`. When `current` is not None and some row has `release_name(row.release) == current`, let `c` be the smallest `_table` of those rows. Each row has a rank:
    - `(0, row._table)` when `c` is None or the row's release is `current`;
    - `(1, row._table)` when `row._table < c`;
    - `(2, row._table)` otherwise.

    The rank replaces `row._table` in three places: the `unfinished` list, the filter that keeps only the first unfinished group's ready rows, and the ready sort key, which becomes `(rank, row.priority, row.line)`. Strikes, links, waits, and `open` are unchanged.
  - `author_ahead` and `status` pass `current=current_release(checkout.repo)` to `choose`. `merged` does not change.
  - New `async def ship(checkout) -> list[str]`:
    1. `current = current_release(checkout.repo)`. When it is None, return `[]` with no other call.
    2. `passed, lines = await run_gate(checkout, current)`. Its refusals (missing roadmap, no gate block for `current`) propagate. When `passed` is false, return `lines`.
    3. When `checkout.config.release.publish` is true, `await release.publishable(checkout.repo, checkout.git, checkout.env, checkout.config)`; its `Refusal` propagates before anything is tagged.
    4. `version, sha = await release.release(checkout.repo, checkout.git, checkout.exec_, child_env(checkout.env, checkout.config), "minor")`, then `release.journal_release(checkout.journal, version, sha)`, then append `release: tagged v<version> at <sha>`.
    5. When `checkout.config.release.publish` is true, `version, _, _ = await release.publish(checkout.repo, checkout.git, checkout.exec_, checkout.fs, checkout.env, checkout.config)`, then append `publish: uploaded <version> to PyPI`. Its `Refusal` propagates.
    6. Return the lines.
- `clutch/release.py`:
  - New `async def publishable(repo, git, env, config) -> None`. It holds publish's first two checks, moved unchanged and in the same order: the token check when `config.release.publish` is true, then `git.status_porcelain(repo, "--untracked-files=no")`. The refusal messages and roads stay the same. `publish` calls it first and keeps everything after those checks.
  - New `def journal_release(journal, version, sha) -> None`. It calls `journal.append(EventType.SIGNAL, {"signal": "release", "version": version, "tag": f"v{version}", "commit": sha})` with those two positional arguments and nothing else, exactly as `main` appends it today.
- `clutch/__main__.py` `main`: the `release` verb calls `release.journal_release(checkout.journal, version, sha)` instead of appending the signal itself. Nothing else in the file changes.
- `docs/how-clutch-works.md` section 2.1, the `roadmap author [--ahead N]` row only. "files ready rows in release order" becomes "files ready rows in release order: the current release (the `pyproject.toml` version as `<major>.<minor>.0`) first, then rows that earlier releases left unfinished, then later releases". Nothing else in the file changes.
- New tests in three new files: `tests/unit/test_roadmap_release_boundary.py`, `tests/unit/test_roadmap_ship.py`, and `tests/integration/test_roadmap_ship.py`. They may import `HEADER` and `row` from `tests/unit/test_roadmap_status.py`, `setup`, `put`, and `run` from `tests/unit/test_roadmap_author.py`, `checkout` and `RecordingExec` from `tests/unit/test_roadmap_gate.py`, `MemoryJournal` from `tests/unit/test_retro_recurrence.py`, and `CONFIG` and `ENV` from `tests/integration/test_cli.py`, all unchanged.

Scope out:
- Calling `ship` from serve or drain, the digest, and the `drain-loop` prompt: `driver-loop` (row 93) does those.
- Moving rows between tables, a "Shipped" section, or any edit of `docs/roadmap.md`, `docs/roadmap-driver-plan.md`, or other plans.
- Retrying a failed upload. A `publish` refusal after the tag leaves that version tagged and not uploaded. `ship` reports it by raising, and the next idle point gates the next release.
- `parse`, `gates`, `run_gate`, `merged`, `release.release`, and the rest of `release.publish`; any new verb, flag, config field, journal signal, or `clutch/help.py` entry.

## Scope fence
- clutch/roadmap.py
- clutch/release.py
- clutch/__main__.py
- docs/how-clutch-works.md
- tests/unit/test_roadmap_release_boundary.py
- tests/unit/test_roadmap_ship.py
- tests/integration/test_roadmap_ship.py

## Acceptance criteria
1. `tests/unit/test_roadmap_release_boundary.py::test_choose_orders_by_release` builds, with `HEADER` and `row` from `tests/unit/test_roadmap_status.py`:
   - `### 1.0.0` with row 1 `old-wait`, whose Content is `after its agent capture`, and row 2 `old-ready`;
   - `### 2.0.0` with row 3 `cur-ready` and row 4 `cur-open`, whose Content is `` `tickets/cur-open/` ``;
   - `### 3.0.0` with row 5 `new-ready` at P0.

   It calls `choose(rows, states=..., files=set(), current=...)` and asserts the ready stems:
   - states `{"cur-open": "running"}`: `current=None` gives `("old-ready",)`, and so does `current="9.9.9"`; `current="2.0.0"` gives `("cur-ready",)`;
   - states with `cur-open` and `cur-ready` both `merged`: `current="2.0.0"` gives `("old-ready",)`, and `current="3.0.0"` gives `("new-ready",)`.

   In every case, `waits` holds `old-wait`. Ruled out:
   - a shipped release's leftover row holding the current release (the stall);
   - leftovers ready beside the current release's rows (the freeze);
   - a later release jumping ahead of the leftovers;
   - a missing or unknown version changing today's order;
   - leftovers silently dropped.
2. `tests/unit/test_roadmap_release_boundary.py::test_current_release` writes `pyproject.toml` under `tmp_path`. It asserts:
   - version `0.3.0` gives `"0.3.0"`, `0.3.1` gives `"0.3.0"`, and `2.10.4` gives `"2.10.0"`;
   - None for each of: no file, invalid TOML, `[project]` without `version`, and version `dev`.

   Ruled out: a patch version read as its own release, a lexical minor (`2.1`), and a crash on a host without a Python version.
3. `tests/unit/test_roadmap_release_boundary.py::test_callers_pass_the_current_release`. With the `fixture` roadmap of `tests/unit/test_roadmap_status.py` and a `pyproject.toml` at version `2.0.0` under its `tmp_path`, `status(checkout)` returns a `next: n-nine` line. Without the file, its `next:` line is still `next: q-eleven, r-six`. With the `setup` fixture of `tests/unit/test_roadmap_author.py` and `pyproject.toml` at version `1.0.0` under `checkout.repo`, a wrapper around `roadmap.choose` that records its keyword arguments and returns the real result records `current="1.0.0"` from `author_ahead`. Ruled out: either caller ignoring the version.
4. `tests/unit/test_roadmap_ship.py::test_ship_steps` fakes `roadmap.run_gate`, `release.publishable`, `release.release`, `release.journal_release`, and `release.publish`, each recording its call in one shared list; `roadmap.child_env` may be faked too. The checkout is a `SimpleNamespace` whose repo is `tmp_path` holding `pyproject.toml` version `1.0.0`. It asserts:
   - with no `pyproject.toml`, `ship` returns `[]` and nothing is called;
   - a failed gate returns the gate's lines, and only `run_gate("1.0.0")` is called;
   - a passed gate with `release.publish` false calls `run_gate`, then `release` with part `minor` and the `child_env` of the checkout, then `journal_release` with the returned version and sha. It returns the gate lines plus `release: tagged v1.1.0 at <sha>`;
   - with `release.publish` true, the order is `run_gate`, `publishable`, `release`, `journal_release`, `publish`, and the last line is `publish: uploaded 1.1.0 to PyPI`;
   - with `release.publish` true and `publishable` raising `Refusal`, `ship` raises it after `run_gate` and before `release`.

   Ruled out: a release on a failed gate, a tag made before the publish preconditions, a publish with `release.publish` false, and a release with no `release` signal.
5. `tests/unit/test_roadmap_ship.py::test_release_helpers`:
   - `release.publishable` with `release.publish` true and the token unset raises the same `Refusal` text `publish` raises, and calls no git;
   - with the token set and `status_porcelain` returning ` M x`, it raises `uncommitted tracked files`;
   - with `release.publish` false and a clean tree, it returns None without reading the token;
   - `release.journal_release(MemoryJournal(), "0.4.0", "abc")` appends exactly one signal, `{"signal": "release", "version": "0.4.0", "tag": "v0.4.0", "commit": "abc"}`.

   Ruled out: the extracted checks drifting from `publish`, and a second shape of the `release` signal.
6. `tests/integration/test_roadmap_ship.py::test_ship_releases_then_waits_for_the_next_gate` uses a real git repo under `tmp_path`, built as `tests/integration/test_release.py::repository` does. `pyproject.toml` and `uv.lock` are at `1.0.0`, uv is faked to bump to `1.1.0`, the journal is real, and `config.yaml` is `CONFIG`. A committed `docs/roadmap.md` has:
   - `### 1.0.0`, one row, and the gate `<sys.executable> -c pass`;
   - `### 1.1.0`, one row, and the gate `<sys.executable> -c "raise SystemExit(1)"`.

   It asserts:
   - The first `ship` returns lines ending `gate 1.0.0: passed` and `release: tagged v1.1.0 at <HEAD>`. HEAD's subject is `release: 1.1.0`, and `v1.1.0^{commit}` is HEAD. The journal's signals are `roadmap_gate` (`1.0.0`, passed), then `release` (`1.1.0`, `v1.1.0`, HEAD). The faked uv saw only the two `uv version` calls (no `uv build`, no `uv publish`).
   - A second `ship` returns lines ending `gate 1.1.0: failed`. It makes no new tag and leaves HEAD unchanged.
   - In a fresh repo with `release.publish: true`, the token variable set in the env, and a modified tracked file, `ship` raises `Refusal` matching `uncommitted tracked files`. There is no `v1.1.0` tag, HEAD is unchanged, and the journal holds the passed `roadmap_gate` and no `release` signal.

   Ruled out: re-releasing a shipped version, a gate run against the old release after the bump, and a tag left behind by a refused publish.
7. `./dev.py test tests/unit/test_release.py tests/unit/test_release_publish.py tests/integration/test_release.py tests/integration/test_release_publish.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_table.py tests/unit/test_roadmap_gate.py tests/integration/test_roadmap_status.py tests/integration/test_roadmap_author.py tests/integration/test_roadmap_table.py tests/integration/test_roadmap_gate.py` exits 0 with those files unedited.
8. The docs command in `## Verification` exits 0: the `roadmap author` row of `docs/how-clutch-works.md` section 2.1 names the current release and the rows earlier releases left unfinished.
9. The unit check (`clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`) passes with `clutch/roadmap.py` and `clutch/release.py` at or above `test-gate.toml`'s `default = 90`, and `clutch/__main__.py` at or above its `13` floor.
10. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_roadmap_release_boundary.py tests/unit/test_roadmap_ship.py
./dev.py test tests/integration/test_roadmap_ship.py
./dev.py test tests/unit/test_release.py tests/unit/test_release_publish.py tests/integration/test_release.py tests/integration/test_release_publish.py tests/unit/test_roadmap_status.py tests/unit/test_roadmap_author.py tests/unit/test_roadmap_table.py tests/unit/test_roadmap_gate.py tests/integration/test_roadmap_status.py tests/integration/test_roadmap_author.py tests/integration/test_roadmap_table.py tests/integration/test_roadmap_gate.py
uv run python -c "import pathlib; q = chr(96); t = pathlib.Path('docs/how-clutch-works.md').read_text(); verbs = t.split('### 2.1 Verbs')[1].split('### 2.2')[0]; row = next(line for line in verbs.splitlines() if line.startswith('| ' + q + 'roadmap author')); assert 'current release' in row and 'left unfinished' in row"
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- `ship` tags, commits, or journals a `release` signal when the gate fails, or tags before `publishable` passes while `release.publish` is true;
- `ship` builds or uploads while `release.publish` is false, or pushes anything;
- `choose` with `current=None` orders rows differently from today, or drops a shipped release's leftover rows instead of ordering them after the current release's;
- `publish`'s refusal messages, roads, or check order change, or `clutch release` journals a different `release` signal body;
- it edits `docs/roadmap.md` or a plan, or adds a verb, flag, config field, journal signal, or `clutch/help.py` entry;
- a file outside `## Scope fence` changes, or any existing test is edited.

## Time budget
- expected: 90m
- stuck: 180m
