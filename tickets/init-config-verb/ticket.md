---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- provider-cli-install
- update-config-verb

## Context
- chupa/config.py::load_config
- chupa/config.py::_CandidatePath
- chupa/config.py::migrate_config
- chupa/config.py::Provider
- chupa/providers.py::CliAdapter
- chupa/providers.py::ClaudeAdapter
- chupa/providers.py::ADAPTERS
- chupa/providers.py::PLACEHOLDER
- chupa/__main__.py::_parser
- chupa/__main__.py::main
- chupa/seams.py::FileSystem
- chupa/seams.py::LocalFileSystem
- dev.py
- tests/unit/test_probe_verb.py
- tests/unit/test_docs_verb.py
- tests/integration/test_config.py::test_migrate_config_validates_before_write
- tests/integration/test_dev.py::test_suggest_forwards_summary
- chupa/docs/host-running.md
- chupa/docs/host-contract.md#Install
- chupa/docs/host-contract.md#Copyable configuration
- docs/how-chupa-works.md#2.1 Verbs
- docs/how-chupa-works.md#2.2
- docs/how-chupa-works.md#11. Config
- tickets/provider-cli-install/ticket.md
- tickets/update-config-verb/ticket.md

## On-demand
- README.md

## Goal / Why
A new host starts from the copyable example in `chupa/docs/host-contract.md` and hand-edits provider names, packages, and model names. The operator asked for a config generation command that offers a suggested configuration file from the providers available, whether already on the system or installed in the project.

`provider-cli-install` gives chupa `cli_status` (which CLIs resolve, from the project or the system) and each adapter's `PACKAGE`; `update-config-verb` gives it `list_models` (the model names each CLI serves). This ticket composes them: `chupa init-config` (`./dev.py init-config` in this repo) prints a suggested `config.yaml` built from the CLIs found and the models they serve, and `--write` publishes it to `config.yaml` only when no config exists. It needs no config, takes no lock, and writes no journal event. The suggestion is loaded through the real loader before it is printed, and every model that could not be determined is written as `OPERATOR-SETS-THIS`, which the engine already refuses at routing time until the operator edits it.

## Scope in / Scope out
In:
- `chupa/config.py`: new `def load_config_text(text: str, *, path: Path, cwd: Path) -> Config`: the `_CandidatePath` block of `migrate_config` (set `text` on a `_CandidatePath(path)` and call `load_config`), which `migrate_config` now calls in place of that block; its `ConfigError` rewording and everything else in `migrate_config` stay as they are.
- `chupa/providers.py`:
  - `CliAdapter` gains `TIER_LABELS: dict[str, str] | None = None`; `ClaudeAdapter.TIER_LABELS = {"low": "haiku", "medium": "sonnet", "high": "opus", "max": "fable"}`; `QwenAdapter.TIER_LABELS = None`, because `QwenAdapter` subclasses `ClaudeAdapter` and Claude's aliases do not apply to Ollama names. An adapter without `TIER_LABELS` suggests its first served name for every tier.
  - New pure function `suggest_config(statuses: Sequence[CliStatus], listings: Mapping[str, ModelListing]) -> str` rendering the text below for the statuses whose `where != "absent"`, in the given order; `listings` is keyed by provider name. It raises `ValueError("no provider CLI found")` when no status is present.
- `chupa/__main__.py`: a new verb `init-config`, `sub.add_parser("init-config", help="print a suggested config.yaml from the provider CLIs found").add_argument("--write", action="store_true")`, handled with the verbs that run before `load_config` (next to `docs`, `new`, and `install`), never constructing `Lockfile` or `Journal`. It runs `cli_status` for every `ADAPTERS` name in `ADAPTERS` order with `exec_=SubprocessExec()`, `env=env`, `cwd=repo` (no config exists yet, so chupa knows no secret names and passes the parent env), then `list_models` for each present adapter with the same arguments, then `text = suggest_config(...)`; `ValueError` becomes `runner.Refusal("no provider CLI found", f"run: chupa install {'|'.join(sorted(ADAPTERS))}")`. It validates with `load_config_text(text, path=repo / "config.yaml", cwd=repo)` (a `ConfigError` here is a chupa defect and exits 2 through the existing handler), prints `text` to stdout, and with `--write` calls `LocalFileSystem().publish(repo / "config.yaml", text.encode())`; `FileExistsError` becomes `runner.Refusal("config.yaml already exists", "remove it, or omit --write and merge the printed suggestion by hand")`. Exit 0.
- The rendered text, in this order:
  - the line `# Suggested by chupa init-config from the provider CLIs found; edit models, checks and routing, then run chupa doctor and chupa probe.`;
  - `schema_version: 1` and `state_dir: .chupa`;
  - `providers:` with one block per present status: `  - name: <name>`, `    kind: cli`, `    package: '<PACKAGE>'`, for an adapter with `uses_base_url` the line `    base_url: http://localhost:11434/v1  # chupa/docs/host-qwen.md`, then `    models_by_tier: {low: <m>, medium: <m>, high: <m>, max: <m>}` where `<m>` for a tier is `listing.models[TIER_LABELS[tier]]` for an adapter with `TIER_LABELS`, else the first value of `listing.models`, and `OPERATOR-SETS-THIS` when that label or value is missing; followed on the same line by `  # served: <space-joined served names>` when `models` is non-empty, and by one line `    # <problem>` per listing problem; then `    limits: {concurrency: 1}` for an adapter with `reports_cost`, else `    limits: {concurrency: 1, est_cost_per_call_usd: <0 for uses_base_url, else 0.25>}  # <binary> reports no cost: edit the estimate`;
  - `routing:` with, for each tier `low`, `medium`, `high`, `max` and each surface `implement`, `review` in that order, the row `  - {tier: <tier>, surface: <surface>, candidates: [{provider: <a>}, {provider: <b>}, ...]}` naming every present provider in status order;
  - `review: {}  # add your host's checks: chupa/docs/host-contract.md`, `merge: {}`, and `engine_plane_safety_inventory: [config.yaml]`.
- `dev.py`: an `init-config` subcommand with a `--write` flag forwarding to `chupa init-config [--write]`; docstring line `./dev.py init-config [--write]  print (or write) a suggested config.yaml from the provider CLIs found`.
- Tests:
  - `tests/unit/test_init_config_verb.py` (new): `suggest_config` over hand-built statuses and listings, and `chupa init-config` through `cli.main` with the fake exec of `tests/unit/test_update_config_verb.py`, `cli.Lockfile` and `cli.Journal` patched to raise `AssertionError`, `cli.load_config` patched to raise `AssertionError` (the verb must not read a config), `Path.is_file` patched as `tests/unit/test_docs_verb.py` patches `Path.exists`, and `cli.LocalFileSystem` patched to a `Mock` whose `publish` records its call or raises `FileExistsError`. The real `load_config_text` runs on the rendered text: it reads from `_CandidatePath`, not from disk.
  - `tests/integration/test_dev.py`: a forwarding test for `./dev.py init-config --write`, shaped like `test_suggest_forwards_summary`.
- Docs:
  - `chupa/docs/host-running.md`: the verb table gains `| `init-config` | Yes | Print a suggested `config.yaml` from the provider CLIs found and the models they serve; `--write` creates `config.yaml` when none exists. |`.
  - `chupa/docs/host-contract.md`: `## Install` gains one sentence after the `chupa install` paragraph: `uv run chupa init-config --write` then creates a `config.yaml` from the CLIs found and the models they serve, which `chupa doctor` and `chupa probe` check. `## Copyable configuration` gains one sentence at the end of its first paragraph: `chupa init-config` prints the same shape filled from the CLIs it finds. Nothing else changes.
  - `docs/how-chupa-works.md`: §2.1 gains `| `init-config [--write]` | no | Prints a suggested `config.yaml` built from the provider CLIs found (project or system) and the model names they serve, validated with the real loader; `--write` publishes it when no `config.yaml` exists. Undetermined models are written as `OPERATOR-SETS-THIS`. |` after the `update-config` row; §2.2 gains `| `init-config [--write]` | `chupa init-config` with the supplied flag |` after the `update-config` row; §11 gains one sentence before the table: `chupa init-config` prints a suggestion built from the installed CLIs. No heading changes.
  - `README.md`: the `## Install` sentence "Your host also needs `config.yaml`; start with the copyable configuration" gains ", or create one with `uv run chupa init-config --write` from the CLIs you installed". The `## Commands` block gains `uv run chupa init-config  # print a suggested config.yaml` under `# Setup`.

Out:
- Any change to `load_config`'s rules, `migrate_config`'s behavior, or the `host-example` block in the contract.
- Reading an existing `config.yaml` or merging into it; overwriting a config.
- Host checks, `merge.strategies`, `notify`, or any field beyond those rendered above.
- Gemini and Ollama detection beyond what `cli_status` and `list_models` already report.

## Scope fence
- chupa/config.py
- chupa/providers.py
- chupa/__main__.py
- dev.py
- tests/unit/test_init_config_verb.py
- tests/integration/test_dev.py
- chupa/docs/host-running.md
- chupa/docs/host-contract.md
- docs/how-chupa-works.md
- README.md

## Acceptance criteria
1. `tests/unit/test_init_config_verb.py` asserts `suggest_config` over statuses `claude` (`project`), `codex` (`system`), `qwen` (`absent`) and listings `claude: {haiku: claude-haiku-5-5, sonnet: claude-sonnet-5-5, opus: claude-opus-5-5}` with problem `fable: error_during_execution`, `codex: {gpt-6.1-sol: gpt-6.1-sol, gpt-6-astra: gpt-6-astra}`: the text contains `    models_by_tier: {low: claude-haiku-5-5, medium: claude-sonnet-5-5, high: claude-opus-5-5, max: OPERATOR-SETS-THIS}`, a line `    # fable: error_during_execution`, `    package: '@openai/codex'`, `    models_by_tier: {low: gpt-6.1-sol, medium: gpt-6.1-sol, high: gpt-6.1-sol, max: gpt-6.1-sol}  # served: gpt-6.1-sol gpt-6-astra`, `est_cost_per_call_usd: 0.25`, eight routing rows each ending `candidates: [{provider: claude}, {provider: codex}]}`, and no `name: qwen`. Ruled out: a `qwen` block for an absent CLI, and `gpt-6-astra` chosen over the first served name.
2. The same file asserts `suggest_config` with only a `qwen` status (`system`) and an empty listing with one problem renders `base_url: http://localhost:11434/v1`, `models_by_tier: {low: OPERATOR-SETS-THIS, medium: OPERATOR-SETS-THIS, high: OPERATOR-SETS-THIS, max: OPERATOR-SETS-THIS}`, `est_cost_per_call_usd: 0`, and routing rows with `candidates: [{provider: qwen}]`; with the same status and the listing `{qwen3-coder:30b: qwen3-coder:30b, llama3.2:latest: llama3.2:latest}` it renders `models_by_tier: {low: qwen3-coder:30b, medium: qwen3-coder:30b, high: qwen3-coder:30b, max: qwen3-coder:30b}  # served: qwen3-coder:30b llama3.2:latest` (ruled out: four `OPERATOR-SETS-THIS` values from Claude's inherited tier labels); and `suggest_config([], {})` raises `ValueError`.
3. The same file asserts that `load_config_text(text, path=Path("/repo/config.yaml"), cwd=Path("/repo"))` loads the text of criteria 1 and 2 without `ConfigError`, with `len(config.routing) == 8` and `config.providers[0].package == "@anthropic-ai/claude-code"` for criterion 1. Ruled out: a rendering the loader refuses.
4. The same file drives `cli.main(["init-config"], cwd=Path("/repo"), env={"PATH": "/bin"})` with the patches named in Scope in: with the fake exec answering claude and codex `--version`, raising `ExecutableNotFound` for `qwen --version`, and answering the alias probes and `codex debug models` as in `tests/unit/test_update_config_verb.py`: exit 0, stdout equals the rendered text, `publish` not called, and no `pnpm` call; `main(["init-config", "--write"], ...)` calls `publish` once with `(Path("/repo/config.yaml"), <stdout text>.encode())`; with `publish` raising `FileExistsError`, exit 2 and stderr contains `config.yaml already exists`; with the exec raising `ExecutableNotFound` for all three `--version` calls, exit 2 and stderr contains `run: chupa install claude|codex|qwen`. Ruled out: `load_config` called, a config written without `--write`, and an existing config overwritten.
5. `tests/integration/test_config.py::test_migrate_config_validates_before_write` and `test_migrate_config_zero_to_one` pass unchanged with `migrate_config` calling `load_config_text`.
6. `tests/integration/test_dev.py` has a test asserting `./dev.py init-config --write` calls `run` once with `["uv", "run", "python", "-m", "chupa", "init-config", "--write"]`.
7. `./dev.py test tests/unit/test_host_running.py tests/unit/test_readme.py tests/integration/test_host_contract.py` exits 0: the `init-config` row is in the run guide's verb table, README's `uv run chupa init-config` names a parser verb, and the contract's example blocks still load.
8. The first `uv run python -c` command in `## Verification` exits 0: `init-config` appears in `chupa/docs/host-running.md`, `chupa/docs/host-contract.md`, `docs/how-chupa-works.md`, and `README.md`.
9. `./dev.py test` exits 0.

## Verification
```
uv run python -c "import pathlib; assert all('init-config' in pathlib.Path(f).read_text() for f in ('chupa/docs/host-running.md', 'chupa/docs/host-contract.md', 'docs/how-chupa-works.md', 'README.md'))"
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- `chupa init-config` reads `config.yaml`, overwrites an existing one, writes without `--write`, takes the writer lock, or writes a journal event;
- the printed text is not loaded by the real loader before printing;
- an undetermined model is written as anything other than `OPERATOR-SETS-THIS`;
- `migrate_config`'s observable behavior changes;
- a file outside the scope fence changes.

## Time budget
- expected: 60m
- stuck: 120m
