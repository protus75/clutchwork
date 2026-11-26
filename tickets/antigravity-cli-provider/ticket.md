---
state: confirmed
source: human
priority: P0
kind: feature
---

## Depends on
- none

## Context
- clutch/config.py::Provider
- clutch/providers.py::CliAdapter
- clutch/providers.py::ADAPTERS
- clutch/providers.py::suggest_config
- clutch/providers.py::cli_status
- clutch/providers.py::ProviderLLM.preflight
- clutch/evidence/codex.py
- clutch/evidence/views.py
- clutch/evidence/schema.py::Event
- clutch/training.py::_trajectory
- clutch/training.py::_reply_text
- clutch/observe.py::extension_fields
- config.yaml

## On-demand
- clutch/__main__.py
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md

## Goal / Why
Replace the shipped `gemini` CLI provider in place with the Antigravity CLI (`agy`) provider named `antigravity` across adapters, config validation, evidence normalization, training export, CLI verbs, extension snapshot fields, documentation, fixtures, and tests.

Google's `gemini` CLI is superseded by Antigravity CLI (`agy`), which uses ambient CLI login (no `GEMINI_API_KEY`), lists models via `agy models`, enforces read-only vs write grants via `--mode plan` vs `--mode auto --dangerously-skip-permissions` (eliminating packaged JSON settings files), and is installed outside pnpm (`https://antigravity.google/cli/install.sh` to `~/.local/bin/agy`). Replacing `gemini` in place follows the no-dual-path rule and keeps `config.yaml`, provider commands, evidence views, and the extension snapshot consistent.

## Boundary contract

### CLI provider adapter registry
- disposition: replace
- owner: clutch/providers.py
- consumers: ProviderLLM, CallMeter, clutch provider install, clutch provider probe, clutch config init, clutch config update, clutch/observe.py
- observable change: replace `GeminiAdapter` (`ADAPTERS["gemini"]`) with `AntigravityAdapter` (`ADAPTERS["antigravity"]`, `binary = "agy"`, `PACKAGE = None`, `AUTH_ENV = None`, `reports_cost = False`), remove `clutch/gemini-readonly.json` and `clutch/gemini-write.json`, list models via `agy models` (stripping `\r` spinner prefixes), invoke `agy` with stdin text and `--mode plan` (read-only) or `--mode auto --dangerously-skip-permissions` (writes), and extract `conversation_id` as `native_ids.session_id` and `init.model` as `model.served` in `CliAdapter.invoke()`. Skip `pnpm view` in `ProviderLLM.preflight()` when `adapter.provider.package is None`.
- compatibility: breaking replacement of `gemini` with `antigravity` per the no-dual-path rule; all in-repo consumers, config, docs, fixtures, and tests migrate in this change.
- acceptance: `ADAPTERS["antigravity"] is AntigravityAdapter`, `"gemini" not in ADAPTERS`, `AntigravityAdapter.argv` emits the live-verified `agy` flags, `list_models` parses `agy models` output with spinner frames, and `ProviderLLM` runs `antigravity` without `package:` or settings files.
- tests: `tests/unit/test_antigravity_adapter.py`, `tests/integration/test_antigravity_provider.py`, `tests/integration/test_closed_sets.py`
- post-merge source of truth: clutch/providers.py

### CLI provider config package validation
- disposition: extend
- owner: clutch/config.py
- consumers: load_config, load_config_text, clutch config init, clutch config migrate, ProviderLLM
- observable change: `Provider._cli_declares_its_package` allows omitting `package` for a `kind: cli` provider whose shipped adapter declares `PACKAGE = None` (`antigravity`), while still refusing omitted `package` for pnpm-installed CLI providers (`claude`, `codex`, `qwen`, or unknown names).
- compatibility: existing configs declaring `package` for pnpm-based CLIs behave unchanged; `antigravity` configs omit `package`.
- acceptance: `load_config_text` accepts `name: antigravity, kind: cli` with no `package` and still raises `ConfigError` matching `declares no \`package\`` when `codex` omits `package`.
- tests: `tests/unit/test_antigravity_adapter.py`, `tests/integration/test_providers.py`
- post-merge source of truth: clutch/config.py

### Evidence stream normalizer
- disposition: replace
- owner: clutch/evidence/antigravity.py, clutch/evidence/views.py
- consumers: AntigravityAdapter.normalizer, CallMeter, clutch/evidence/views.py, clutch/training.py
- observable change: replace `clutch/evidence/gemini.py` (`gemini-stream/1`) with `clutch/evidence/antigravity.py` (`NORMALIZER_ID = "antigravity-stream/1"`, `VERIFIED_PROVIDERS = frozenset({"antigravity"})`) normalizing `agy --output-format stream-json` NDJSON (`init`, `step_update` for `user_input`, `tool` ACTIVE/DONE, `agent_response` delta/DONE, and `result` SUCCESS/ERROR); `views.normalizer` maps `"antigravity"` to `antigravity` and drops `"gemini"`.
- compatibility: breaking replacement of `gemini-stream/1` with `antigravity-stream/1` in place.
- acceptance: all observed `agy` event shapes normalize without `unknown` kinds, `result` carries `init.model`, `input_uncached`/`input_cache_read`/`output_total`/`output_reasoning`, and `parsed_from_events` + `CallMeter` consume them accurately.
- tests: `tests/unit/test_evidence_antigravity.py`, `tests/unit/test_evidence_views.py`, `tests/unit/test_provider_parsed_events.py`, `tests/unit/test_watchdog_antigravity.py`, `tests/integration/test_evidence_antigravity_fixture.py`, `tests/integration/test_provider_parsed_fixtures.py`
- post-merge source of truth: clutch/evidence/antigravity.py, clutch/evidence/views.py

### CLI provider install, init, update, and docs commands
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators, VS Code extension, MCP server
- observable change: `clutch host docs` lists `host-antigravity.md` instead of `host-gemini.md`; `clutch provider install` reports non-pnpm adapters (`PACKAGE is None`) as `installed outside pnpm` (with `follow clutch/docs/host-antigravity.md` when absent) and refuses `clutch provider install antigravity` with a paved road to `clutch/docs/host-antigravity.md`; `clutch config init` omits `package:` when `adapter.PACKAGE is None` and lists only pnpm-installable adapters in its no-CLI refusal road; `clutch config update` points missing non-pnpm binaries to `clutch/docs/host-antigravity.md`.
- compatibility: pnpm-managed providers (`claude`, `codex`, `qwen`) behave unchanged.
- acceptance: CLI unit and integration tests verify `host docs`, `provider install`, `config init`, and `config update` output and exit codes.
- tests: `tests/unit/test_docs_verb.py`, `tests/unit/test_main_host_group.py`, `tests/unit/test_install_verb.py`, `tests/unit/test_main_provider_group.py`, `tests/unit/test_init_config_verb.py`, `tests/unit/test_update_config_verb.py`, `tests/integration/test_cli.py`
- post-merge source of truth: clutch/__main__.py

### Extension snapshot provider installs
- disposition: extend
- owner: clutch/observe.py
- consumers: VS Code extension, MCP dashboard
- observable change: `extension_fields` builds `providerInstalls` only for adapters where `ADAPTERS[name].PACKAGE is not None` (`claude`, `codex`, `qwen`) so the UI never offers `installs None@latest` or passes `antigravity` to `clutch provider install`.
- compatibility: snapshot shape (`providerInstalls` list of `{label, detail, argv}`) is unchanged; entries reflect pnpm-installable adapters only.
- acceptance: `extension_fields` omits `antigravity` and `gemini` from `providerInstalls` and from `Update all providers`.
- tests: `tests/unit/test_observe_extension_fields.py`, `tests/unit/test_observe_provider_installs.py`
- post-merge source of truth: clutch/observe.py

### Training export stream assembly
- disposition: replace
- owner: clutch/training.py
- consumers: clutch training export
- observable change: `_trajectory` and `_reply_text` map `"AntigravityAdapter"` to `antigravity.normalize` instead of `"GeminiAdapter"` -> `gemini.normalize`; `_reply_text` concatenates assistant `message` deltas for `"AntigravityAdapter"`; `_trajectory` also checks `"Path"` when filtering excluded paths in tool args.
- compatibility: replaces `GeminiAdapter` in place.
- acceptance: conflict and ticket training export tests assemble chunked `AntigravityAdapter` assistant deltas and drop `GeminiAdapter`.
- tests: `tests/unit/test_training_export_conflict.py`, `tests/unit/test_training_ticket_kind.py`
- post-merge source of truth: clutch/training.py

## Scope in / Scope out

### Scope in
1. **`clutch/evidence/antigravity.py` (new) and delete `clutch/evidence/gemini.py`**:
   - Define `NORMALIZER_ID = "antigravity-stream/1"`, `VERIFIED_PROVIDERS = frozenset({"antigravity"})`, and `TOOL_CLASSES` mapping `agy` tools (`read_file` -> `read`, `write_file` -> `write`, `edit_file` -> `edit`, `run_command` -> `shell`, `grep_search` -> `search`, `find_by_name` -> `list`, `list_dir` -> `list`, `search_web` -> `web_search`, `read_url_content` -> `web_fetch`, `invoke_subagent` -> `subagent`).
   - Normalize `agy --output-format stream-json` NDJSON lines (top-level discriminator `"event"`):
     - `"init"`: `kind = "session_start"`, `native_type = "init"`; record `init_model = (native.get("init") or {}).get("model")` if a non-empty `str`.
     - `"step_update"` (`su = native.get("step_update") or {}`, `step_type = su.get("step_type")`, `state = su.get("state")`):
       - `step_type == "user_input"`: `kind = "message"`, `role = "user"`.
       - `step_type == "tool"` and `state == "ACTIVE"`: `kind = "tool_call"`, `tool_id = str(su.get("step_index", seq))`, `name = su.get("tool_name") or tool_info.get("name") or "unknown"`, `tool = {"id": tool_id, "class": TOOL_CLASSES.get(name, "other"), "native": name}`, `args = tool_info.get("parameters")` (dict or `{}`). Remember `tools[tool_id] = tool`.
       - `step_type == "tool"` and `state == "DONE"`: `kind = "tool_result"`, reuse `tools.get(tool_id)` or construct fallback, `status = "error"` if `su.get("error")` or `tool_info.get("error")` else `"success"`, `output_blob = put_blob(output.encode())` when `isinstance(output, str)` else `None`; strip `"output"` from `native["step_update"]["tool_info"]`.
       - `step_type == "agent_response"`: when `isinstance(su.get("text_delta"), str)`, append to `chunks`, emit `kind = "message"`, `role = "assistant"`, `text_blob = put_blob(delta.encode())`, and strip `"text_delta"` from `native["step_update"]`. When `state == "DONE"` without `text_delta`, emit `kind = "usage"` (never `message` with `text_blob=None`) with `tokens` mapped from `su.get("usage")` if present (no `status`, so `parsed_from_events` still resolves on the closing `result` event).
     - `"result"` (`res = native.get("result") or {}`, `usage = res.get("usage") or {}`):
       - `kind = "result"`, `success = res.get("status") == "SUCCESS"`.
       - `message = res["response"]` when `success and isinstance(res.get("response"), str)` else `"".join(chunks)` if `success` else `(res.get("error") or res.get("status") or "error")`.
       - `status = "success" if success else "error"`, `text_blob = put_blob(str(message).encode())`, `model = init_model`, strip `"response"` from `native["result"]`.
       - `tokens`: `{"input_uncached": usage.get("input_tokens"), "input_cache_read": usage.get("cache_read_tokens"), "input_cache_write": None, "output_total": usage.get("output_tokens"), "output_reasoning": usage.get("thinking_tokens"), "tokenizer": "antigravity"}`.
     - Unrecognized events or non-JSON/non-dict lines become `kind = "unknown"` (`native = {"line": line}` for non-JSON/non-dict).

2. **`clutch/providers.py`, delete `clutch/gemini-readonly.json` and `clutch/gemini-write.json`**:
   - Import `antigravity` instead of `gemini` from `clutch.evidence`.
   - Type `CliAdapter.PACKAGE: str | None = None` and `CliStatus.package: str | None`.
   - Replace `GeminiAdapter` with `AntigravityAdapter(CliAdapter)` and `ADAPTERS["antigravity"] = AntigravityAdapter`:
     - `normalizer = staticmethod(antigravity.normalize)`
     - `PACKAGE = None`, `binary = "agy"`, `reports_cost = False`, `AUTH_ENV = None`
     - `AUTH_MARKERS = ("please sign in", "not signed in", "authentication required", "unauthenticated")`
     - `LOGIN_ROAD = "run agy interactively to sign in, then `clutch engine drain`"`
     - `argv(self, model, effort, writes)`:
       - `writes=True`: `["agy", "--output-format", "stream-json", "--input-format", "text", "--model", model, "--mode", "auto", "--dangerously-skip-permissions"]`
       - `writes=False`: `["agy", "--output-format", "stream-json", "--input-format", "text", "--model", model, "--mode", "plan"]`
       - Never pass `--print` or `--disable-slash-commands`.
     - `list_models`: run `[cls.binary, "models"]`; on non-zero exit return last non-empty stripped line (after `line.rsplit("\r", 1)[-1].strip()`) as problem `f"agy models: {msg}"`; on exit 0 parse each line via `clean = line.rsplit("\r", 1)[-1].strip()`, skipping blank lines and taking `clean.split()[0]` as both key and value; if empty return problem `"agy models: no models listed"`.
   - In `CliAdapter.invoke()`:
     - When recording `native_ids` on live `stdout_line` and in the `end` record, accept top-level non-empty `"conversation_id"` as `"session_id"` when `"session_id"` is absent.
     - When recording `end.model.served`, check top-level `"model"` first and fall back to nested `event["init"]["model"]` (when `isinstance(event.get("init"), dict)` and `isinstance(event["init"].get("model"), str)`).
   - In `suggest_config`: omit the `package:` line when `adapter.PACKAGE is None`.
   - In `ProviderLLM.preflight()`: still run `[adapter.binary, "--version"]` to capture `adapter.cli_version`, then skip `pnpm view` when `adapter.provider.package is None`; in probe-failure messages, when `adapter.PACKAGE is None`, use `check {adapter.binary} (clutch/docs/host-{provider}.md)` instead of `run: clutch provider install {provider}`.
   - `conduct_file("antigravity")` continues to return the non-Claude conduct filename (same as `codex`).

3. **`clutch/config.py`**:
   - Update `Provider._cli_declares_its_package` to allow `not self.package` when `ADAPTERS.get(self.name)` exists and has `PACKAGE is None` (using a local `from clutch.providers import ADAPTERS` import, matching `Route._known_kinds`), while still refusing missing `package` for pnpm-based CLI providers and unknown CLI names.

4. **`clutch/evidence/views.py`, `clutch/training.py`, `clutch/observe.py`**:
   - `clutch/evidence/views.py`: swap `gemini` -> `antigravity` in import and `normalizer()`.
   - `clutch/training.py`: swap `gemini` -> `antigravity` and `"GeminiAdapter"` -> `"AntigravityAdapter"` in `_trajectory()` and `_reply_text()`; include `"Path"` in `_trajectory()`'s path-key lookup.
   - `clutch/observe.py`: build `providerInstalls` in `extension_fields()` over `[name for name in sorted(ADAPTERS) if ADAPTERS[name].PACKAGE is not None]`.

5. **`clutch/__main__.py`**:
   - `handle_docs`: replace `("gemini", "gemini provider setup")` with `("antigravity", "antigravity provider setup")`.
   - `handle_install`: refuse named providers whose `PACKAGE is None` with `runner.Refusal(f"{name} is not installed through pnpm", f"follow clutch/docs/host-{name}.md")`; when reporting status with no names, format `status.package is None` as `f"{status.name}: {status.where}{' ' + status.version if status.version else ''}, installed outside pnpm"` plus `f" -- follow clutch/docs/host-{name}.md"` when `status.where == "absent"`. Update `provider install` help text accordingly.
   - `handle_init_config`: in the no-CLI refusal road, list only pnpm-installable adapters (`claude|codex|qwen`).
   - `handle_update_config`: on `ExecutableNotFound`, use `f"follow clutch/docs/host-{name}.md"` when `ADAPTERS[name].PACKAGE is None`.

6. **`config.yaml`**:
   - Update the top comment (`Claude, codex, and antigravity use ambient CLI login`).
   - Replace the `gemini` provider entry with:
     ```yaml
       - name: antigravity
         kind: cli
         models_by_tier: {low: gemini-3.8-flash-low, medium: gemini-4-neon-medium, high: gemini-4-neon-high, max: gemini-4-carbon-high}
         limits: {concurrency: 1, est_cost_per_call_usd: 0.25}
     ```
     (no `package:` key).

7. **Docs**:
   - Create `clutch/docs/host-antigravity.md` and delete `clutch/docs/host-gemini.md`: document `agy` install (`https://antigravity.google/cli/install.sh` to `~/.local/bin/agy`), ambient login (`agy` interactively), model listing (`clutch config update`), `config.yaml` declaration (no `package:`), `clutch provider probe antigravity`, routing, conduct file managed by `clutch host core`, and cost/token limits.
   - Update `README.md` (intro provider list and setup link to `clutch/docs/host-antigravity.md`).
   - Update `clutch/docs/host-contract.md` (frontmatter `relates`, provider table/prose around lines 300-304 noting `antigravity` and optional `package` for non-pnpm CLIs).
   - Update `clutch/docs/host-running.md` (`provider install` verb row noting non-pnpm providers).
   - Update `docs/how-clutch-works.md` (provider adapters, write/read-only grants, conduct files, model listing around lines 645-652, and normalizer IDs around line 862).

8. **Fixtures and tests**:
   - Replace `tests/fixtures/evidence/gemini/` (`README.md`, `stream.jsonl`) with `tests/fixtures/evidence/antigravity/` (`README.md`, `stream.jsonl`) containing a realistic multi-step `agy --output-format stream-json` capture (init, `user_input`, `tool` ACTIVE/DONE with `read_file` and `run_command`, `agent_response` `text_delta` + DONE, and `result` SUCCESS with `usage`).
   - Replace `tests/unit/test_gemini_adapter.py`, `tests/unit/test_evidence_gemini.py`, `tests/unit/test_watchdog_gemini.py` with `tests/unit/test_antigravity_adapter.py`, `tests/unit/test_evidence_antigravity.py`, `tests/unit/test_watchdog_antigravity.py`.
   - Replace `tests/integration/test_gemini_provider.py` and `tests/integration/test_evidence_gemini_fixture.py` with `tests/integration/test_antigravity_provider.py` (using in-memory `FakeFileSystem`, NO `disk_io_skip` marker) and `tests/integration/test_evidence_antigravity_fixture.py`.
   - Update existing tests pinned to the provider/doc/adapter sets:
     - `tests/unit/test_callmeter_events.py` (update import from `test_antigravity_adapter`)
     - `tests/unit/test_docs_verb.py` (`gemini` -> `antigravity`)
     - `tests/unit/test_main_host_group.py` (`gemini` -> `antigravity`)
     - `tests/unit/test_evidence_views.py` (`gemini` -> `antigravity`, `antigravity-stream/1`)
     - `tests/unit/test_init_config_verb.py` (no-CLI refusal road `claude|codex|qwen` and `agy` in `Exec`)
     - `tests/unit/test_install_verb.py` (`antigravity` status line, refusal on `provider install antigravity`, unknown-provider list `antigravity, claude, codex, qwen`)
     - `tests/unit/test_main_provider_group.py` (status line format for `PACKAGE is None`)
     - `tests/unit/test_observe_extension_fields.py` (remove `gemini` from `providerInstalls` and `Update all providers`)
     - `tests/unit/test_observe_provider_installs.py` (filter `ADAPTERS` by `PACKAGE is not None`)
     - `tests/unit/test_provider_parsed_events.py` (replace `test_gemini_closing` with `test_antigravity_closing`, `GeminiAdapter` -> `AntigravityAdapter`)
     - `tests/unit/test_training_export_conflict.py` and `tests/unit/test_training_ticket_kind.py` (`GeminiAdapter` -> `AntigravityAdapter` with `agy` `step_update` `agent_response` `text_delta` events)
     - `tests/unit/test_update_config_verb.py` (unknown-adapter message `antigravity, claude, codex, qwen` and `AntigravityAdapter.list_models` coverage)
     - `tests/integration/test_cli.py` (only line 745: `gemini` -> `antigravity` in `host docs` check; add no new tests to `test_cli.py`)
     - `tests/integration/test_closed_sets.py` (`ADAPTERS` and `PACKAGE` maps: `"antigravity": "AntigravityAdapter"`, `"antigravity": None`)
     - `tests/integration/test_provider_parsed_fixtures.py` (`("antigravity", AntigravityAdapter)` and `result.usage` token check)

### Scope out
- `clutch/antigravity.py` and `tests/unit/test_antigravity_plugin.py` (Antigravity IDE MCP plugin installer, unrelated to the `agy` CLI provider).
- `package.json`, `pnpm-workspace.yaml`, and `pnpm-lock.yaml` (workspace pnpm manifest and lockfile are outside this ticket's provider replacement).
- Historical records, changelog, frozen bootstrap plan, roadmap, and design plan documents under `tickets/` and `docs/`, as well as `tests/integration/test_ask_plan_drain.py` and `tests/integration/test_live_call_source.py`.

## Scope fence
- README.md
- clutch/__main__.py
- clutch/config.py
- clutch/docs/host-antigravity.md
- clutch/docs/host-contract.md
- clutch/docs/host-gemini.md
- clutch/docs/host-running.md
- clutch/evidence/antigravity.py
- clutch/evidence/gemini.py
- clutch/evidence/views.py
- clutch/gemini-readonly.json
- clutch/gemini-write.json
- clutch/observe.py
- clutch/providers.py
- clutch/training.py
- config.yaml
- docs/how-clutch-works.md
- tests/fixtures/evidence/antigravity/README.md
- tests/fixtures/evidence/antigravity/stream.jsonl
- tests/fixtures/evidence/gemini/README.md
- tests/fixtures/evidence/gemini/stream.jsonl
- tests/integration/test_antigravity_provider.py
- tests/integration/test_cli.py
- tests/integration/test_closed_sets.py
- tests/integration/test_evidence_antigravity_fixture.py
- tests/integration/test_evidence_gemini_fixture.py
- tests/integration/test_gemini_provider.py
- tests/integration/test_provider_parsed_fixtures.py
- tests/unit/test_antigravity_adapter.py
- tests/unit/test_callmeter_events.py
- tests/unit/test_docs_verb.py
- tests/unit/test_evidence_antigravity.py
- tests/unit/test_evidence_gemini.py
- tests/unit/test_evidence_views.py
- tests/unit/test_gemini_adapter.py
- tests/unit/test_init_config_verb.py
- tests/unit/test_install_verb.py
- tests/unit/test_main_host_group.py
- tests/unit/test_main_provider_group.py
- tests/unit/test_observe_extension_fields.py
- tests/unit/test_observe_provider_installs.py
- tests/unit/test_provider_parsed_events.py
- tests/unit/test_training_export_conflict.py
- tests/unit/test_training_ticket_kind.py
- tests/unit/test_update_config_verb.py
- tests/unit/test_watchdog_antigravity.py
- tests/unit/test_watchdog_gemini.py

## Acceptance criteria
1. `AntigravityAdapter` replaces `GeminiAdapter` in `ADAPTERS` (`ADAPTERS["antigravity"] is AntigravityAdapter`, `"gemini" not in ADAPTERS`), sets `PACKAGE = None`, `binary = "agy"`, `reports_cost = False`, `AUTH_ENV = None`, `AUTH_MARKERS`, and `LOGIN_ROAD`, and emits exact read-only (`--mode plan`) and write (`--mode auto --dangerously-skip-permissions`) argvs without `--print` or `--disable-slash-commands`, verified by `./dev.py test tests/unit/test_antigravity_adapter.py tests/integration/test_closed_sets.py` (rules out stale `gemini` adapter registration or wrong CLI flags).
2. `AntigravityAdapter.list_models` parses `agy models` output with `\r`-delimited spinner frames into `{model_id: model_id}` and surfaces non-zero exit errors cleanly, verified by `./dev.py test tests/unit/test_antigravity_adapter.py tests/unit/test_update_config_verb.py` (rules out leaving spinner bytes in model IDs or failing to report `agy models` errors).
3. `clutch/evidence/antigravity.py` (`antigravity-stream/1`) normalizes `init`, `step_update` (`user_input`, `tool` ACTIVE/DONE, `agent_response` delta/DONE), and `result` (SUCCESS/ERROR) events with `init.model`, `input_uncached`/`input_cache_read`/`output_total`/`output_reasoning`, and no `unknown` events on the captured fixture, and `CallMeter` + `parsed_from_events` consume them, verified by `./dev.py test tests/unit/test_evidence_antigravity.py tests/unit/test_provider_parsed_events.py tests/unit/test_watchdog_antigravity.py tests/integration/test_evidence_antigravity_fixture.py tests/integration/test_provider_parsed_fixtures.py` (rules out dropping `init.model`, emitting `message` with `text_blob=None`, or miscounting `cache_read_tokens`).
4. `Provider` config validation accepts `name: antigravity, kind: cli` without `package:` and still refuses missing `package:` for pnpm-based CLIs (`codex`), `ProviderLLM` runs `antigravity` read-only and write calls in memory and records `conversation_id` as `native_ids.session_id` and `init.model` as `model.served` while skipping `pnpm view` in preflight, and `config.yaml` loads cleanly with the declared `antigravity` provider, verified by `./dev.py test tests/integration/test_antigravity_provider.py tests/integration/test_providers.py` (rules out rejecting `antigravity` without `package:` or invoking `pnpm view None version`).
5. `clutch provider install` reports `antigravity` as `installed outside pnpm` and refuses `clutch provider install antigravity` with a road to `clutch/docs/host-antigravity.md`, `clutch host docs` lists `host-antigravity.md`, `clutch config init` omits `package:` for `antigravity`, `extension_fields` excludes `antigravity` from `providerInstalls`, and `clutch/training.py` assembles chunked `AntigravityAdapter` streams, verified by `./dev.py test tests/unit/test_install_verb.py tests/unit/test_main_provider_group.py tests/unit/test_init_config_verb.py tests/unit/test_docs_verb.py tests/unit/test_main_host_group.py tests/unit/test_observe_extension_fields.py tests/unit/test_observe_provider_installs.py tests/unit/test_evidence_views.py tests/unit/test_training_export_conflict.py tests/unit/test_training_ticket_kind.py tests/integration/test_cli.py` (rules out `installs None@latest`, broken `host-gemini.md` paths, or `KeyError` on `AntigravityAdapter` exports).
6. Old `gemini` provider files (`clutch/evidence/gemini.py`, `clutch/gemini-readonly.json`, `clutch/gemini-write.json`, `clutch/docs/host-gemini.md`, `tests/fixtures/evidence/gemini/*`, and the five `test_*gemini*` test modules) are deleted, `clutch/docs/host-antigravity.md` and updated docs (`README.md`, `clutch/docs/host-contract.md`, `clutch/docs/host-running.md`, `docs/how-clutch-works.md`) match the code, and the full unit, integration, lint, and format suites pass via `./dev.py test` and `uv run ruff check .` / `uv run ruff format --check .`.

## Verification
```
./dev.py test tests/unit/test_antigravity_adapter.py tests/unit/test_evidence_antigravity.py tests/unit/test_watchdog_antigravity.py tests/unit/test_callmeter_events.py tests/unit/test_provider_parsed_events.py tests/unit/test_evidence_views.py tests/unit/test_install_verb.py tests/unit/test_main_provider_group.py tests/unit/test_init_config_verb.py tests/unit/test_update_config_verb.py tests/unit/test_docs_verb.py tests/unit/test_main_host_group.py tests/unit/test_observe_extension_fields.py tests/unit/test_observe_provider_installs.py tests/unit/test_training_export_conflict.py tests/unit/test_training_ticket_kind.py tests/integration/test_antigravity_provider.py tests/integration/test_evidence_antigravity_fixture.py tests/integration/test_provider_parsed_fixtures.py tests/integration/test_closed_sets.py tests/integration/test_providers.py tests/integration/test_cli.py
uv run ruff check .
uv run ruff format --check .
```

## Definition of rejected
- Dual-path code: `GeminiAdapter`, `clutch/evidence/gemini.py`, `clutch/gemini-readonly.json`, `clutch/gemini-write.json`, or `clutch/docs/host-gemini.md` remains alongside `antigravity`.
- `AntigravityAdapter.argv` passes `--print` or `--disable-slash-commands`, or omits `--mode plan` for read-only calls or `--mode auto --dangerously-skip-permissions` for write calls.
- `clutch provider install antigravity`, `ProviderLLM.preflight()`, or `extension_fields()["providerInstalls"]` invokes or advertises `pnpm` for `antigravity`.
- `tests/integration/test_antigravity_provider.py` carries `pytest.mark.disk_io_skip` instead of using in-memory fakes.
- Any edit touches files outside `## Scope fence` (such as `clutch/antigravity.py` or `package.json`).

## Time budget
- expected: 20m
- stuck: 40m
- reason: Atomic replacement of `gemini` with `antigravity` across adapter, normalizer, CLI, config, docs, and pinned tests; splitting would either leave broken references or violate the no-dual-path rule.
