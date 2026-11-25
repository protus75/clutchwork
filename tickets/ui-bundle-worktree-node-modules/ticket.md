---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Runs before
- mcp-dashboard-ux-parity

## Context
- dev.py
- tests/unit/test_dev_ui_bundle.py
- tests/integration/test_mcp_app_dashboard.py

## Goal / Why
Fix `dev.build_ui_bundle` so it resolves `node_modules/.bin/esbuild` (and sets `NODE_PATH`) from the main git checkout when invoked inside a linked git worktree (such as `.clutch/state/worktrees/<stem>`) that does not have its own `node_modules/`.

Currently, `dev.py::build_ui_bundle` hardcodes `root / "node_modules/.bin/esbuild"`, which does not exist in fresh git worktrees. As a result, any ticket whose `## Verification` runs `tests/integration/test_mcp_app_dashboard.py::test_dashboard_bundle` (including `mcp-dashboard-ux-parity`) fails Check with `RuntimeError: ui-bundle: missing source or esbuild: [Errno 2] No such file or directory: '.../.clutch/state/worktrees/<stem>/node_modules/.bin/esbuild'`.

## Boundary contract

### UI bundle builder (`dev.build_ui_bundle`)
- disposition: extend
- owner: dev.py
- consumers: `./dev.py ui-bundle`, `tests/integration/test_mcp_app_dashboard.py`, `tests/integration/test_mcp_dashboard_wheel.py`, `tests/unit/test_dev_ui_bundle.py`
- observable change: `dev.build_ui_bundle` resolves `node_modules` via a private helper `_resolve_node_modules(root: Path) -> Path`. When `(root / "node_modules/.bin/esbuild").is_file()` is false and `(root / ".git").is_file()` contains a `gitdir:` pointer to `<main>/.git/worktrees/<name>` whose `<main>/node_modules/.bin/esbuild` exists as a regular file, `build_ui_bundle` invokes `<main>/node_modules/.bin/esbuild` and passes `env={**os.environ, "NODE_PATH": str(main_root / "node_modules")}` to `run_cmd` so `esbuild` resolves npm packages (`@modelcontextprotocol/ext-apps`, `zod`) from the main checkout. When `root` has its own `node_modules/.bin/esbuild` or no worktree fallback exists, `build_ui_bundle` keeps using `root / "node_modules/.bin/esbuild"` without adding an `env` keyword argument to `run_cmd`, preserving the existing `RuntimeError("ui-bundle: missing source or esbuild: ...")` failure when `esbuild` is absent.
- compatibility: all existing `build_ui_bundle(root=ROOT, out=None, run_cmd=subprocess.run)` callers, default output path, esbuild CLI flags, and `run_cmd` call signature when not using the worktree fallback remain unchanged.
- acceptance: `tests/unit/test_dev_ui_bundle_worktree.py`, `tests/unit/test_dev_ui_bundle.py`, and `tests/integration/test_mcp_app_dashboard.py` verify local resolution, relative and absolute worktree `gitdir:` fallback with `NODE_PATH`, missing-fallback error behavior, and real dashboard bundling inside a linked worktree.
- tests: `tests/unit/test_dev_ui_bundle_worktree.py`, `tests/unit/test_dev_ui_bundle.py`, `tests/integration/test_mcp_app_dashboard.py`
- post-merge source of truth: `dev.py`

## Scope in / Scope out
**Scope in:**
- `dev.py`:
  - Add helper `_resolve_node_modules(root: Path) -> Path`:
    - If `(root / "node_modules/.bin/esbuild").is_file()`, return `root / "node_modules"`.
    - Else if `(root / ".git").is_file()`, read it and look for a line starting with `gitdir:` (after stripping whitespace). Resolve the path after `gitdir:` relative to `root` (`(root / raw).resolve()`). If `gitdir.parent.name == "worktrees"` and `len(gitdir.parents) >= 3`, compute `main_root = gitdir.parents[2]`; if `(main_root / "node_modules/.bin/esbuild").is_file()`, return `main_root / "node_modules"`.
    - Ignore `OSError` when reading `(root / ".git")` and fall through to returning `root / "node_modules"`.
  - In `build_ui_bundle(root=ROOT, out=None, run_cmd=subprocess.run) -> Path`:
    - Normalize `root = Path(root)` and call `node_modules = _resolve_node_modules(root)`.
    - Build the `run_cmd` argv using `str(node_modules / ".bin/esbuild")`.
    - Pass `env={**os.environ, "NODE_PATH": str(node_modules)}` to `run_cmd` ONLY when `node_modules != root / "node_modules"`; omit `env` when `node_modules == root / "node_modules"` so existing fake `run_cmd` callers (such as `tests/unit/test_dev_ui_bundle.py`) retain their exact keyword arguments.
- `tests/unit/test_dev_ui_bundle_worktree.py` (new):
  - Pure `tmp_path` unit tests (no repo-file reads, no real subprocesses) covering:
    - `_resolve_node_modules` prefers `root / "node_modules"` when `(root / "node_modules/.bin/esbuild").is_file()` is true, even if `.git` points to a worktree whose main checkout also has `esbuild`.
    - `_resolve_node_modules` resolves `<main>/node_modules` when `root / ".git"` is a file with an absolute `gitdir:` pointing to `<main>/.git/worktrees/<name>` and `<main>/node_modules/.bin/esbuild` exists.
    - `_resolve_node_modules` resolves `<main>/node_modules` when `root / ".git"` is a file with a relative `gitdir:` pointing to `<main>/.git/worktrees/<name>` and `<main>/node_modules/.bin/esbuild` exists.
    - `_resolve_node_modules` returns `root / "node_modules"` when neither checkout has `esbuild`, when `.git` is missing or a directory, or when `.git` does not point under a `worktrees/` parent.
    - `build_ui_bundle` invokes `<main>/node_modules/.bin/esbuild` with `env["NODE_PATH"] == str(main / "node_modules")` on worktree fallback, and omits `env` when using `root / "node_modules"`.
- `tests/regression/ui_bundle_worktree_node_modules.py` (new):
  - Deterministic, pure-Python reproducer speaking the `regression_result` JSON protocol using only base-compatible `dev.build_ui_bundle(root=..., out=..., run_cmd=...)`:
    - Checks that `dev.build_ui_bundle` is importable; if missing, prints `{"regression_result": "error"}` to stdout (diagnostics to stderr) and exits 2.
    - Creates a temporary main directory with `node_modules/.bin/esbuild` and `.git/worktrees/wt`, plus a temporary worktree directory containing `.git` (`gitdir: <main>/.git/worktrees/wt`) and the 4 bundle source files (`vscode-clutchwork/media/view.css`, `clutch/ui/dashboard.css`, `vscode-clutchwork/media/ticket-lifecycle.svg`, `clutch/ui/app.js`).
    - Calls `dev.build_ui_bundle(root=wt, out=wt / "dashboard.html", run_cmd=fake_run)` where `fake_run` raises `FileNotFoundError` if `Path(argv[0]).is_file()` is false and otherwise returns a stub result with `returncode=0, stdout="console.log(1);", stderr=""`.
    - Verifies `build_ui_bundle` succeeds, invokes `main / "node_modules/.bin/esbuild"`, passes `env["NODE_PATH"] == str(main / "node_modules")`, and writes `dashboard.html`.
    - Prints ONLY one JSON object to stdout: `{"regression_result": "pass"}` (exit 0) when all checks pass, or `{"regression_result": "defect"}` (exit 1) when `build_ui_bundle` raises `RuntimeError` or invokes the wrong path/env; diagnostics go to stderr.

**Scope out:**
- No edits to `tests/unit/test_dev_ui_bundle.py`, `tests/integration/test_mcp_app_dashboard.py`, `clutch/`, or any of the 7 hot test files (`tests/integration/test_daemon_composition.py`, `tests/integration/test_drain.py`, `tests/integration/test_mergequeue.py`, `tests/integration/test_stages.py`, `tests/integration/test_cli.py`, `tests/integration/test_watch.py`, `tests/integration/serve_rig.py`).
- No installing or symlinking `node_modules/` in git worktrees.
- No committing of gitignored `clutch/ui/dashboard.html`.

## Scope fence
- dev.py
- tests/unit/test_dev_ui_bundle_worktree.py
- tests/regression/ui_bundle_worktree_node_modules.py

## Acceptance criteria
1. `_resolve_node_modules(root)` returns `root / "node_modules"` when `(root / "node_modules/.bin/esbuild").is_file()` is true (not the worktree fallback), returns `<main>/node_modules` when `root` lacks `esbuild` and `root / ".git"` is a file with an absolute or relative `gitdir:` under `<main>/.git/worktrees/<name>` whose `<main>/node_modules/.bin/esbuild` exists (not `root / "node_modules"`), and returns `root / "node_modules"` when neither checkout has `esbuild` or `.git` is not a worktree pointer (not raising an unhandled exception); verified by `./dev.py test tests/unit/test_dev_ui_bundle_worktree.py`.
2. `build_ui_bundle` invokes `<main>/node_modules/.bin/esbuild` with `env["NODE_PATH"] == str(main / "node_modules")` on worktree fallback (not omitting `NODE_PATH` or invoking the missing worktree path), and omits the `env` keyword argument when `node_modules == root / "node_modules"` (not breaking callers expecting the original `run_cmd` signature); verified by `./dev.py test tests/unit/test_dev_ui_bundle.py tests/unit/test_dev_ui_bundle_worktree.py`.
3. `tests/integration/test_mcp_app_dashboard.py::test_dashboard_bundle` builds and validates the MCP dashboard bundle from inside a linked git worktree without a local `node_modules/` directory (not failing with `RuntimeError: ui-bundle: missing source or esbuild`); verified by `./dev.py test tests/integration/test_mcp_app_dashboard.py`.
4. The regression reproducer exits 0 with `{"regression_result": "pass"}` on the fixed branch and exits non-zero with `{"regression_result": "defect"}` on the merge base; verified by `uv run python tests/regression/ui_bundle_worktree_node_modules.py`.

## Verification
```
./dev.py test tests/unit/test_dev_ui_bundle.py tests/unit/test_dev_ui_bundle_worktree.py tests/integration/test_mcp_app_dashboard.py
```

## Definition of rejected
- `build_ui_bundle` fails with `missing source or esbuild` when invoked from a linked git worktree whose main checkout has `node_modules/.bin/esbuild`.
- `build_ui_bundle` passes an extra `env` keyword argument to `run_cmd` when `node_modules == root / "node_modules"`, breaking `tests/unit/test_dev_ui_bundle.py`.
- Any unit test under `tests/unit/test_dev_ui_bundle_worktree.py` reads repo files outside `tmp_path` or spawns a real subprocess.
- Any edit occurs outside `## Scope fence`.

## Time budget
- expected: 10m
- stuck: 20m

## Regression
```
uv run python tests/regression/ui_bundle_worktree_node_modules.py
```
- carries: tests/regression/ui_bundle_worktree_node_modules.py
