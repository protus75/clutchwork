---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- provider-cli-install

## Context
- chupa/providers.py::CliAdapter
- chupa/providers.py::ClaudeAdapter
- chupa/providers.py::CodexAdapter
- chupa/providers.py::QwenAdapter
- chupa/providers.py::ADAPTERS
- chupa/providers.py::_events
- chupa/providers.py::PLACEHOLDER
- chupa/providers.py::PROBE_PROMPT
- chupa/providers.py::child_env
- chupa/config.py::Provider
- chupa/config.py::ModelsByTier
- chupa/config.py::Route
- chupa/config.py::Candidate
- chupa/__main__.py::_parser
- chupa/__main__.py::main
- chupa/seams.py::ExecutableNotFound
- dev.py
- tests/unit/test_probe_verb.py
- tests/integration/test_closed_sets.py::test_providers_closed_sets_and_constants
- tests/integration/test_dev.py::test_suggest_forwards_summary
- chupa/docs/host-running.md
- docs/how-chupa-works.md#2.1 Verbs
- docs/how-chupa-works.md#2.2
- docs/how-chupa-works.md#8.1 Providers

## On-demand
- README.md

## Goal / Why
Model names in `config.yaml` (`models_by_tier` and routing candidates' `model`) go stale when a provider ships a new series or version. Today the operator learns this only when a preflight probe fails, and nothing tells them the current names. The operator asked for a config update command that offers updated model names for the available providers.

Each CLI can say what it serves, and a hand test on 2026-11-14 established how:
- Claude Code 2.1.322: `claude --help` says `--model` takes "an alias for the latest model (e.g. 'fable', 'opus', or 'sonnet') or a model's full name". With `claude -p "Reply with the single word ok." --output-format stream-json --verbose --model sonnet --tools Read --permission-mode dontAsk`, the first event is `{"type": "system", "subtype": "init", ..., "model": "claude-sonnet-5-5"}` and the terminal `result` event (`subtype: success`, `total_cost_usd: 0.0401`) carries `modelUsage` keyed by the same name; `--model haiku` resolved to `claude-haiku-5-5` for `$0.0023`. The alias table lives in the CLI: an unknown name (`claude-bogus-9`) is echoed unchanged in `init`, so a resolution counts only when the `result` event reports success. A new Claude series therefore reaches chupa through a CLI update (`chupa install claude`) followed by this verb. Each alias resolution is one small model call.
- codex-cli 0.167.1: `codex debug models` prints, in 0.4 s and without a model call, a JSON object `{"models": [...]}`; every entry has `slug`, `display_name`, `visibility` (`list` or `hide`), and an integer `priority` (1 first). That day the listed slugs in priority order were `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6.1-terra`, `gpt-6-sol`, `gpt-6-luna`, `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`; `gpt-reserve` and `codex-auto-review` were hidden.
- Ollama: `ollama list` prints a table with the header `NAME ID SIZE MODIFIED` and one model per line, name first (documented format; Ollama is not installed on the authoring machine, so this case is hand-built). On a WSL host whose Ollama runs on Windows (`chupa/docs/host-qwen.md` variant b) the `ollama` binary is not on the WSL `PATH`, so the listing is unavailable there and the verb must say so with a road.

When this ticket is done, `chupa update-config` (`./dev.py update-config` in this repo) prints, for each declared provider, the model names its CLI serves now, and beside each configured model name whether it is current, which newer name replaces it, or that it is not served. It writes nothing: `config.yaml` is operator-owned and the operator applies the suggestion. It takes no lock and writes no journal event. It exits 0 when every configured name is current, 1 when it printed a suggestion, and 2 on a refusal.

## Scope in / Scope out
In:
- `chupa/providers.py`:
  - New `@dataclass(frozen=True) class ModelListing` with `models: dict[str, str]` and `problems: tuple[str, ...]`. `models` maps a label to a served model name: for `claude` the label is an alias and the value its resolved name; for `codex` and `qwen` the label equals the name. A label whose value differs from it is a family alias.
  - New constant `CLAUDE_ALIASES = ("haiku", "sonnet", "opus", "fable")`.
  - `CliAdapter` gains `@classmethod async def list_models(cls, *, exec_: ProcessExec, env: Mapping[str, str], cwd: Path) -> ModelListing`, raising `NotImplementedError` in the base. Every implementation runs its children with `cwd=cwd`, `env=tool_env(env, cwd)` (from `provider-cli-install`), and `timeout=PREFLIGHT_TIMEOUT_S`.
  - `ClaudeAdapter.list_models`: for each alias in `CLAUDE_ALIASES`, concurrently (`asyncio.gather`, as preflight runs its probes), run `[cls.binary, "-p", PROBE_PROMPT, "--output-format", "stream-json", "--verbose", "--model", alias, "--tools", "Read", "--permission-mode", "dontAsk"]`. The alias resolves when the stream (`_events(out)`) has a terminal `result` event with `subtype == "success"` and no `is_error`, and a `system` event with `subtype == "init"` and a non-empty string `model`; then `models[alias] = model`, in `CLAUDE_ALIASES` order. Otherwise `problems` gets `f"{alias}: {reason}"`, where reason is the `result` event's `subtype` and `result` text, or `no terminal result event (rc {rc})`. `ExecutableNotFound` propagates.
  - `CodexAdapter.list_models`: run `[cls.binary, "debug", "models"]`; parse stdout as JSON; `models` is `{slug: slug}` for the entries of `models` whose `visibility == "list"`, in ascending `priority`. A nonzero exit or unparsable stdout gives `ModelListing({}, (f"codex debug models: {reason}",))` with the last non-blank stderr line or the JSON error as reason. `ExecutableNotFound` propagates.
  - `QwenAdapter.list_models`: run `["ollama", "list"]`; `models` is `{name: name}` for the first whitespace-delimited field of every non-blank stdout line after the first (header) line, in order. `ExecutableNotFound` gives `ModelListing({}, ("ollama is not on PATH; run `ollama list` where Ollama runs (chupa/docs/host-qwen.md) and set models_by_tier by hand",))`; a nonzero exit gives a problem with the last non-blank stderr line.
- `chupa/__main__.py`: a new verb `update-config`, `sub.add_parser("update-config", help="list the model names each declared provider serves and compare them with config.yaml")`, handled after `config = load_config(...)`, never constructing `Lockfile` or `Journal`. For each provider in `config.providers`, in config order:
  - a name not in `ADAPTERS` prints `f"{name}: no shipped cli adapter; name one of {', '.join(sorted(ADAPTERS))}"` and counts as a suggestion;
  - otherwise it awaits `ADAPTERS[name].list_models(exec_=SubprocessExec(), env=child_env(env, config, provider), cwd=repo)`; `ExecutableNotFound` becomes `runner.Refusal(str(exc), f"run: chupa install {name}")`;
  - it prints `name`, then `  serves: ` followed by the space-joined entries, each `f"{label}={model}"` when the label differs from the model and the model alone otherwise (or `  serves: nothing listed` when `models` is empty), then one `  problem: {text}` line per problem;
  - then one line per configured name, for `models_by_tier.{tier}` over `low`, `medium`, `high`, `max` and for `routing[{i}].candidates[{j}].model` over routing candidates naming this provider with an explicit `model`, in that order. With `N` the configured name: `  {where}: {N} current` when `N` is in `models.values()`; else `  {where}: {N} -> {models[L]} (latest {L})` when a family alias `L` (a label differing from its value) is a substring of `N`; else `  {where}: {N} is the placeholder; pick a served name` when `N == PLACEHOLDER`; else `  {where}: {N} not served; pick a served name`.

  It exits 0 when every configured-name line says `current` and every provider has an adapter, and 1 otherwise. `problem:` lines alone do not change the exit code.
- `dev.py`: an `update-config` subcommand with no arguments forwarding to `chupa update-config`; docstring line `./dev.py update-config    list the model names each provider serves and compare them with config.yaml`.
- Tests:
  - `tests/unit/test_update_config_verb.py` (new), with a fake exec in the shape of `tests/unit/test_probe_verb.py` that answers by `argv[0]` and the value after `--model`: `list_models` for all three adapters and `chupa update-config` through `cli.main`, as the acceptance criteria list.
  - `tests/integration/test_closed_sets.py::test_providers_closed_sets_and_constants`: add `providers.CLAUDE_ALIASES == ("haiku", "sonnet", "opus", "fable")`.
  - `tests/integration/test_dev.py`: a forwarding test for `./dev.py update-config`, shaped like `test_suggest_forwards_summary`.
- Docs:
  - `chupa/docs/host-running.md`: the verb table gains `| `update-config` | Yes | List the model names each declared provider serves and say which configured names are current, replaced, or not served; writes nothing. |`.
  - `docs/how-chupa-works.md`: §2.1 gains `| `update-config` | no | Lists the model names each declared provider's CLI serves and compares them with `models_by_tier` and routing candidates; exit 0 when every name is current, 1 when a suggestion was printed. Writes nothing. |` after the `install` row; §2.2 gains `| `update-config` | `chupa update-config` |` after the `install` row; §8.1 gains a paragraph `**Model names.**` saying where each adapter's served names come from: `claude` resolves the aliases `haiku`, `sonnet`, `opus`, `fable` by one small probe call each and reads the resolved name from the stream's `init` event; `codex` reads `codex debug models` (visible entries in priority order, no model call); `qwen` reads `ollama list` where `ollama` is on `PATH`. `chupa update-config` prints them beside the configured names. No heading changes.
  - `README.md` `## Commands` gains `uv run chupa update-config  # list current model names per provider` under `# Setup`.

Out:
- Writing `config.yaml` (no `--write`); `migrate-config`; `init-config` (its own ticket).
- Listing Ollama models over HTTP; Gemini; any change to `probe`, preflight, `parse`, or `argv`.
- Judging which served name is "better" beyond the alias family rule; the operator picks.

## Scope fence
- chupa/providers.py
- chupa/__main__.py
- dev.py
- tests/unit/test_update_config_verb.py
- tests/integration/test_closed_sets.py
- tests/integration/test_dev.py
- chupa/docs/host-running.md
- docs/how-chupa-works.md
- README.md

## Acceptance criteria
1. `tests/integration/test_closed_sets.py::test_providers_closed_sets_and_constants` asserts `providers.CLAUDE_ALIASES == ("haiku", "sonnet", "opus", "fable")`.
2. `tests/unit/test_update_config_verb.py` asserts `ClaudeAdapter.list_models` with a fake exec that answers each alias probe with a `system`/`init` event carrying `model` (`haiku` -> `claude-haiku-5-5`, `sonnet` -> `claude-sonnet-5-5`, `opus` -> `claude-opus-5-5`) and a `result` success event, and answers `fable` with an init event `model: claude-fable-5-1` and a `result` event `subtype: error_during_execution`: returns `models == {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}` and one problem starting `fable: `; each probe argv equals `["claude", "-p", PROBE_PROMPT, "--output-format", "stream-json", "--verbose", "--model", <alias>, "--tools", "Read", "--permission-mode", "dontAsk"]` and its env `PATH` starts with `<cwd>/node_modules/.bin`. Ruled out: `fable` mapped from its `init` event despite the failed result, and a prompt on stdin.
3. The same file asserts `CodexAdapter.list_models` with `["codex", "debug", "models"]` answered by the JSON `{"models": [{"slug": "gpt-6-astra", "visibility": "list", "priority": 2}, {"slug": "gpt-reserve", "visibility": "hide", "priority": 5}, {"slug": "gpt-6.1-sol", "visibility": "list", "priority": 1}]}` returns `models == {"gpt-6.1-sol": "gpt-6.1-sol", "gpt-6-astra": "gpt-6-astra"}` in that order and no problems; answered by `(1, "", "error: not logged in\n")` returns empty `models` and one problem containing `not logged in`; answered by `(0, "not json", "")` returns one problem. Ruled out: the hidden slug listed, and file order kept over priority order.
4. The same file asserts `QwenAdapter.list_models` with `["ollama", "list"]` answered by `"NAME    ID    SIZE    MODIFIED\nqwen3-coder:30b    abc    18 GB    2 days ago\nllama3.2:latest    def    2 GB    1 day ago\n"` returns `models == {"qwen3-coder:30b": "qwen3-coder:30b", "llama3.2:latest": "llama3.2:latest"}`, and with the exec raising `ExecutableNotFound("ollama")` returns empty `models` and one problem containing `host-qwen.md`, not a raised exception. Ruled out: `NAME` listed as a model.
5. The same file drives `cli.main(["update-config"], cwd=Path("/repo"), env={"PATH": "/bin"})` with `cli.load_config` patched to return a config (as `tests/unit/test_probe_verb.py` does) and `cli.Lockfile` and `cli.Journal` patched to raise `AssertionError`:
   - config providers `claude` with `models_by_tier` `{low: claude-haiku-5-5, medium: claude-sonnet-5-5, high: claude-opus-5-4, max: claude-opus-5-4}` and `codex` with all tiers `gpt-6-astra`, routing `[{tier: medium, surface: review, candidates: [{provider: claude, model: claude-opus-5-4}]}]`, with the fake exec of criteria 2 and 3: exit 1, and stdout contains the lines `  serves: haiku=claude-haiku-5-5 sonnet=claude-sonnet-5-5 opus=claude-opus-5-5`, `  problem: fable: `, `  models_by_tier.low: claude-haiku-5-5 current`, `  models_by_tier.high: claude-opus-5-4 -> claude-opus-5-5 (latest opus)`, `  routing[0].candidates[0].model: claude-opus-5-4 -> claude-opus-5-5 (latest opus)`, `  serves: gpt-6.1-sol gpt-6-astra`, and `  models_by_tier.low: gpt-6-astra current`;
   - the same with `claude` tiers all `claude-opus-5-5` and no routing candidate model: exit 0;
   - `codex` tiers `gpt-4.1` prints `  models_by_tier.low: gpt-4.1 not served; pick a served name` and exits 1; a tier set to `OPERATOR-SETS-THIS` prints `is the placeholder; pick a served name` and exits 1;
   - a provider named `gemini` prints `gemini: no shipped cli adapter; name one of claude, codex, qwen` and exits 1;
   - the exec raising `ExecutableNotFound("claude")` for the claude probes exits 2 with `run: chupa install claude` on stderr.
   Ruled out: exit 0 when a name was replaced or not served, and any `Lockfile` or `Journal` use.
6. `tests/integration/test_dev.py` has a test asserting `./dev.py update-config` calls `run` once with `["uv", "run", "python", "-m", "chupa", "update-config"]`.
7. `./dev.py test tests/unit/test_host_running.py tests/unit/test_readme.py` exits 0: the `update-config` row is in the run guide's verb table and README's `uv run chupa update-config` names a parser verb.
8. The first `uv run python -c` command in `## Verification` exits 0: `docs/how-chupa-works.md` names `update-config`, `codex debug models`, and `ollama list`.
9. `./dev.py test` exits 0.

## Verification
```
uv run python -c "import pathlib; h = pathlib.Path('docs/how-chupa-works.md').read_text(); assert all(s in h for s in ('update-config', 'codex debug models', 'ollama list')); assert 'update-config' in pathlib.Path('chupa/docs/host-running.md').read_text(); assert 'uv run chupa update-config' in pathlib.Path('README.md').read_text()"
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- `chupa update-config` writes `config.yaml` or any file, takes the writer lock, or writes a journal event;
- a Claude alias is mapped from its `init` event when the `result` event did not report success;
- a hidden Codex entry (`visibility` other than `list`) is listed as served;
- `ExecutableNotFound` for `ollama` is raised instead of reported as a problem with a road;
- a file outside the scope fence changes.

## Time budget
- expected: 75m
- stuck: 150m
