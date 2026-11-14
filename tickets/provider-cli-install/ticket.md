---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- chupa/providers.py::CliAdapter
- chupa/providers.py::ClaudeAdapter
- chupa/providers.py::CodexAdapter
- chupa/providers.py::QwenAdapter
- chupa/providers.py::ADAPTERS
- chupa/providers.py::child_env
- chupa/providers.py::ProviderLLM.preflight
- chupa/__main__.py::_parser
- chupa/__main__.py::main
- chupa/seams.py::ExecutableNotFound
- dev.py
- .gitignore
- tests/unit/test_probe_verb.py
- tests/unit/test_docs_verb.py
- tests/unit/test_qwen_adapter.py::test_qwen_argv_and_env
- tests/integration/test_providers.py::PreflightExec
- tests/integration/test_providers.py::test_llm_call_env_restores_only_the_serving_providers_key
- tests/integration/test_providers.py::test_preflight_version_children_carry_no_provider_key
- tests/integration/test_providers.py::test_preflight_reports_a_stale_cli_without_refusing_the_run
- tests/integration/test_closed_sets.py::test_providers_closed_sets_and_constants
- tests/integration/test_dev.py::test_suggest_forwards_summary
- chupa/docs/host-running.md
- chupa/docs/host-qwen.md
- chupa/docs/host-contract.md#Install
- docs/how-chupa-works.md#2.1 Verbs
- docs/how-chupa-works.md#2.2
- docs/how-chupa-works.md#8.1 Providers

## On-demand
- tests/integration/test_daemon_composition.py
- docs/gemini-graphics-refactor-plan.md
- README.md

## Goal / Why
chupa drives each provider through its agent CLI (`claude`, `codex`, `qwen`) and expects that binary on `PATH`. The pnpm package of each CLI is written only in every host's `config.yaml` (`package`, required for the preflight's latest-release check) and in the guides; the only install road chupa prints is the text `pnpm add -g <package>@latest` inside two preflight messages. A host has no way to declare which CLIs it uses, no verb installs or updates them, and a CLI installed inside the project is not found.

The operator asked for optional dependencies for the Claude, Codex, Gemini, and Ollama CLI tools. A Python extra cannot carry them: all four agent CLIs are npm packages and Ollama is a native server, so `pyproject.toml` can never install them. The project-level record that can is pnpm's `package.json`: `pnpm add -D` writes the CLI as a dev dependency and links its binary under `node_modules/.bin`, so `pnpm install` restores the host's chosen CLIs.

Hand test on 2026-11-14 (pnpm 10.34.5): in an empty directory, `pnpm add -D @qwen-code/qwen-code@latest` created `package.json` (`devDependencies: {"@qwen-code/qwen-code": "^0.27.3"}`), `pnpm-lock.yaml`, and `node_modules/.bin/qwen`, which answered `--version` with `0.27.3`; pnpm printed an "Ignored build scripts" warning that is harmless. On the same machine `claude --version` prints `2.1.322 (Claude Code)`, `codex --version` prints `codex-cli 0.167.1`, and `qwen --version` prints `0.27.1`, each from a pnpm global shim; `gemini --version` prints `0.49.0` but Gemini has no adapter yet (`docs/roadmap.md` row 32, `gemini-provider`), and Ollama is not an npm package.

When this ticket is done:
- Each adapter in `ADAPTERS` carries its pnpm package as a class attribute `PACKAGE`, the one home for that name in engine code.
- `chupa install [PROVIDER...]` (`./dev.py install [PROVIDER...]` in this repo) installs each named CLI into the host project as a pnpm dev dependency, through the exec seam, and then reports it. With no names it reports every adapter: package, where its binary resolves (`project`, `system`, or `absent`), and version. It needs no `config.yaml`, takes no lock, and writes no journal event, so it works before a host has a config.
- A CLI installed in the project is used before one on `PATH`: `<checkout>/node_modules/.bin` heads the `PATH` of every provider call and of the preflight's `--version` children. Non-LLM children (checks, git, notifications) are unchanged.
- The preflight's stale-CLI notice and probe-failure road name `chupa install <provider>` instead of `pnpm add -g`.
- Gemini joins the registry when `gemini-provider` adds its adapter with `PACKAGE = "@google/gemini-cli"`; this ticket records that in the Gemini plan. Ollama stays a third-party install: `chupa install qwen` installs Qwen Code only and names `chupa/docs/host-qwen.md` for Ollama.

## Scope in / Scope out
In:
- `chupa/providers.py`:
  - `CliAdapter` gains the class attribute annotation `PACKAGE: str`. `ClaudeAdapter.PACKAGE = "@anthropic-ai/claude-code"`, `CodexAdapter.PACKAGE = "@openai/codex"`, `QwenAdapter.PACKAGE = "@qwen-code/qwen-code"`.
  - New module function `tool_env(env: Mapping[str, str], checkout: Path) -> dict[str, str]`: a copy of `env` whose `PATH` is `str(checkout / "node_modules" / ".bin")`, then `os.pathsep`, then the original `PATH`; when `env` has no `PATH` the value is the bin directory alone. No existence check: a missing directory on `PATH` is harmless and keeps the function pure.
  - `CliAdapter.call_env()` returns `tool_env(child_env(self._env, self._config, self.provider), self._cwd)`. `QwenAdapter.call_env` keeps building on `super().call_env()` and does not change.
  - New module function `installed_version(out: str, err: str) -> str | None`: the first `\d+\.\d+\.\d+` match in `out + err`, else `None`. `ProviderLLM.preflight` uses it in place of its inline `re.search`.
  - New constant `INSTALL_TIMEOUT_S = 600.0` beside `PREFLIGHT_TIMEOUT_S`.
  - New `@dataclass(frozen=True) class CliStatus` with fields `name: str`, `package: str`, `binary: str`, `where: Literal["project", "system", "absent"]`, `version: str | None`, and `async def cli_status(name: str, *, exec_: ProcessExec, env: Mapping[str, str], cwd: Path) -> CliStatus`: it runs `[ADAPTERS[name].binary, "--version"]` with `cwd=cwd`, `env=tool_env(env, cwd)`, `timeout=PREFLIGHT_TIMEOUT_S`. `ExecutableNotFound` gives `where="absent"`, `version=None`. Otherwise `where` is `"project"` when `(cwd / "node_modules" / ".bin" / binary).is_file()` and `"system"` when not, and `version` is `installed_version(out, err)`.
  - `ProviderLLM.preflight`: the `--version` child runs with `env=tool_env(child_env(self._env, self._config), self._cwd)`, so it still carries no provider key and resolves a project install first; the `pnpm view` child keeps `child_env(self._env, self._config)` unchanged. The stale notice ends `-- run: chupa install {provider name}` and the probe-failure road ends `-- run: chupa install {provider name}, or route a model this login serves in config.yaml`. Nothing else in preflight changes.
- `chupa/__main__.py`: a new verb `install`, parser `sub.add_parser("install", help="install provider CLIs into the host project as pnpm dev dependencies").add_argument("providers", nargs="*")`, handled with the verbs that run before `load_config` (next to `docs` and `new`); it never loads config, never constructs `Lockfile` or `Journal`. For each name:
  - a name not in `ADAPTERS` raises `runner.Refusal(f"unknown provider {name!r}", f"name one of {', '.join(sorted(ADAPTERS))}")` before any process runs;
  - it runs `["pnpm", "add", "-D", f"{ADAPTERS[name].PACKAGE}@latest"]` through `SubprocessExec` with `cwd=repo`, `env=tool_env(env, repo)`, `timeout=INSTALL_TIMEOUT_S`. `ExecutableNotFound` becomes `runner.Refusal("pnpm is not on PATH", "install pnpm (https://pnpm.io/installation), then rerun chupa install")`; a nonzero exit becomes `runner.Refusal(f"pnpm add {package}@latest failed (rc {rc}): {last non-blank stderr line}", "fix the pnpm error, then rerun chupa install")`;
  - it then prints the row for that name. With no names it prints one row per `ADAPTERS` entry in `ADAPTERS` order and installs nothing.

  A row is `f"{s.name}: {s.where}{' ' + s.version if s.version else ''}, package {s.package}"`, plus the suffix ` -- run: chupa install {s.name}` when `where == "absent"`. A `qwen` row is followed by the line `ollama: not installed by chupa; follow chupa/docs/host-qwen.md`. Exit 0 after the rows; refusals exit 2 through the existing handler.
- `dev.py`: an `install` subcommand taking optional provider names, forwarding to `chupa install [PROVIDER...]`; docstring line `./dev.py install [PROVIDER...]  install provider CLIs into this repo as pnpm dev dependencies`.
- `.gitignore`: add the line `node_modules/`.
- Tests:
  - `tests/unit/test_install_verb.py` (new), built the way `tests/unit/test_probe_verb.py` fakes `cli.SubprocessExec`, with `cli.load_config`, `cli.Lockfile`, and `cli.Journal` patched to raise `AssertionError` as `tests/unit/test_docs_verb.py::test_docs_without_config_or_lock` does; the project-install case patches `Path.is_file` the way that file patches `Path.exists`. Tests of `tool_env`, `installed_version`, `cli_status`, and `chupa install` as listed in the acceptance criteria.
  - `tests/unit/test_qwen_adapter.py::test_qwen_argv_and_env`: the one expectation that changes is the last assertion, `a.call_env()["PATH"] == "/repo/node_modules/.bin:/bin"`.
  - `tests/integration/test_providers.py`: `test_llm_call_env_restores_only_the_serving_providers_key` expects `PATH` to be `f"{tmp_path / 'checkout' / 'node_modules' / '.bin'}:/usr/bin"` in both call envs, keys unchanged. `test_preflight_version_children_carry_no_provider_key` distinguishes `--version` children from `pnpm view` children (for example by recording `argv[0]` beside the env in `PreflightExec`): the two `--version` envs carry `PATH == f"{tmp_path / 'checkout' / 'node_modules' / '.bin'}:{ENV['PATH']}"`, the two `pnpm` envs carry `ENV["PATH"]`, and no env carries a key. `test_preflight_reports_a_stale_cli_without_refusing_the_run` expects `-- run: chupa install codex` in the notice and no `pnpm add`.
  - `tests/integration/test_daemon_composition.py`: the assertion `"pnpm add -g test-cli@latest" in message` becomes `"-- run: chupa install " in message`.
  - `tests/integration/test_closed_sets.py::test_providers_closed_sets_and_constants`: add the `PACKAGE` map and `INSTALL_TIMEOUT_S` pins in criterion 1.
  - `tests/integration/test_dev.py`: a forwarding test for `./dev.py install qwen`, shaped like `test_suggest_forwards_summary`.
- Docs:
  - `chupa/docs/host-running.md`: the verb table gains the row `| `install` | Yes | Install named provider CLIs into the host project as pnpm dev dependencies; with no names, report each adapter's package, location, and version. |`.
  - `chupa/docs/host-contract.md` `## Install`: a new paragraph after the existing one: `uv run chupa install claude codex` installs the CLIs you route as pnpm dev dependencies of the host (`package.json`, `pnpm-lock.yaml`, `node_modules/.bin`); commit the first two and gitignore `node_modules/`. A CLI already on `PATH` works without it; a project install is used first. `uv run chupa install` with no names reports each adapter's package, location, and version. Nothing else in the file changes.
  - `docs/how-chupa-works.md`: §2.1 gains the row `| `install [PROVIDER...]` | no | Installs named provider CLIs into the host project as pnpm dev dependencies, or with no names reports each adapter's package, location, and version. |` after the `probe` row; §2.2 gains `| `install [PROVIDER...]` | `chupa install` with the supplied providers |` after the `probe` row; §8.1 gains one bullet after the Preflight bullet: a CLI installed in the host project (`chupa install <provider>`, a pnpm dev dependency under `node_modules/.bin`) is used before one on `PATH`, because the checkout's `node_modules/.bin` heads every provider child's `PATH`; the preflight's update road is `chupa install <provider>`. No heading changes.
  - `README.md`: in `## Install`, after the `uv sync` block, one sentence: install the provider CLIs you route with `uv run chupa install claude codex` (pnpm dev dependencies under `node_modules/.bin`; a CLI already on `PATH` works without it). The `## Commands` block gains `uv run chupa install  # install provider CLIs into the host` under `# Setup`. No `./dev.py` mention before `## Developing chupa`.
  - `chupa/docs/host-qwen.md` `## Install Qwen Code`: the step becomes: run `chupa install qwen` (`./dev.py install qwen` in the chupa repo) to install it into the host project, or `pnpm add -g @qwen-code/qwen-code@latest` for a system-wide install.
  - `docs/gemini-graphics-refactor-plan.md`, Part A target design, the `GeminiAdapter(CliAdapter)` bullet: add that it sets `PACKAGE = "@google/gemini-cli"`, which `chupa install gemini` and the closed-set pin require.

Out:
- Installing Ollama or any non-npm binary; `chupa install` runs no shell and no install script.
- `chupa/config.py`: `Provider.package` stays required and stays the preflight's `pnpm view` source.
- Writing `.gitignore` or `package.json` in a host beyond what pnpm itself writes.
- A `gemini` adapter: `chupa install gemini` is refused as unknown until `gemini-provider` lands.
- The `pnpm view` latest-release check, the probe content, `live_call`, and `routed_conduct_paths`.
- Running `chupa install` in this repo; the operator does that after merge.

## Scope fence
- chupa/providers.py
- chupa/__main__.py
- dev.py
- .gitignore
- tests/unit/test_install_verb.py
- tests/unit/test_qwen_adapter.py
- tests/integration/test_providers.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_closed_sets.py
- tests/integration/test_dev.py
- chupa/docs/host-running.md
- chupa/docs/host-contract.md
- chupa/docs/host-qwen.md
- docs/how-chupa-works.md
- docs/gemini-graphics-refactor-plan.md
- README.md

## Acceptance criteria
1. `tests/integration/test_closed_sets.py::test_providers_closed_sets_and_constants` asserts `{k: a.PACKAGE for k, a in providers.ADAPTERS.items()} == {"claude": "@anthropic-ai/claude-code", "codex": "@openai/codex", "qwen": "@qwen-code/qwen-code"}` and `providers.INSTALL_TIMEOUT_S == 600.0`. Ruled out: an adapter without `PACKAGE` (the comprehension raises `AttributeError`).
2. `tests/unit/test_install_verb.py` asserts `tool_env({"PATH": "/bin", "X": "1"}, Path("/repo")) == {"PATH": "/repo/node_modules/.bin:/bin", "X": "1"}` and `tool_env({}, Path("/repo"))["PATH"] == "/repo/node_modules/.bin"`. Ruled out: `PATH` unchanged, and the bin directory appended after `/bin`.
3. The same file asserts `installed_version("codex-cli 0.167.1\n", "") == "0.167.1"`, `installed_version("", "2.1.322 (Claude Code)") == "2.1.322"`, and `installed_version("", "") is None`. Ruled out: `""` in place of `None`.
4. The same file asserts, with a fake exec answering `["claude", "--version"]` with `(0, "2.1.322 (Claude Code)\n", "")`: `cli_status("claude", exec_=..., env={"PATH": "/bin"}, cwd=Path("/repo"))` equals `CliStatus("claude", "@anthropic-ai/claude-code", "claude", "system", "2.1.322")` and the child's env `PATH` is `"/repo/node_modules/.bin:/bin"`; with `Path.is_file` patched to return `True` for `Path("/repo/node_modules/.bin/claude")`, `where == "project"`; with the exec raising `ExecutableNotFound("claude")`, the result is `CliStatus("claude", "@anthropic-ai/claude-code", "claude", "absent", None)`. Ruled out: `"absent"` for a binary that answered, `"system"` while the project file exists, and a raised `ExecutableNotFound`.
5. The same file drives `cli.main` with `cli.load_config`, `cli.Lockfile`, and `cli.Journal` patched to raise `AssertionError`:
   - `main(["install"], cwd=Path("/repo"), env={"PATH": "/bin"})` exits 0, runs no `pnpm` call, and prints exactly the rows `claude: system 2.1.322, package @anthropic-ai/claude-code`, `codex: system 0.167.1, package @openai/codex`, `qwen: absent, package @qwen-code/qwen-code -- run: chupa install qwen`, `ollama: not installed by chupa; follow chupa/docs/host-qwen.md`, in that order, when the fake exec answers claude and codex `--version` and raises `ExecutableNotFound` for `qwen`;
   - `main(["install", "codex"], ...)` exits 0 and runs exactly one `pnpm` call, `["pnpm", "add", "-D", "@openai/codex@latest"]` with `cwd=Path("/repo")`, `timeout=600.0`, and an env whose `PATH` starts with `/repo/node_modules/.bin`, then prints the codex row;
   - `main(["install", "gemini"], ...)` exits 2, runs no process, and stderr names `claude, codex, qwen`;
   - with the fake exec raising `ExecutableNotFound("pnpm")` for the `pnpm` call, `main(["install", "codex"], ...)` exits 2 and stderr contains `pnpm.io/installation`;
   - with the `pnpm` call answering `(1, "", "ERR_PNPM_FETCH_404 not found\n")`, `main(["install", "codex"], ...)` exits 2 and stderr contains `ERR_PNPM_FETCH_404`.
   Ruled out: exit 0 on a failed install, a `pnpm` call for an unknown name, and any `Lockfile`, `Journal`, or `load_config` use.
6. `tests/unit/test_qwen_adapter.py::test_qwen_argv_and_env` asserts `a.call_env()["PATH"] == "/repo/node_modules/.bin:/bin"`; `"/bin"` alone is the ruled-out value.
7. `tests/integration/test_providers.py`: `test_llm_call_env_restores_only_the_serving_providers_key` asserts both call envs carry `PATH == f"{tmp_path / 'checkout' / 'node_modules' / '.bin'}:/usr/bin"`, `HOME`, and only the serving provider's key; `test_preflight_version_children_carry_no_provider_key` asserts the two `--version` children carry `PATH == f"{tmp_path / 'checkout' / 'node_modules' / '.bin'}:{ENV['PATH']}"`, the two `pnpm view` children carry `ENV["PATH"]`, and none of the four carries `CLAUDE_KEY` or `CODEX_KEY`; `test_preflight_reports_a_stale_cli_without_refusing_the_run` asserts `-- run: chupa install codex` is in the notice and `pnpm add` is not.
8. `tests/integration/test_daemon_composition.py` asserts `"-- run: chupa install " in message` where it asserted `"pnpm add -g test-cli@latest" in message`.
9. `tests/integration/test_dev.py` has a test asserting `./dev.py install qwen` calls `run` once with `["uv", "run", "python", "-m", "chupa", "install", "qwen"]`.
10. `./dev.py test tests/unit/test_host_running.py tests/unit/test_readme.py` exits 0: the `install` row is in the run guide's verb table and README's `uv run chupa install` names a parser verb.
11. The first `uv run python -c` command in `## Verification` exits 0: `chupa/providers.py` no longer contains `pnpm add -g`; `chupa install` appears in `chupa/docs/host-contract.md`, `chupa/docs/host-qwen.md`, `chupa/docs/host-running.md`, `docs/how-chupa-works.md`, and `README.md`; `PACKAGE` appears in `docs/gemini-graphics-refactor-plan.md`; `.gitignore` contains `node_modules/`.
12. `./dev.py test` exits 0.

## Verification
```
uv run python -c "import pathlib; assert 'pnpm add -g' not in pathlib.Path('chupa/providers.py').read_text(); assert all('chupa install' in pathlib.Path(f).read_text() for f in ('chupa/docs/host-contract.md', 'chupa/docs/host-qwen.md', 'chupa/docs/host-running.md', 'docs/how-chupa-works.md', 'README.md')); assert 'PACKAGE' in pathlib.Path('docs/gemini-graphics-refactor-plan.md').read_text(); assert 'node_modules/' in pathlib.Path('.gitignore').read_text()"
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- `chupa install` runs a shell, an install script, or `pnpm add -g`;
- `chupa install` loads `config.yaml`, takes the writer lock, or writes a journal event;
- a `--version` or `pnpm view` child receives a provider key, or a non-LLM child's `PATH` changes;
- `Provider.package` becomes optional or is read from `PACKAGE`;
- `package.json` or `node_modules` is committed in this repo;
- a file outside the scope fence changes.

## Time budget
- expected: 75m
- stuck: 150m
