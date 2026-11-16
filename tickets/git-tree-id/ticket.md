---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- clutch/git.py::Git
- clutch/git.py::GitError
- docs/evidence-trail-plan.md#2. Envelope schema (`clutch.evidence.call`, version 1.0)
- tests/unit/test_git_commit.py
- tests/integration/test_git.py::test_ls_files_lists_committed_files_not_untracked_files

## Goal / Why
The evidence envelope (`docs/evidence-trail-plan.md`, roadmap row 29, the next ticket `evidence-envelope`) records the git tree each model call saw before it ran (`repo.tree_before` in `start.json`) and, for the writing surface, the tree it left and the paths it changed (`repo.tree_after` and `repo.changed_paths` in `end.json`). The plan takes both from a temporary index, so recording them never touches the branch, the real index or the reflog. All git access goes through `clutch/git.py` (CLAUDE.md, "All git through `git.py`"), and `Git` has no operation that does either today. After this change `Git` has two argv-list operations the envelope calls:

- `Git.tree_id(dir, index) -> str`: runs `git -C <dir> add -A` and then `git -C <dir> write-tree`, both with `GIT_INDEX_FILE` set to the caller's `index` path, and returns the tree id `write-tree` prints. The tree covers tracked, modified and untracked files that `.gitignore` does not exclude.
- `Git.tree_changes(dir, before, after) -> list[str]`: runs `git -C <dir> diff --name-only <before> <after>` on two tree ids and returns the changed paths.

## Scope in / Scope out
Scope in:
- `clutch/git.py`: add `tree_id` and `tree_changes` to `Git`, each built on the existing `_call`/`_run` helpers so it is dir-pinned and raises `GitError` on a nonzero exit. `tree_id` passes `env={**self._env, "GIT_INDEX_FILE": str(index)}` to both of its commands, runs `write-tree` only after `add -A` succeeded, and returns the stripped `write-tree` output. It does not take the commit lock: it writes only the caller's index file and git objects, never the real index. The caller owns `index` (its directory must exist; the caller removes the file afterwards). `tree_changes` passes both ids through `_ref` and returns the output split into lines, `[]` for empty output.
- New tests in two new files: `tests/unit/test_git_tree_id.py` runs the new lines against a fake `ProcessExec`, as `clutch/git.py` has a positive unit floor in `test-gate.toml`; `tests/integration/test_git_tree_id.py` runs both operations against a real repository under `tmp_path` through `SubprocessExec`, with the same isolating env as `tests/integration/test_git.py::test_ls_files_lists_committed_files_not_untracked_files` (it builds its own env and repository; it imports only `commit_lock` from `tests/integration/test_git.py`).

Scope out:
- Every caller: `clutch/providers.py`, `clutch/evidence/` and the rest stay unchanged; `evidence-envelope` calls these operations.
- Choosing, creating or removing the temporary index path, and any change to existing `Git` operations or `tests/integration/test_git.py`.

Simpler approach rejected: `git stash create` or `commit-tree` would also capture the working tree but write refs or need a commit; a temporary index plus `write-tree` is the plan's mechanism and writes nothing outside the object store and the caller's file.

## Scope fence
- clutch/git.py
- tests/unit/test_git_tree_id.py
- tests/integration/test_git_tree_id.py

## Acceptance criteria
1. `tests/unit/test_git_tree_id.py::test_tree_id_argv_env_and_result`: with a fake exec answering `(0, "added\n", "")` then `(0, "abc123\n", "")`, `tree_id(Path("/repo"), Path("/state/x.index"))` issues exactly `["git", "-C", "/repo", "add", "-A"]` and then `["git", "-C", "/repo", "write-tree"]`, each with `env["GIT_INDEX_FILE"] == "/state/x.index"` and every key of the `Git` env preserved, and returns `"abc123"`, not the `add` output `"added"`.
2. `tests/unit/test_git_tree_id.py::test_tree_id_failure_raises`: when `add -A` exits 1, `tree_id` raises `GitError` carrying that argv and issues no `write-tree`; it returns no empty string.
3. `tests/unit/test_git_tree_id.py::test_tree_changes_argv_and_lines`: `tree_changes(Path("/repo"), "t1", "t2")` issues `["git", "-C", "/repo", "diff", "--name-only", "t1", "t2"]` and returns `["a.py", "b/c.py"]` for output `"a.py\nb/c.py\n"` and `[]`, not `[""]`, for empty output; an option-shaped id such as `"-x"` raises `ValueError` before any process runs.
4. `tests/integration/test_git_tree_id.py::test_tree_id_captures_worktree_without_touching_index`: in a real repository with one committed file, that file then modified and one new untracked file, `tree_id` with an index path under `tmp_path` returns a tree whose `git ls-tree -r` lists the untracked file and the modified file's new blob; the bytes of `.git/index`, the output of `git status --porcelain`, `HEAD` and the `main` reflog are identical before and after the call.
5. `tests/integration/test_git_tree_id.py::test_tree_changes_lists_paths_between_trees`: `tree_changes(repo, <HEAD^{tree}>, <the tree from tree_id>)` returns exactly the modified and the untracked file's paths, sorted as git prints them; with the same id twice it returns `[]`.

## Verification
```
./dev.py test tests/unit/test_git_tree_id.py
./dev.py test tests/integration/test_git_tree_id.py tests/integration/test_git.py
```

## Definition of rejected
The branch changes an existing `Git` operation or `tests/integration/test_git.py`, adds a caller outside the new tests, takes the commit lock in `tree_id`, writes or reads the real index, creates a ref or reflog entry, or uses `shell=True` or a string-assembled command.

## Time budget
- expected: 25m
- stuck: 60m
