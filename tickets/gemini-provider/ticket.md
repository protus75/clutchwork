---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- tickets/gemini-provider/evidence/README.md
- tickets/gemini-provider/evidence/fact-01-result-event-shape.txt
- tickets/gemini-provider/evidence/fact-02-failed-turn-exit.txt
- tickets/gemini-provider/evidence/fact-04-context-filename-agents-md.txt
- tickets/gemini-provider/evidence/fact-05-auth-and-quota-wording.txt
- tickets/gemini-provider/evidence/fact-06-process-argv.txt
- tickets/gemini-provider/evidence/fact-11-workspace-trust-and-files.txt
- tickets/gemini-provider/evidence/fact-12-model-selection.txt
- tickets/gemini-provider/evidence/fact-14-list-models.txt
- clutch/providers.py::FAILURE_MARKERS
- clutch/providers.py::child_env
- clutch/providers.py::routed_conduct_paths
- clutch/providers.py::Parsed
- clutch/providers.py::CliAdapter
- clutch/providers.py::_events
- clutch/providers.py::ClaudeAdapter
- clutch/providers.py::CodexAdapter
- clutch/providers.py::QwenAdapter
- clutch/providers.py::ADAPTERS
- clutch/providers.py::suggest_config
- clutch/qwen-settings.json
- clutch/watchdog.py::CallMeter
- clutch/watchdog.py::Detector
- clutch/observe.py::live_call
- clutch/docs/host-qwen.md
- clutch/docs/host-contract.md#Complete field inventory
- docs/how-clutch-works.md#8.1 Providers
- tests/unit/test_qwen_adapter.py
- tests/unit/test_live_call.py
- tests/unit/test_install_verb.py
- tests/unit/test_init_config_verb.py::test_verb
- tests/unit/test_init_config_verb.py::test_suggestions
- tests/unit/test_update_config_verb.py::test_verb
- tests/unit/test_docs_verb.py::test_docs_without_config_or_lock
- tests/integration/test_closed_sets.py::test_providers_closed_sets_and_constants
- tests/integration/test_cli.py::test_docs_reports_installed_guides
- tests/integration/test_providers.py::CONFIG
- tests/integration/test_providers.py::ENV
- tests/integration/test_providers.py::config
- tests/integration/test_providers.py::FakeExec
- tests/integration/test_providers.py::provider_session
- tests/integration/test_providers.py::req
- tests/integration/test_providers.py::jsonl
- tests/integration/test_providers.py::test_unknown_cli_provider_has_no_adapter

## On-demand
- clutch/__main__.py

## Goal / Why
clutch routes calls only to the `claude`, `codex`, and `qwen` CLIs. A provider named `gemini` is refused at setup with `no shipped cli adapter`. Roadmap row 32 (`docs/gemini-graphics-refactor-plan.md` Part A) adds Google's Gemini CLI (`gemini`, pnpm package `@google/gemini-cli`) as a fourth adapter, so a host can route review or implement work to Gemini models.

The plan's hand test A0 was run by an agent on 2026-11-15 against `@google/gemini-cli` 0.49.0 with an API key and an empty `HOME`. Its captures are this ticket's evidence under `tickets/gemini-provider/evidence/` (`README.md` and `fact-01` to `fact-14`, plus the two 64x64 input images of fact 7). The two 1024x1024 images that fact 7 recovered stay at `.claude/evidence/gemini-a0/fact-07-generated-fusion.png` and `.claude/evidence/gemini-a0/fact-07-generated-4-inputs.png` and are not part of this ticket. Where the facts and the plan differ, the facts win:
- Headless `gemini` in a directory it does not trust exits 55 before any API call. `--skip-trust` passes; every tool-grant run in fact 3 (t13 to t18) used it (fact 11).
- The stream is JSONL: `init`, `message` (a `user` echo, then `assistant` chunks with `delta: true`), `tool_use` and `tool_result` (paired by `tool_id`), `error`, and a terminal `result` with `status` `success` or `error`, an optional `error {type, message}`, and `stats` (`input_tokens` including cached, `output_tokens`, `cached`, `total_tokens`, and a `models` map). The reply text is the concatenation of the assistant chunks; `result` carries no text (fact 1).
- A failure can exit 0: an "Invalid stream" turn has an `error` event, `result.status: "error"`, and exit 0 (t27). Other observed exits: 1 (model 404), 144 (invalid key), 41 (no auth), 42 (no input), 55 (untrusted). So success is `result.status == "success"`, never the exit code (fact 2).
- `-m` is not a literal pin. Any name ending in `flash` is rewritten; `-m gemini-2.5-flash` was served as `gemini-3.6-flash`. The `result.stats.models` key is the model actually served (fact 12).
- A `tools.core` allowlist of `read_file`, `glob`, `grep_search`, `list_directory` in the file `GEMINI_CLI_SYSTEM_SETTINGS_PATH` names blocks writes and shell even under `--approval-mode yolo`, and a workspace `.gemini/settings.json` cannot widen it. A system file without `tools.core`, plus `--approval-mode yolo`, writes and runs shell. Headless `default` mode does not offer the write or shell tools (fact 3).
- `context.fileName: "AGENTS.md"` loads `AGENTS.md`, but it adds to `GEMINI.md` instead of replacing it, so a host's `GEMINI.md` (or `~/.gemini/GEMINI.md`) also loads (fact 4).
- Auth wording: `Please set an Auth method ...` (exit 41) and `API key not valid ... API_KEY_INVALID` (exit 144). Model errors: `ModelNotFoundError: ...` on stderr while `result.error.message` reads `[API Error: An unknown error occurred.]`. Quota wording from the CLI source: `RESOURCE_EXHAUSTED` for HTTP 429 and `You have exhausted your daily quota on this model.` for a daily quota (fact 5).
- Each call runs as two node processes, a launcher and a `--max-old-space-size` relaunch child. The launcher's argv[1] is `.../bin/gemini` under npm or nvm and `.../@google/gemini-cli/bundle/gemini.js` under pnpm (fact 6).
- A stdin-only prompt runs headless; no `-p` is needed (fact 10). No USD cost appears anywhere, only tokens (fact 13). The CLI has no model-listing command, and the API's ListModels is not authoritative (`gemini-2.5-pro` is listed but returns 404). Served ids include `gemini-3.1-pro-preview`, `gemini-3-flash-preview`, and `gemini-3.1-flash-lite`; the plan's `gemini-3-pro`, `gemini-3-flash`, and `gemini-2.5-pro` are not usable (fact 14).
- The CLI discards generated images, so image generation through it is impossible (fact 7). The later `api-provider-client` ticket owns that.

When this ticket is done:
- A provider declared as `name: gemini` with `auth: GEMINI_API_KEY` is served by a new `GeminiAdapter`. It authenticates with the key in `GEMINI_API_KEY`, which `child_env` passes only to gemini calls. `clutch init-config` writes that `auth` line for a gemini it finds: the key is gemini's only covered auth, and `child_env` removes and the redactor scrubs only a declared `auth`, so a suggestion without it would pass the key to every child process unredacted (`CLAUDE.md` section A, "Never pass a provider key to a process that does not need it"). It sends the prompt on stdin. It grants tools through one of two packaged settings files chosen per call. It decides success from the terminal `result` event's `status`, and it records the model the stream says served the call.
- The watchdog meters a gemini call's tool ids and tokens, and the live view labels a running gemini call `gemini <model>` for npm, nvm, and pnpm installs.
- `clutch docs` lists a fifth guide, `clutch/docs/host-gemini.md`, and the host contract and `docs/how-clutch-works.md` §8.1 describe the fourth adapter truthfully, including that `GEMINI.md` still loads.

Routing gemini in this repo's `config.yaml` stays an operator edit after setup; Part A does not require it.

## Scope in / Scope out
- In:
  - `clutch/gemini-readonly.json` (new): exactly `{"tools": {"core": ["read_file", "glob", "grep_search", "list_directory"]}, "context": {"fileName": "AGENTS.md"}}` plus a trailing newline.
  - `clutch/gemini-write.json` (new): exactly `{"context": {"fileName": "AGENTS.md"}}` plus a trailing newline. Neither file carries a trust setting; the trust grant is the `--skip-trust` flag, the form every observed tool-grant run used.
  - `clutch/providers.py`:
    - `FAILURE_MARKERS` gains three lowercase markers, each appended at the end of its row: `"exhausted your daily quota"` in `quota_exhausted`, `"resource_exhausted"` in `rate_limited`, and `"modelnotfounderror"` in `model_error`. Because `quota_exhausted` is checked before `rate_limited`, a daily-quota message that also carries `RESOURCE_EXHAUSTED` stays a quota error, while a plain 429 is a rate limit.
    - `Parsed` gains a last field `model: str | None = None`: the model the stream says served the call. `CliAdapter.invoke` returns `LLMResult.model` as `parsed.model` when it is not `None`, else the requested model. The claude, codex, and qwen parses never set it, so their results do not change.
    - `CliAdapter.call_env` takes `writes: bool`, and `invoke` passes `self.call_env(writes)`. `QwenAdapter.call_env` takes the same parameter and ignores it.
    - `CliAdapter` gains `AUTH_ENV: str | None = None`, the env var the CLI itself reads its key from. `suggest_config` writes `    auth: <AUTH_ENV>` directly after an adapter's `package` line when `AUTH_ENV` is set. The claude, codex, and qwen adapters leave it `None`, so their suggestions do not change.
    - New `class GeminiAdapter(CliAdapter)`, placed after `QwenAdapter`, registered as `"gemini": GeminiAdapter`, the last entry of `ADAPTERS`. It sets:
      - `PACKAGE = "@google/gemini-cli"`, `binary = "gemini"`, `reports_cost = False`;
      - `AUTH_MARKERS = ("please set an auth method", "api key not valid")` and `AUTH_ENV = "GEMINI_API_KEY"`;
      - `LOGIN_ROAD` to ``export GEMINI_API_KEY as clutch/docs/host-gemini.md describes, then `clutch drain` ``;
      - `argv(model, effort, writes)` to return `["gemini", "--skip-trust", "-m", model, "-o", "stream-json", "--approval-mode", "yolo" if writes else "default"]`. `default` is the mode run t13 ran in without a flag. There is no effort flag and no `-p`: the prompt arrives on stdin as for every adapter;
      - `call_env(writes)` to return the base result plus `GEMINI_CLI_SYSTEM_SETTINGS_PATH` set to the absolute path of the packaged `gemini-write.json` when `writes` is true and `gemini-readonly.json` otherwise, located from `Path(__file__).parent` as `QwenAdapter.call_env` locates `qwen-settings.json`;
      - `parse(out)`, over `_events(out)`:
        - no `result` event: raise `ValueError` whose text starts `no terminal result event`;
        - the last `result` event's `status` is not `"success"`: raise `ValueError` whose text starts `result event reports failure: ` and names `result.error.message` when present, else the `message` of the last `error` event, else the status;
        - otherwise return `Parsed(text=<every role-"assistant" message event's content, concatenated in order>, input_tokens=stats["input_tokens"], output_tokens=stats["output_tokens"], usd=None, model=<the single key of stats["models"]>)`. When `stats.models` has no key or more than one, `model` is `None`;
      - `list_models` as a classmethod that runs no process and returns `ModelListing({}, (problem,))`. The problem says that gemini has no model-listing command, names `clutch/docs/host-gemini.md`, and names `clutch probe gemini`. `suggest_config` handles that listing as any empty listing (placeholder models, the problem as a comment, the `0.25` estimate) plus the `auth` line above, and `update-config` prints the problem as a `problem:` line unchanged.
    - `routed_conduct_paths` does not change: it already selects `AGENTS.md` for gemini.
  - `clutch/watchdog.py` `CallMeter._consume`: a `tool_use` event adds its `tool_id` to `self.tools`. A `result` event that carries `stats` and no `usage` (Gemini's terminal event) uses `stats` as its terminal usage, so its `input_tokens` and `output_tokens` are counted, and `cached` and `total_tokens` are not. The claude and codex branches do not change.
  - `clutch/observe.py` `live_call`: add one branch, after the qwen branch. A process whose argv[0] file name is `node` and whose argv[1] has the file name `gemini` (npm or nvm, `.../bin/gemini`) or contains `/@google/gemini-cli/` (pnpm, `.../@google/gemini-cli/bundle/gemini.js`) returns `gemini <model>`, with the model read after `-m` (`?` when absent). The relaunch child's argv[1] is `--max-old-space-size=<n>`, so only the launcher matches, and the walk reaches the launcher first. Leave the claude, codex, and qwen branches unchanged.
  - `clutch/__main__.py`: the `docs` verb's tuple gains a fifth entry, `("gemini", "gemini provider setup")`, after `qwen`. Nothing else in the file changes; `install`, `init-config`, `update-config`, and `probe` pick gemini up from `ADAPTERS`.
  - `clutch/docs/host-gemini.md` (new), the host setup guide. It never tells the operator to create or edit a file in their home directory, and it names `clutch` verbs, never clutch's gemini argv. Sections, in this order:
    1. **What it is**: Google's Gemini CLI (`gemini`) as a clutch provider for text work. clutch passes the prompt, the tool grant, the conduct file, and the workspace trust itself, so no gemini configuration file is needed. Image generation does not work through it: the CLI discards generated images.
    2. **Install**: `clutch install gemini` (a pnpm dev dependency in the host), or `pnpm add -g @google/gemini-cli@latest`.
    3. **Authenticate**: create an API key in Google AI Studio, export `GEMINI_API_KEY` in the environment that starts clutch, and declare `auth: GEMINI_API_KEY` (`clutch init-config` writes that line when it finds gemini). The CLI reads exactly that variable. Declaring it makes clutch pass the key only to gemini calls and redact it from captures. Google OAuth login and Vertex AI are not covered.
    4. **Pick models**: the CLI has no listing command, so `clutch update-config` lists no gemini models and prints a problem line. The hand test called `gemini-3.1-pro-preview` and `gemini-3.1-flash-lite`, and the API lists `gemini-3-flash-preview`. A name ending in `flash` is rewritten by the CLI (`gemini-2.5-flash` was served as `gemini-3.6-flash`); clutch records the served name as the call's model. `gemini-2.5-pro` is listed but returns 404 for new keys. Confirm every choice with `clutch probe gemini`.
    5. **Declare it in config.yaml**: a YAML snippet with `name: gemini`, `kind: cli`, `package: "@google/gemini-cli"`, `auth: GEMINI_API_KEY`, `models_by_tier` naming the ids above, and `limits: {concurrency: 1, est_cost_per_call_usd: 0.25}`.
    6. **Probe it**: `clutch probe gemini` prints `gemini <model>: ok`. `Please set an Auth method` means the key is not exported in clutch's environment; `API key not valid` means the key is wrong; a model error means the id is not served.
    7. **Route it**: an example row, `{tier: medium, surface: review, candidates: [{provider: claude}, {provider: gemini}]}`. Preflight probes every routed model at drain start.
    8. **Conduct file**: gemini reads `AGENTS.md`, where `clutch core` writes the managed block once gemini is routed. It also loads any `GEMINI.md` in the working directory or home, which clutch cannot switch off; keep host rules in `AGENTS.md`.
    9. **Limits**: the CLI reports tokens, never USD, so `est_cost_per_call_usd` is the per-call charge; edit it to the operator's prices. Each call carries about 8k input tokens of the CLI's own system prompt. A daily-quota error cools gemini for `limits.quota_window_minutes`. A prompt over 8 MiB is truncated without an error. Each call leaves a full transcript under `~/.gemini/tmp/`, and an API error writes `/tmp/gemini-client-error-*.json` holding the prompt context. A refusal is a successful reply.
  - `clutch/docs/host-contract.md`, section "Complete field inventory" only:
    - "Shipped runtime adapters are `claude`, `codex`, and `qwen` (see [qwen setup](host-qwen.md))" becomes "Shipped runtime adapters are `claude`, `codex`, `qwen` (see [qwen setup](host-qwen.md)), and `gemini` (see [gemini setup](host-gemini.md))";
    - "Codex and qwen report no cost" becomes "Codex, qwen, and gemini report no cost".

    The Managed conduct sentence stays as it is: gemini falls under "AGENTS.md otherwise".
  - `docs/how-clutch-works.md` §8.1 only:
    - "Three CLI adapters ship: ..." becomes "Four CLI adapters ship: `claude`, `codex`, `qwen` (Qwen Code against a local Ollama model at the provider’s `base_url`), and `gemini` (Google's Gemini CLI with an API key)";
    - the write-access list adds `gemini --approval-mode yolo`. Add one sentence: gemini's grant is also a packaged system settings file chosen per call, `gemini-readonly.json` allowing only its read tools and `gemini-write.json` allowing every tool;
    - the conduct sentence adds: `gemini` reads `AGENTS.md` through the packaged settings files' `context.fileName`, and also loads any `GEMINI.md`, which that setting cannot exclude;
    - the **Model names** paragraph adds: `gemini` lists none, because the CLI has no listing command; a gemini call records the model its stream's `stats.models` names, because `-m` does not pin flash-family names.
  - New tests, each in a new file:
    - `tests/unit/test_gemini_adapter.py`: argv, `call_env`, `parse`, failure classes, registry, listing, suggested config, conduct path, and setup refusals, with fakes and no disk, process, or network. The recorded streams and stderr texts are string literals copied from the evidence runs named in the criteria. A fake config that reaches `child_env` or `Redactor.from_config` carries `release=SimpleNamespace(pypi_token="UV_PUBLISH_TOKEN")` beside `providers`. That attribute is unread at HEAD. It keeps the file valid in either merge order with the confirmed ticket `release-publish`, whose moved `secret_names` reads `config.release.pypi_token`: without it this file raises `AttributeError` after that ticket merges, and if this ticket merges first it fails `release-publish`'s suite in a file outside that ticket's fence.
    - `tests/unit/test_watchdog_gemini.py`: `CallMeter` over a recorded gemini stream, with a `Detector` built from fakes.
    - `tests/unit/test_live_call_gemini.py`: `live_call` over hand-built process rows.
    - `tests/integration/test_gemini_provider.py`: the two packaged settings files, and gemini calls through `ProviderLLM` with `FakeExec`. It may import `CONFIG`, `ENV`, `config`, `FakeExec`, `provider_session`, `req`, and `jsonl` from `tests/integration/test_providers.py`, as other test modules do, and changes none of them.
  - Existing tests whose assertions flip, each changed only as named:
    - `tests/unit/test_install_verb.py`: `Exec.run`'s version mapping gains `"gemini": "0.49.0\n"`; `test_install`'s no-argument expected output gains the last line `gemini: system 0.49.0, package @google/gemini-cli`; `main("codex", "gemini")` becomes `main("codex", "llama")`, and its expected refusal text `"claude, codex, qwen"` becomes `"claude, codex, gemini, qwen"`.
    - `tests/unit/test_init_config_verb.py::test_verb`: `"run: clutch install claude|codex|qwen"` becomes `"run: clutch install claude|codex|gemini|qwen"`.
    - `tests/unit/test_update_config_verb.py::test_verb`: `provider("gemini", ["x"] * 4)` becomes `provider("llama", ["x"] * 4)`, and the expected line becomes `llama: no shipped cli adapter; name one of claude, codex, gemini, qwen`.
    - `tests/unit/test_docs_verb.py::test_docs_without_config_or_lock` and `tests/integration/test_cli.py::test_docs_reports_installed_guides`: the guide name tuple gains `"gemini"` last, and `len(lines) == 4` becomes `len(lines) == 5`.
    - `tests/integration/test_closed_sets.py::test_providers_closed_sets_and_constants`: the `ADAPTERS` identity map gains `"gemini": "GeminiAdapter"`, the `PACKAGE` map gains `"gemini": "@google/gemini-cli"`, and the `FAILURE_MARKERS` literal gains the three markers above in those positions.
    - `tests/integration/test_providers.py::test_unknown_cli_provider_has_no_adapter`: the renamed provider `gemini` becomes `llama` in both replacements.
    - `tests/unit/test_qwen_adapter.py::test_qwen_argv_and_env`: both `a.call_env()` calls become `a.call_env(False)`.
- Out:
  - `config.yaml`: routing gemini is an operator edit after setup.
  - Image generation, image models, the judge's JSON schema and temperature aliases (Part B and `api-provider-client`), Vertex AI, and Google OAuth login.
  - Any HTTP client, a ListModels call, or a probe call inside `list_models`.
  - `update-config`'s generic per-model wording when a listing names no models.
  - Any change to the argv or parse of `ClaudeAdapter`, `CodexAdapter`, or `QwenAdapter`, and to `routed_conduct_paths`.
  - `README.md`: its "`AGENTS.md` for other CLIs" stays true for gemini.
  - Disabling the CLI's own transcripts under `~/.gemini/tmp/` (filed to the Suggestion Box).

## Scope fence
- clutch/providers.py
- clutch/gemini-readonly.json
- clutch/gemini-write.json
- clutch/watchdog.py
- clutch/observe.py
- clutch/__main__.py
- clutch/docs/host-gemini.md
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_gemini_adapter.py
- tests/unit/test_watchdog_gemini.py
- tests/unit/test_live_call_gemini.py
- tests/integration/test_gemini_provider.py
- tests/unit/test_install_verb.py
- tests/unit/test_init_config_verb.py
- tests/unit/test_update_config_verb.py
- tests/unit/test_docs_verb.py
- tests/unit/test_qwen_adapter.py
- tests/integration/test_cli.py
- tests/integration/test_closed_sets.py
- tests/integration/test_providers.py

## Acceptance criteria
1. `tests/unit/test_gemini_adapter.py::test_argv_grants` asserts `argv("gemini-3.1-flash-lite", "high", False)` equals `["gemini", "--skip-trust", "-m", "gemini-3.1-flash-lite", "-o", "stream-json", "--approval-mode", "default"]`, and that `writes=True` differs only in `yolo` in place of `default`. Ruled out: `yolo` on a read-only call, a `-p` flag or positional prompt, an effort flag, and an argv without `--skip-trust` (exit 55, fact 11).
2. `tests/unit/test_gemini_adapter.py::test_call_env_selects_the_grant_file` builds the adapter for a provider with `auth="GEMINI_API_KEY"` beside a `claude` provider with `auth="CLAUDE_KEY"`, in a config `SimpleNamespace(providers=[<gemini>, <claude>], release=SimpleNamespace(pypi_token="UV_PUBLISH_TOKEN"))`, with env `{"PATH": "/bin", "GEMINI_API_KEY": "g", "CLAUDE_KEY": "c"}`. It asserts that `Path(call_env(False)["GEMINI_CLI_SYSTEM_SETTINGS_PATH"])` equals `Path(clutch.__file__).parent / "gemini-readonly.json"` and is absolute, and that `call_env(True)` names `gemini-write.json` the same way. Both envs carry `GEMINI_API_KEY` and not `CLAUDE_KEY`, and `PATH` starts with `/repo/node_modules/.bin`. Ruled out: the write file on a read-only call, a relative path, and the other provider's key in the gemini child.
3. `tests/unit/test_gemini_adapter.py::test_parse_success` parses the recorded stdout of run t17 (`fact-01-result-event-shape.txt`) and asserts text ``"DONE\n\nSteps succeeded:\n1. Created `out.txt` containing `WRITTEN`.\n2. Ran `echo SHELL > shell.txt` to create `shell.txt`."``, `input_tokens == 21982`, `output_tokens == 186`, `usd is None`, and `model == "gemini-3.6-flash"`. It also asserts that run t02 (`-m gemini-2.5-flash`) parses to text `PONG` and model `gemini-3.6-flash`, and that a hand-built success `result` whose `stats.models` has two keys gives `model is None` (hand-built: A0 observed no fallback switch). Ruled out: the user echo in the text, only the last chunk, `13638` or `30326` input tokens, and `gemini-2.5-flash` (the `-m` and `init` name) as the model.
4. `tests/unit/test_gemini_adapter.py::test_parse_failures` asserts that `parse` raises `ValueError` for: run t27's stdout (`fact-02`: an `error` event and `status: "error"`, exit 0), with `Invalid stream` in the text; run t04's stdout, with `[API Error: An unknown error occurred.]` in the text; and `""` (run t06), with `no terminal result event` in the text. Ruled out: a `Parsed` for an exit-0 failure stream.
5. `tests/unit/test_gemini_adapter.py::test_failure_classes` calls `classify_failure("nonzero exit", rc=..., stderr_tail=...)` on the recorded stderr and asserts:
   - run t06 (exit 41): `auth_error` with `paved_road == GeminiAdapter.LOGIN_ROAD`;
   - run t07 (exit 144): `auth_error`;
   - run t34 `gemini-2.5-pro` (exit 1): `model_error`;
   - `You have exhausted your daily quota on this model. (Status: RESOURCE_EXHAUSTED)`: `quota_exhausted`;
   - `[API Error: Resource has been exhausted (e.g. check quota). (Status: RESOURCE_EXHAUSTED)] Please wait and try again later. To increase your limits, request a quota increase through AI Studio, or switch to another /auth method`: `rate_limited`, not `quota_exhausted`.

   The two quota texts are hand-built from the source wording in `fact-05`, because a 429 cannot be provoked cheaply on a paid key. Ruled out: `unclassified` for any of the five.
6. `tests/unit/test_gemini_adapter.py::test_registry_listing_and_conduct` asserts:
   - `providers.ADAPTERS["gemini"] is GeminiAdapter`, with `PACKAGE == "@google/gemini-cli"`, `binary == "gemini"`, and `reports_cost is False`;
   - `list_models` with an exec fake whose `run` raises `AssertionError` returns no models and exactly one problem containing `host-gemini.md` and `clutch probe gemini`;
   - `suggest_config([CliStatus("gemini", "@google/gemini-cli", "gemini", "system", "0.49.0")], {"gemini": <that listing>})` contains the line `    auth: GEMINI_API_KEY` directly after the `package` line, `OPERATOR-SETS-THIS` for all four tiers, and `est_cost_per_call_usd: 0.25`. `load_config_text` of that text (path `/repo/config.yaml`, cwd `/repo`) loads a gemini provider whose `auth == "GEMINI_API_KEY"`. A suggestion for a `claude` status alone has no `auth:` line;
   - `routed_conduct_paths` for a config routing only `gemini` returns `(checkout / "AGENTS.md",)`;
   - constructing the adapter for a provider without `est_cost_per_call_usd`, or with a `base_url`, raises `ProviderSetupError`.

   Ruled out: a listing that spawns a process, a suggested gemini block without `auth` (its key would reach every child process unredacted), an `auth` line added to the other adapters' suggestions, and `CLAUDE.md` as gemini's conduct file.
7. `tests/unit/test_watchdog_gemini.py::test_meter_reads_gemini_tools_and_stats` starts a call on a `Detector` built from fakes, with `Served(<gemini provider, est_cost_per_call_usd=0.5>, "gemini-2.5-flash")`, and feeds the parsed events of run t17. It asserts `meter.tools` equals the three `tool_id`s of its `tool_use` events, `detector.tokens == 22168`, and `detector.spend == 0.5`. After `meter.complete()`, `detector.bases == {}`. Ruled out: `tokens is None` (stats ignored), `23016` (`total_tokens`), and `30512` (`cached` added).
8. `tests/unit/test_live_call_gemini.py` asserts that `live_call` over a drain row plus the two process rows of each install form returns one label:
   - the npm/nvm form `node /home/u/.nvm/versions/node/v24.15.0/bin/gemini --skip-trust -m gemini-3.1-flash-lite -o stream-json` with its child `/home/u/.nvm/versions/node/v24.15.0/bin/node --max-old-space-size=20054 /home/u/.nvm/versions/node/v24.15.0/bin/gemini --skip-trust -m gemini-3.1-flash-lite -o stream-json` returns `gemini gemini-3.1-flash-lite`;
   - the pnpm form `node /p/global/5/.pnpm/@google+gemini-cli@0.49.0/node_modules/@google/gemini-cli/bundle/gemini.js --skip-trust -m gemini-3.1-pro-preview -o stream-json` with its child returns `gemini gemini-3.1-pro-preview`;
   - a launcher without `-m` returns `gemini ?`;
   - `node /usr/lib/node_modules/npm/bin/npm-cli.js install` returns `""`.

   Ruled out: `""` for the npm/nvm form (the plan's pnpm-only matcher).
9. `tests/integration/test_gemini_provider.py::test_packaged_settings_files` asserts that `clutch/gemini-readonly.json` parses to exactly `{"tools": {"core": ["read_file", "glob", "grep_search", "list_directory"]}, "context": {"fileName": "AGENTS.md"}}` and `clutch/gemini-write.json` to exactly `{"context": {"fileName": "AGENTS.md"}}`, and that both are the existing files that `call_env(False)` and `call_env(True)` name. Ruled out: `write_file`, `replace`, `run_shell_command`, or `invoke_agent` in the read-only allowlist, and a `tools` key in the write file.
10. `tests/integration/test_gemini_provider.py::test_calls_through_provider_llm` loads a config that declares `gemini` with `auth: GEMINI_API_KEY` and `est_cost_per_call_usd: 0.5` and routes it, then sends requests through `ProviderLLM` with `FakeExec` and an env carrying `GEMINI_API_KEY` and `CLAUDE_KEY`:
    - a read-only request replaying run t02's stdout returns `text == "PONG"`, `model == "gemini-3.6-flash"`, and `usd == 0.5`. The recorded call's argv ends `--approval-mode default`, its env names `gemini-readonly.json` and carries `GEMINI_API_KEY` but not `CLAUDE_KEY`, and its stdin holds the prompt;
    - an `implement` request with a worktree runs with `yolo`, the `gemini-write.json` path, and `cwd` equal to the worktree;
    - run t27's stdout with exit 0 raises `ProviderCallError`, not a result;
    - exit 41 with empty stdout and run t06's stderr raises `ProviderCallError` with `failure_class == "auth_error"` and `paved_road == GeminiAdapter.LOGIN_ROAD`.

    Ruled out: an exit-0 failure accepted as success, and the requested `gemini-2.5-flash` recorded as the served model.
11. `./dev.py test tests/unit/test_install_verb.py tests/unit/test_init_config_verb.py tests/unit/test_update_config_verb.py tests/unit/test_docs_verb.py tests/unit/test_qwen_adapter.py tests/unit/test_live_call.py tests/integration/test_closed_sets.py tests/integration/test_providers.py tests/integration/test_cli.py tests/integration/test_host_contract.py tests/integration/test_engine_text_verbs.py tests/integration/test_watchdog.py tests/integration/test_watchdog_activation.py` exits 0 with only the assertions named in `## Scope in / Scope out` changed. So `clutch docs` prints five guides ending with `host-gemini.md`, `ADAPTERS` names `claude`, `codex`, `qwen`, and `gemini`, the claude, codex, and qwen `live_call` labels and watchdog metering are unchanged, and `clutch/docs/host-gemini.md` names no `dev.py`.
12. The `uv run python -c` command in `## Verification` exits 0. It checks that `clutch/docs/host-gemini.md` contains each of `clutch install gemini`, `@google/gemini-cli`, `auth: GEMINI_API_KEY`, `name: gemini`, `clutch probe gemini`, `{provider: gemini}`, `gemini-3.1-pro-preview`, `gemini-3.1-flash-lite`, `GEMINI.md`, `est_cost_per_call_usd`, and `quota_window_minutes`. It also checks that the guide contains none of `dev.py`, `stream-json`, `--skip-trust`, `--approval-mode`, `GEMINI_CLI_SYSTEM_SETTINGS_PATH`, or `settings.json`. Finally, `docs/how-clutch-works.md` contains `Four CLI adapters ship`, `gemini-readonly.json`, and `GEMINI.md` and not `Three CLI adapters`, and `clutch/docs/host-contract.md` contains `[gemini setup](host-gemini.md)` and `Codex, qwen, and gemini report no cost`.
13. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_gemini_adapter.py tests/unit/test_watchdog_gemini.py tests/unit/test_live_call_gemini.py tests/integration/test_gemini_provider.py
./dev.py test tests/unit/test_install_verb.py tests/unit/test_init_config_verb.py tests/unit/test_update_config_verb.py tests/unit/test_docs_verb.py tests/unit/test_qwen_adapter.py tests/unit/test_live_call.py tests/integration/test_closed_sets.py tests/integration/test_providers.py tests/integration/test_cli.py tests/integration/test_host_contract.py tests/integration/test_engine_text_verbs.py tests/integration/test_watchdog.py tests/integration/test_watchdog_activation.py
uv run python -c "import pathlib; g = pathlib.Path('clutch/docs/host-gemini.md').read_text(); h = pathlib.Path('docs/how-clutch-works.md').read_text(); c = pathlib.Path('clutch/docs/host-contract.md').read_text(); need = ['clutch install gemini', '@google/gemini-cli', 'auth: GEMINI_API_KEY', 'name: gemini', 'clutch probe gemini', '{provider: gemini}', 'gemini-3.1-pro-preview', 'gemini-3.1-flash-lite', 'GEMINI.md', 'est_cost_per_call_usd', 'quota_window_minutes']; ban = ['dev.py', 'stream-json', '--skip-trust', '--approval-mode', 'GEMINI_CLI_SYSTEM_SETTINGS_PATH', 'settings.json']; bad = [s for s in need if s not in g] + [s for s in ban if s in g] + [s for s in ('Four CLI adapters ship', 'gemini-readonly.json', 'GEMINI.md') if s not in h] + (['Three CLI adapters'] if 'Three CLI adapters' in h else []) + [s for s in ('[gemini setup](host-gemini.md)', 'Codex, qwen, and gemini report no cost') if s not in c]; assert not bad, bad"
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- a file outside the scope fence changes, including `config.yaml` and `README.md`;
- the argv or parse of `ClaudeAdapter`, `CodexAdapter`, or `QwenAdapter` changes, or `QwenAdapter.call_env` changes beyond the ignored `writes` parameter;
- a read-only gemini call gets `--approval-mode yolo`, the write settings file, or an allowlist naming a write or shell tool;
- `GeminiAdapter` treats a zero exit as success when the terminal `result` status is not `success`, or passes the prompt by `-p` or argv;
- clutch code writes under `~/.gemini`, or `clutch/docs/host-gemini.md` tells the operator to create or edit a file in their home directory;
- image generation, an HTTP client, a ListModels call, or a model call inside `list_models` is added;
- a new test is added to `tests/integration/test_cli.py`, or an existing assertion other than those named in `## Scope in / Scope out` is changed or weakened.

## Time budget
- expected: 80m
- stuck: 170m
