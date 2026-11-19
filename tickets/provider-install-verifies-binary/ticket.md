---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
- none

## Context
- clutch/providers.py::cli_status
- clutch/providers.py::installed_version
- tests/unit/test_install_verb.py
- tests/regress_already_satisfied.py

## On-demand
- clutch/__main__.py

## Goal / Why
After `clutch provider install <name>` exits 0, the installed provider CLI runs. Today it can exit 0 with a CLI that cannot start. On 2026-11-18, with pnpm 10.34.5, `clutch provider install claude` printed `claude: project, package @anthropic-ai/claude-code` (no version) and exited 0. The CLI was broken: `node_modules/.bin/claude --version` exited 1 with `Error: claude native binary not installed. Either postinstall did not run (--ignore-scripts, some pnpm configs) ...` (see `evidence/`). pnpm 10 skips dependency build scripts unless a package is allowed to build. `@anthropic-ai/claude-code` downloads its native binary in its postinstall script, so `pnpm add -D @anthropic-ai/claude-code@latest` leaves a binary that cannot run. The install handler in `clutch/__main__.py` (`handle_install`) then reads `cli_status`, which ignores the `--version` exit code. The empty version prints as nothing, and the verb exits 0. Every provider child puts the checkout's `node_modules/.bin` first on `PATH` (`clutch/providers.py::tool_env`). The next drain therefore calls the broken binary for every claude-routed stage, and every run fails until someone repairs the binary by hand. This happens on every claude upgrade through the verb, so it will recur.

## Scope in / Scope out
Scope in, all in `handle_install` inside `clutch/__main__.py::main`, plus tests:
- The pnpm argv becomes `["pnpm", "add", "-D", f"--allow-build={package}", f"{package}@latest"]`, so pnpm runs the installed provider package's own build script. pnpm 10.34.5's `pnpm add --help` lists `--allow-build` as "A list of package names that are allowed to run postinstall scripts during installation".
- After a named install, when `cli_status` reports no version (`status.version is None`), raise `runner.Refusal`. The message names the provider and says its CLI printed no version after install. The road says to rerun `clutch provider install <name>`, and to check that pnpm allowed the package's build script if the refusal repeats. The exit code is 2.
- Update the `install` command's `exits=` help text in the same file to list this refusal.
- In `tests/unit/test_install_verb.py`, update the one pnpm argv assertion to the new argv, and add a test with a fake exec whose `claude --version` returns `(1, "", "Error: claude native binary not installed.\n")`. The test asserts that `provider install claude` returns 2, not 0, and that stderr names `claude`.
- Add the carried reproducer `tests/regress_provider_install_broken_binary.py`, written in the style of `tests/regress_already_satisfied.py`. It calls `clutch.__main__.main(["provider", "install", "claude"], ...)` with `SubprocessExec` monkeypatched to an in-process fake: pnpm returns `(0, "", "")`, and `claude --version` returns `(1, "", "Error: claude native binary not installed.\n")`. It prints `pass` when the call returns 2 and `defect` when it returns 0, and maps any exception to `error`.

Scope out: the bare report (`clutch provider install` with no names) keeps today's output and exit code. Leave the engine's provider preflight, `cli_status`, `CliStatus`, `clutch provider probe`, `package.json` and the docs unchanged. The verb tables already describe the verb without its refusals.

## Scope fence
- clutch/__main__.py
- tests/unit/test_install_verb.py
- tests/regress_provider_install_broken_binary.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_install_verb.py` passes. It asserts the named-install pnpm argv is `["pnpm", "add", "-D", "--allow-build=@openai/codex", "@openai/codex@latest"]`, not the old argv without `--allow-build`. It also asserts that `provider install claude` with a `--version` that exits 1 and prints no version returns 2, not 0.
2. `uv run python tests/regress_provider_install_broken_binary.py` prints `{"regression_result": "pass"}` and exits 0 on the branch.
3. `./dev.py test tests/unit/test_main_provider_group.py tests/unit/test_main_help.py` passes: the bare report and the help standard are unchanged.

## Verification
```
./dev.py test tests/unit/test_install_verb.py tests/unit/test_main_provider_group.py tests/unit/test_main_help.py
uv run python tests/regress_provider_install_broken_binary.py
```

## Definition of rejected
A named install whose CLI prints no version still exits 0. The pnpm argv lacks `--allow-build` for the installed package. The bare report changes output or exit code. Or the change touches `cli_status`, the engine preflight, or any file outside the fence.

## Time budget
- expected: 15m
- stuck: 30m

## Regression
```
uv run python tests/regress_provider_install_broken_binary.py
```
- carries: tests/regress_provider_install_broken_binary.py
