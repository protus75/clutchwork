---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- clutch/git.py
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/lockfile.py::Lockfile
- clutch/seams.py::ProcessExec
- clutch/runner.py::Refusal
- clutch/providers.py::child_env
- tests/unit/test_git_commit.py
- tests/unit/test_host_running.py
- tests/integration/test_cli.py::ENV
- tests/integration/test_cli.py::CONFIG
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1
- docs/roadmap-driver-plan.md#5.

## Goal / Why
`docs/roadmap.md` section 1 makes every release a minor version with a git tag, but nothing in clutch bumps a minor version or creates a tag: `./dev.py publish` bumps only the patch, and `clutch/git.py::Git` has no tag method. The 0.3.0 bump that opened the current phase was done by hand (`c761b213`: `uv version --bump minor`, a hand commit of `pyproject.toml` and `uv.lock` together with this repo's extension version, then an annotated tag `v0.3.0`). Every later phase boundary needs the same three steps, `docs/journal-sql-refactor-plan.md` (Release protocol, step 3) tags 0.3.0 with `clutch release --minor`, and the roadmap driver (`docs/roadmap-driver-plan.md` section 5, roadmap row 92 `release-publish`) builds publishing on top of this verb. Hosts version their own projects with the same verb, so it is a `clutch` verb, not a `./dev.py` subcommand.

After this change `uv run clutch release --minor` (or `--patch`) in a checkout:
1. takes the writer lock (`clutch.lock`), because it rewrites tracked files in the main checkout and commits on it, which a running drain or serve also merges into;
2. refuses (exit 2) when `pyproject.toml` or `uv.lock` already has uncommitted changes, because the release commit would otherwise carry them;
3. asks `uv version --bump <part> --dry-run --short` for the next version and refuses (exit 2) when tag `v<version>` already exists, so that a collision is found before anything is written (a tag collision found after the commit would leave an untagged release commit on main);
4. runs `uv version --bump <part>`, which rewrites `pyproject.toml` and `uv.lock`;
5. commits exactly those two files with message `release: <version>`, leaving every other working-tree and staged change alone;
6. creates the annotated tag `v<version>` on that commit, with message `release: <version>`;
7. prints `release: tagged v<version> at <commit sha>` and exits 0.

Every refusal leaves `pyproject.toml`, `uv.lock`, HEAD, and the tags as they were, except a failure of step 4 itself, whose refusal message tells the operator to restore the two files.

## Scope in / Scope out
Scope in:
- New `clutch/release.py` with one async function that takes the repo path, a `Git`, a `ProcessExec`, the child env, and the part (`"minor"` or `"patch"`), runs steps 2 to 6 above, and returns the version and the commit sha. Every git call goes through `Git`; both `uv` calls go through the `ProcessExec` seam with argv lists `["uv", "version", "--bump", part, "--dry-run", "--short"]` and `["uv", "version", "--bump", part]` and a finite module-level timeout. The version is the dry run's stripped stdout; the bump's stdout is not parsed. A non-zero `uv` exit raises `runner.Refusal` whose message includes the last non-blank stderr line. The dirty check uses `Git.status_porcelain` restricted to the two paths; the commit uses `Git.commit(..., only=["pyproject.toml", "uv.lock"])`; the tag-existence check goes through `Git` (for example `rev_parse` of `refs/tags/v<version>`, whose failure means absent).
- `clutch/release.py` is a new file under `test-gate.toml`'s `default = 90` unit coverage floor, so `tests/unit/test_release.py` exercises every branch with a scripted fake exec, as `tests/unit/test_git_commit.py` does.
- `clutch/git.py`: new `Git.tag(dir, name, message)` that runs `git tag -a <name> -m <message>` on HEAD, passing `name` through `_ref`.
- `clutch/__main__.py`: in `_parser`, a `release` subcommand with a required, mutually exclusive `--minor` / `--patch` pair (no default part, no `--major`). In `main`, after the config load and checkout build, the `release` branch acquires `Lockfile(config.state_dir, verb="release", ...)` as `dismiss` does (without its `runner.reap`), calls the `clutch/release.py` function with `checkout.git`, `checkout.exec_`, and `child_env(env, config)`, releases the lock in a `finally`, prints the step 7 line, and returns 0. `LockHeld`, `runner.Refusal`, and `ExecutableNotFound` (no `uv` on PATH) already map to exit 2 through `main`'s existing handler; nothing is added to it.
- `clutch/docs/host-running.md`: add a `release` row to the verb table (works while serve runs: No) saying it bumps the version with `--minor` or `--patch`, commits `pyproject.toml` and `uv.lock`, tags `v<version>`, and publishes nothing; add `release` to the "Stop serve before ..." sentence's list of verbs that take the writer lock. `tests/unit/test_host_running.py` requires the row; it is not edited.
- `docs/how-clutch-works.md` section 2.1: add a `release --minor\|--patch` row to the verb table (Lock: yes) describing steps 1 to 7. Nothing else in the file changes.
- New tests: `tests/unit/test_release.py` and `tests/integration/test_release.py`.

Scope out:
- Publishing, pushing, or uploading anything; a `release` journal signal; a `release` config block; `clutch publish`; `./dev.py vscode-publish` (all roadmap row 92 `release-publish`).
- `dev.py`: `./dev.py publish` keeps bumping only the patch, and no `release` subcommand is added there.
- A `--major` or any other bump kind; refusing on the current branch name.
- The VS Code extension version, `vscode-clutchwork/`, `clutch/help.py`, and `clutch/observe.py`: `release` is not an extension surface.
- `README.md`, `CLAUDE.md`, `AGENTS.md`, `clutch/hostfiles.py`.
- `docs/roadmap.md` and the plan documents under `docs/`: row linking and striking is done by a person or the roadmap driver, not by the implementing ticket.

## Scope fence
- clutch/release.py
- clutch/git.py
- clutch/__main__.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_release.py
- tests/integration/test_release.py

## Acceptance criteria
1. `tests/unit/test_release.py::test_minor_release_bumps_commits_and_tags` drives the `clutch/release.py` function for `"minor"` over a `Git` built on a scripted fake exec (clean status, dry run printing `0.2.0`, tag absent, bump exit 0, commit succeeding) and asserts it returns version `0.2.0` and the scripted HEAD sha, and that the recorded argvs contain, in this order, `["uv", "version", "--bump", "minor", "--dry-run", "--short"]`, `["uv", "version", "--bump", "minor"]`, git `commit -m "release: 0.2.0" --only -- pyproject.toml uv.lock`, then git `tag -a v0.2.0 -m "release: 0.2.0"` as the last call, with exactly two `uv` calls. Ruled out: a bump with no dry run before it, a commit without `--only` (which would carry other staged changes), a tag made before the commit, and a lightweight tag (no `-a`).
2. `tests/unit/test_release.py::test_patch_release_passes_patch` runs the same function with `"patch"` and a dry run printing `0.1.6`, and asserts both `uv` argvs carry `patch` and the tag argv names `v0.1.6`. Ruled out: a hard-coded `minor`.
3. `tests/unit/test_release.py::test_dirty_version_files_refuse` scripts the status call to report ` M pyproject.toml` and asserts the function raises `runner.Refusal` naming `pyproject.toml` and that the status call was the only exec call. Ruled out: any `uv`, commit, or tag call after a dirty status.
4. `tests/unit/test_release.py::test_existing_tag_refuses` scripts the tag-existence check to find `v0.2.0` and asserts `runner.Refusal` naming `v0.2.0`, with the dry run as the only `uv` call and no commit or tag call. Ruled out: a bump or commit before the collision is detected.
5. `tests/unit/test_release.py::test_uv_failure_refuses` covers both `uv` calls: a dry run exiting 2 with stderr ending in `error: No version field found` raises `runner.Refusal` containing that line, with no further exec call; a bump exiting 1 with stderr ending in `error: lock failed` after a clean dry run and absent tag raises `runner.Refusal` containing that line and naming both `pyproject.toml` and `uv.lock` as the files to restore, with no commit or tag call. Ruled out: committing or tagging after a failed `uv` call, a refusal that drops `uv`'s error, and a bump refusal that does not tell the operator which files to restore.
6. `tests/unit/test_release.py::test_git_tag_argv` asserts `Git.tag(Path("/repo"), "v0.2.0", "release: 0.2.0")` runs exactly `git -C /repo tag -a v0.2.0 -m "release: 0.2.0"`, and that `Git.tag` with name `-f` raises `ValueError` before any exec call.
7. `tests/unit/test_release.py::test_parser_requires_one_part` asserts `_parser().parse_args` raises `SystemExit` for `["release"]`, `["release", "--minor", "--patch"]`, and `["release", "--major"]`, and accepts `["release", "--minor"]` and `["release", "--patch"]`. Ruled out: an implicit default part.
8. `tests/integration/test_release.py::test_release_commits_and_tags` builds a real git repo in `tmp_path` holding `config.yaml`, a committed `pyproject.toml` at version `0.1.5`, a committed `uv.lock`, one modified tracked file, and one staged change to another tracked file, and monkeypatches `SubprocessExec.run` to answer `uv` argvs (the dry run prints `0.2.0`; the bump rewrites the version in both files) while passing git argvs to the real method. `main(["release", "--minor"], cwd=repo, env=...)` returns 0 and prints `release: tagged v0.2.0 at <HEAD sha>`; HEAD's subject is `release: 0.2.0`; `git show --name-only --format= HEAD` lists exactly `pyproject.toml` and `uv.lock`; `git cat-file -t v0.2.0` prints `tag`; `git rev-parse v0.2.0^{commit}` equals HEAD; the modified file is still modified and unstaged and the staged change is still staged and uncommitted. Ruled out: a lightweight tag, a tag on the old HEAD, and a commit that carries the unrelated changes.
9. `tests/integration/test_release.py::test_release_refusals_change_nothing` runs `main(["release", "--minor"], ...)` in three repos built as in criterion 8: one whose `pyproject.toml` is modified, one where tag `v0.2.0` already exists, and one where the test holds `Lockfile(state_dir, ...)` itself. Each returns 2 with stderr starting `clutch release:`; the held-lock case names `clutch.lock` and records no `uv` call; in all three HEAD, the tag list, and the bytes of `pyproject.toml` and `uv.lock` are unchanged. Ruled out: a refusal reached only after the bump, commit, or tag.
10. The unit check (`clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`) passes with `clutch/release.py` at or above `test-gate.toml`'s `default = 90`.
11. `./dev.py test tests/unit/test_host_running.py` exits 0 with the `release` row in `clutch/docs/host-running.md`, and the docs command in `## Verification` exits 0: the `docs/how-clutch-works.md` section 2.1 verb table has a row starting with `release`, and the host-running "Stop serve before" sentence names `release`.
12. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_release.py tests/unit/test_host_running.py
./dev.py test tests/integration/test_release.py
uv run python -c "import pathlib; t = pathlib.Path('docs/how-clutch-works.md').read_text(); verbs = t.split('### 2.1 Verbs')[1].split('### 2.2')[0]; assert '| ' + chr(96) + 'release ' in verbs; h = pathlib.Path('clutch/docs/host-running.md').read_text(); stop = next(line for line in h.splitlines() if line.startswith('Stop serve before')); assert chr(96) + 'release' + chr(96) in stop"
./dev.py test
```

## Definition of rejected
The branch is rejected if it publishes, pushes, or uploads anything, journals a `release` signal, or adds a `release` config block; if it changes `./dev.py publish` or adds a `dev.py` subcommand; if it rewrites the version in `pyproject.toml` or `uv.lock` itself instead of through `uv version`; if the release commit can carry any path other than `pyproject.toml` and `uv.lock`; if it creates a lightweight tag; if a dirty-file, existing-tag, held-lock, or dry-run refusal leaves the bump, a commit, or a tag behind; if it offers a default part or a `--major`; or if it adds an extension menu item, a `clutch/help.py` entry, or a `vscode-clutchwork/` version bump.

## Time budget
- expected: 60m
- stuck: 150m
