---
state: confirmed
source: human
priority: P2
kind: bug
---

## Depends on
- none

## Context
- clutch/meta.py::_files
- clutch/meta.py::check
- clutch/__main__.py::_run_meta
- tests/unit/test_meta_cli.py
- tests/unit/test_meta_refresh.py

## Goal / Why
`clutch meta check`, `meta refresh` and `meta fill` given a path argument that selects no file exit 0 and print nothing. `meta._files` walks only git-tracked `.md`/`.py` files under a configured `meta.paths` root and silently drops a named path that matches none of them. A new, untracked document is the common case: `meta check` reports it clean and `meta refresh`/`fill` write no block, a false green. Observed 2026-11-22 writing `docs/provider-roles-plan.md` (`fill` and `check` both exited 0 with no block until the file was `git add -N`'d), and reproduced in `evidence/meta-untracked.txt`.

When done, each of the three verbs refuses before doing any work when a named path selects no file: it prints one line per such path naming it with a paved road, and exits 2. The road says: for a new file, run `git add -N <path>` so it is tracked, then rerun; otherwise name a `.md` or `.py` path under a configured `meta.paths` root. Paths that select files behave exactly as today, and calls with no paths are unchanged.

## Boundary contract
### Meta verb path selection
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators and chat sessions running `clutch meta check|refresh|fill <paths>`; Check's meta stage, which calls `meta.check`/`metafill.fill` directly without paths and is unaffected
- observable change: a named path selecting no tracked configured file is refused with exit 2 and a paved road, instead of exit 0 with no output
- compatibility: no-path calls and paths that select files keep their output and exit codes; `meta.check`, `meta.refresh` and `metafill.fill` signatures are unchanged
- acceptance: an untracked or out-of-root named path makes each verb exit 2 naming the path and `git add -N`; a tracked path still exits as before
- tests: tests/unit/test_meta_path_selects_nothing.py, tests/regress_meta_path_selects_nothing.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- In `clutch/__main__.py::_run_meta`, before dispatching any verb, collect each entry of `paths` for which `meta._files(config, tracked, (path,))` yields nothing. If any, print one line per path to stderr through the existing `_fail` helper, prefixed with the verb (`meta check`, `meta refresh`, `meta fill`), naming the path and the paved road from Goal / Why, and return 2 without calling the verb.
- Add `tests/unit/test_meta_path_selects_nothing.py` using `MemoryFS` and `config` from `tests/unit/test_meta_refresh.py`, driving `_run_meta` for all three verbs (fill with a stub `ask` that must not be called).
- Add the carried reproducer `tests/regress_meta_path_selects_nothing.py`. It inserts the repo root on `sys.path`, imports `_run_meta` from `clutch.__main__` and `MemoryFS` and `config` from `tests.unit.test_meta_refresh` (printing `{"regression_result": "error"}` with a non-zero exit if an import fails), then runs `_run_meta("check", config(), Path("/repo"), fs, ["docs/a.md"], "123456789", ("docs/new.md",))` with `docs/new.md` present in the fake filesystem but untracked. A return of 0 prints `{"regression_result": "defect"}` and exits 1; a return of 2 prints `{"regression_result": "pass"}` and exits 0; anything else prints `error` and exits 2. It writes nothing to disk.
- In `docs/how-clutch-works.md` section 2, update only the `meta refresh`, `meta check` and `meta fill` rows to say a named path that selects no tracked file under a configured root is refused.
Scope out: `clutch/meta.py`, `clutch/metafill.py`, the CLI help text (its `2 on refusal` already covers this), and any other verb that takes paths.

## Scope fence
- clutch/__main__.py
- docs/how-clutch-works.md
- tests/unit/test_meta_path_selects_nothing.py
- tests/regress_meta_path_selects_nothing.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_meta_path_selects_nothing.py` passes and covers: for each of `check`, `refresh` and `fill`, `_run_meta` with tracked `["docs/a.md"]` and paths `("docs/new.md",)` returns 2, not 0; stderr names `docs/new.md` and `git add -N`; no file in the `MemoryFS` changes; and the `fill` stub `ask` is never called.
2. The same test file covers a path outside every configured root (`src/x.py`) returning 2, and a mixed call `("docs/a.md", "docs/new.md")` returning 2 without writing `docs/a.md`.
3. The same test file covers `_run_meta("check", ...)` with paths `("docs/a.md",)` on a tracked file carrying a valid block returning 0, so selecting paths still pass.
4. `./dev.py test tests/unit/test_meta_cli.py` passes unchanged.
5. `uv run python tests/regress_meta_path_selects_nothing.py` prints `{"regression_result": "pass"}` on the branch.

## Verification
```
./dev.py test tests/unit/test_meta_path_selects_nothing.py tests/unit/test_meta_cli.py
uv run python tests/regress_meta_path_selects_nothing.py
```

## Definition of rejected
A verb still exits 0 for a named path that selects nothing, writes or calls the model before refusing, or changes behavior for no-path calls or paths that select files.

## Time budget
- expected: 15m
- stuck: 30m

## Regression
```
uv run python tests/regress_meta_path_selects_nothing.py
```
- carries: tests/regress_meta_path_selects_nothing.py
