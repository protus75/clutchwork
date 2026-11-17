---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- cli-help-standard

## Context
- clutch/__main__.py::_command
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/providers.py::GeminiAdapter.list_models
- clutch/providers.py::suggest_config
- clutch/providers.py::ProviderLLM.preflight
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_main_box_group.py
- tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner

## On-demand
- README.md
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-contract.md
- clutch/docs/host-qwen.md
- clutch/docs/host-gemini.md
- tests/unit/test_install_verb.py
- tests/unit/test_probe_verb.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_host_onboarding_doc.py
- tests/integration/test_daemon_composition.py

## Goal / Why
Roadmap row 136 (`cli-group-provider`), group `provider`. `cli-help-standard` (row 129, merged at `e09d9e05`) added `_command` in `clutch/__main__.py` and the repo-local rules in `CLAUDE.md` section A: every command carries help to the standard through `_command`, every command lives under a top-level group, and a command change updates every document that describes it in the same change. Rows 130-134 (merged at `fcefb4f6`, `9de3d083`, `f2a246d7`, `084b9e48` and `8362970e`) built the `engine`, `ticket` and `box` groups that way, and row 135 (`cli-group-config`, confirmed at `720ec22b`) builds `config`. At HEAD (`720ec22b`) `install` and `probe` are still top-level verbs added with a bare `sub.add_parser` and a one-line `help=`, so `clutch help probe` prints no reads, writes, lock, exit codes or examples, and 35 lines of `README.md`, `clutch/__main__.py`, `clutch/providers.py`, the host guides, the plan-ticket-drain prompt, `docs/how-clutch-works.md` and `tests/` spell them `clutch install` or `clutch probe`, including the roads the drain's provider preflight prints (`-- run: clutch install codex`).

When this ticket is done:
- `clutch provider install [PROVIDER ...]` and `clutch provider probe [PROVIDER ...]` take the same arguments, print the same stdout lines apart from the road text, run the same processes (`pnpm add -D <package>@latest`, `<cli> --version`, one probe call per distinct model), write the same files, and exit with the same codes as `clutch install` and `clutch probe` do at HEAD. `provider install` still runs before config loads; `provider probe` still runs after the config load and before any checkout, lock or journal is built. The only visible differences are the help text, argparse's own usage and error lines, the refusal prefix (`clutch provider:`), the roads that name these commands, and the documents, prompt and tests that name them (all in Scope in).
- `clutch install` and `clutch probe` no longer parse: argparse exits 2 with an invalid-choice error. There is no alias (`CLAUDE.md` "No dual-path code").
- The `provider` group and its two subcommands carry help to the row 129 standard, so the parser walk in `tests/unit/test_main_help.py` checks them.
- Every caller names the new form in the same change: the install, init-config/config init and update-config/config update roads, the preflight's stale-CLI notice and failed-probe road, the gemini listing problem, the suggested config's header comment, the plan-ticket-drain prompt, `README.md`, the host guides (`host-running.md`, `host-contract.md`, `host-qwen.md`, `host-gemini.md`), `docs/how-clutch-works.md`, and the tests.

Why: the owner asked on 2026-11-17 for every command to live under a group with standard help (rows 129-140), so a person setting up a host finds the provider commands together under `clutch help provider`, each with what it reads, writes and locks and how it exits. `CLAUDE.md` "Guides name verbs, not command lines" also needs every guide and road to name the verb the CLI accepts. Rows 137-140 move the rest.

Transition, once: a host operator or agent following a setup guide, README (including the PyPI README of an earlier release), host-qwen or host-gemini guide from before this merge runs `clutch install <name>` or `clutch probe [<name>]` and gets exit 2 with an argparse invalid-choice error; nothing is installed or probed. Run `clutch provider install <name>` or `clutch provider probe [<name>]` instead, or `clutch help provider`. The same holds for a road already printed by an engine started before the merge: its provider preflight notice (`clutch: provider preflight notice: ... -- run: clutch install codex`, in the terminal or `<state_dir>/drain.out`) and its failed-probe refusal name the old form; run the `provider` form. An agent that rendered `clutch prompt plan-ticket-drain` before the merge holds `clutch probe`; re-render the prompt. No running engine needs a restart: drain, serve and `ticket review` run the preflight in-process and never spawn `clutch install` or `clutch probe`, no lock verb changes, and neither the snapshot nor the VS Code extension names these commands. No conduct block or `CORE_TEMPLATE` line names them (its "your clutch install" is a noun), so `clutch core` is not needed and no engine refuses a stale block. A `config.yaml` written by an earlier `init-config --write` keeps its header comment naming `clutch probe`; it is a comment and nothing reads it.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `install` and `probe` parsers. Add a group `provider` where the `install` parser was, the way `ticket`, `engine`, `box` and (after row 135) `config` are built: a one-line summary (for example "install and probe provider CLIs"), a `description` of what the group covers (for example "Install or report the provider CLIs clutch routes, and probe the declared providers' models."), an `Examples:` epilog whose `clutch provider ...` line parses, and `argparse.RawDescriptionHelpFormatter`. Its subparsers take `dest="provider_verb"` and `required=True`. Its two subcommands are built with `_command`, with every field, and each keeps its positional `providers` (`nargs="*"`). Read each fact from its `docs/how-clutch-works.md` section 2.1 row and its handler before writing it:
  - `install`. Facts: installs the named provider CLIs into the host project as pnpm dev dependencies (`pnpm add -D <package>@latest`), then reports each one's package, location and version; with no names, installs nothing and reports every adapter. Reads each provider CLI's `--version` output from the project's `node_modules/.bin` or `PATH`; no config. Writes, with names, `package.json`, `pnpm-lock.yaml` and `node_modules/` through pnpm; with no names, nothing. Lock: none. Exits 0 when installed or reported, 2 on refusal (unknown provider name, pnpm not on `PATH`, or a failed `pnpm add`). Examples `clutch provider install` and `clutch provider install claude codex`.
  - `probe`. Facts: sends one probe call to each distinct model of the named declared providers, or of every declared provider, and prints each model's `ok` or its error. Reads config and the declared provider CLIs. Writes nothing it keeps (each call's scratch prompt under `<state_dir>/evidence/scratch/` is removed after it). Lock: none. Exits 0 when every probe answers, 1 when a probe or provider setup fails, 2 for an undeclared provider name or on refusal. Examples `clutch provider probe` and `clutch provider probe claude`.
- Dispatch: `handlers` drops the `"install"` and `"probe"` entries and gains `"provider"`, dispatching by `args.provider_verb` to the unchanged `handle_install` and `handle_probe`. `provider install` still runs before config loads: `"install"` leaves the pre-config verb set and `or (args.verb == "provider" and args.provider_verb == "install")` joins that condition's other clauses (`box issue`, `ticket new`, and after row 135 `config init|migrate`). `provider probe` still runs right after `load_config`: in the post-config set, `"probe"` becomes `"provider"` (only `provider probe` reaches that line).
- Refusals keep going through `_fail(args.verb, ...)`, so a provider refusal prints `clutch provider: <message> -- <road>`, as `ticket`, `engine`, `box` and `config` refusals print their group. `handle_probe` keeps its name and its own unprefixed stderr line `unknown providers: ...; declared providers: ...` (exit 2), which `tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner` names; no `print(..., file=sys.stderr)` is added.
- Roads: `handle_init_config`'s `run: clutch install {'|'.join(sorted(ADAPTERS))}` becomes `run: clutch provider install ...`; `handle_install`'s two `then rerun clutch install` become `then rerun clutch provider install`, and its absent-CLI suffix ` -- run: clutch install {name}` becomes ` -- run: clutch provider install {name}`; `handle_update_config`'s `run: clutch install {name}` becomes `run: clutch provider install {name}`. `ruff format` then splits `handle_install`'s status `print` argument over two lines (it passes 200 columns); no other line changes.

In, `clutch/providers.py`, string literals only:
- `GeminiAdapter.list_models`: `... and run clutch provider probe gemini`.
- `suggest_config`'s header comment: only its last words `clutch probe.` become `clutch provider probe.`; the rest of the line keeps main's form (`clutch config init` once row 135 merged, `clutch init-config` before).
- `ProviderLLM.preflight`: the stale-CLI notice's ` -- run: clutch provider install {adapter.provider.name}` and the failed-probe problem's ` -- run: clutch provider install {provider}, or route a model this login serves in config.yaml`.

In, prompt: `clutch/specs/ask/plan-ticket-drain.md` (no `version`): "`clutch provider probe` must reach every declared provider."

In, documents. Only references to the two commands change:
- `README.md`: the Install paragraph's `` `uv run clutch provider install claude codex` ``; "Set up a host"'s `` `uv run clutch provider probe` ``; the `# Setup` lines `uv run clutch provider install  # install provider CLIs into the host` and `uv run clutch provider probe  # probe declared providers and models`.
- `clutch/docs/host-running.md`: the intro's "for example, `clutch provider install` reports provider CLIs", and the first cells of the `probe` and `install` rows become `provider probe` and `provider install`, in place, text unchanged.
- `clutch/docs/host-contract.md`: Install's `` `uv run clutch provider install claude codex` `` and `` `uv run clutch provider install` with no names ``, and "which `clutch doctor` and `clutch provider probe` check"; Onboarding step 2 `` Use `clutch provider install` `` and step 5 `` `clutch doctor` and `clutch provider probe` ``.
- `clutch/docs/host-qwen.md`: `` `clutch provider probe qwen` cannot connect ``, `` Run `clutch provider install qwen` `` and `` Run `clutch provider probe qwen` ``.
- `clutch/docs/host-gemini.md`: `` Run `clutch provider install gemini` ``, the model paragraph's "Confirm every choice with `clutch provider probe gemini`", and `` Run `clutch provider probe gemini` ``.
- `docs/how-clutch-works.md`: the section 2.1 rows begin `` `provider probe [PROVIDER...]` `` and `` `provider install [PROVIDER...]` ``, in place, text unchanged; section 8.1's bullet `` (`clutch provider install <provider>`, ... `` and "the preflight's update road is `clutch provider install <provider>`".

In, tests. Only the argv (`"provider"` before the subcommand) and the pinned text named here change:
- New `tests/unit/test_main_provider_group.py` (criteria 1-4). It builds `_parser()` in memory and calls `main(..., cwd=tmp_path, env={})` in an empty `tmp_path`, replacing `clutch.__main__.SubprocessExec` with a fake whose `run` raises `ExecutableNotFound`. It reads no repo file and starts no process, and it runs the new parser and dispatch lines of `clutch/__main__.py` (coverage floor 13).
- Argv only: `tests/unit/test_install_verb.py` (`cli.main(["provider", "install", *args], ...)`) and `tests/unit/test_probe_verb.py` (its three `cli.main(["provider", "probe", ...], ...)` calls).
- Pinned text: `tests/unit/test_install_verb.py` (`-- run: clutch provider install qwen`), `tests/unit/test_init_config_verb.py` (`run: clutch provider install claude|codex|gemini|qwen`), `tests/unit/test_update_config_verb.py` (`run: clutch provider install claude`), `tests/unit/test_gemini_adapter.py` (`clutch provider probe gemini`), `tests/integration/test_providers.py` (`-- run: clutch provider install codex`), `tests/integration/test_daemon_composition.py` (`-- run: clutch provider install `; a do-not-grow file, fenced only for that one assertion, and nothing is added to it), `tests/integration/test_ask_plan_drain.py` (the `clutch provider probe` phrase and its place in the `text.index` order), and `tests/integration/test_host_onboarding_doc.py` (`"clutch provider install"` and `"clutch provider probe"` in the ordered `verbs` tuple; its other entries keep main's form).
- Test file and function names (`test_install_verb.py`, `test_probe_verb.py`, `test_install`, `test_probe`) stay. A scratch prototype built on row 135's prototype at `720ec22b` touched exactly the 19 fenced files; with the test edits 917 unit and 3,408 integration tests passed, the one failure being the base flake named in criterion 13, and `ruff check`, `ruff format --check` and the unit coverage gate passed. The same change applied to `720ec22b` without row 135 also touched exactly these 19 files and passed 914 unit and 3,408 integration tests, with the same one flake.

Merge order. Row 135 (`cli-group-config`, confirmed and queued at `720ec22b`, P1, authored before this ticket) also fences `clutch/__main__.py`, `clutch/providers.py`, `clutch/docs/host-running.md`, `clutch/docs/host-contract.md`, `clutch/docs/host-gemini.md`, `docs/how-clutch-works.md`, `README.md`, `tests/unit/test_init_config_verb.py`, `tests/unit/test_update_config_verb.py` and `tests/integration/test_host_onboarding_doc.py`, and edits lines next to or shared with this ticket's: the parser block (its `config` group replaces the `migrate-config` parser after `probe`), the `handlers` entries, the pre-config condition, the post-config set, `suggest_config`'s header line, host-contract's "`uv run clutch config init --write` then creates ..." sentence, host-gemini's model paragraph, the README `# Setup` block, the run-guide rows, and the onboarding `verbs` tuple. In each, this ticket changes only the words for `install` and `probe`; every other word keeps the form main has when it runs, and the counts in the criteria are the same in either order. Expected order, row 135 first (both P1, row 135 older): the pre-config set goes from `{"docs", "install", "covgate", "doctor"}` to `{"docs", "covgate", "doctor"}`, the post-config set from `{"config", "probe", "core", "prompt"}` to `{"config", "provider", "core", "prompt"}`, the header reads `# Suggested by clutch config init ... then run clutch doctor and clutch provider probe.`, and the tuple begins `("clutch provider install", "clutch config init", "clutch doctor", "clutch provider probe", ...)`. If this ticket runs first: the sets become `{"docs", "init-config", "migrate-config", "covgate", "doctor"}` and `{"update-config", "provider", "core", "prompt"}`, the header and the tuple keep `init-config`, and row 135 then starts from this merged code; its own edits change only the config words, its argv lines in the two config verb tests differ from this ticket's pinned-road lines, and its onboarding test still finds `clutch config init` between `clutch provider install` and `clutch doctor`. `plan-status-sweep-030` (running) fences four plans under `docs/`, among them the gemini graphics refactor plan, which this ticket leaves alone. A later row (137-140) starts from this ticket's merged code.

Out:
- An alias of any kind for the old names; every other command, including `config` (row 135), `doctor` and `core` (row 138).
- `clutch/hostfiles.py` `CORE_TEMPLATE`, the managed blocks, `CLAUDE.md`, `AGENTS.md` and `hosts/fixture/CLAUDE.md` (their "your clutch install" is a noun), and `clutch/author.py`'s "The clutch install owns these specs" (a noun): `clutch core` is not run.
- `clutch/help.py`, `clutch/observe.py` and `vscode-clutchwork/`: no help topic, `COMMANDS` entry or extension argv names `install` or `probe` (`git grep -nwE 'install|probe' -- clutch/help.py clutch/observe.py vscode-clutchwork/extension.js vscode-clutchwork/package.json` prints nothing at HEAD), so none is added.
- Prose naming probing or installing, not the command: "lock probe", "Preflight probes every routed model", "failed its probe", `PROBE_PROMPT`, the `preflight` surface, `INSTALL_TIMEOUT_S`, and "install clutch" links.
- Python names: `handle_install`, `handle_probe`, `cli_status`, `suggest_config`, `ProviderLLM.preflight`, and every test name.
- `CLUTCH_PLAN.md` (frozen), `docs/roadmap.md`, the plans under `docs/` (the gemini graphics refactor plan names `clutch install gemini` and `clutch probe gemini` as design history), `dev.py`, and `tickets/`.
- `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/unit/test_readme.py`, `tests/unit/test_help.py`, `tests/integration/test_help.py` and `tests/integration/test_main_verb_groups.py` stay unedited and passing; they already walk the parser and groups, match run-guide rows to parser paths, check the first word of each `uv run clutch` line, and list the stderr print owners.

## Scope fence
- clutch/__main__.py
- clutch/providers.py
- clutch/specs/ask/plan-ticket-drain.md
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- clutch/docs/host-qwen.md
- clutch/docs/host-gemini.md
- docs/how-clutch-works.md
- README.md
- tests/unit/test_main_provider_group.py
- tests/unit/test_install_verb.py
- tests/unit/test_probe_verb.py
- tests/unit/test_init_config_verb.py
- tests/unit/test_update_config_verb.py
- tests/unit/test_gemini_adapter.py
- tests/integration/test_providers.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_ask_plan_drain.py
- tests/integration/test_host_onboarding_doc.py

## Acceptance criteria
1. `tests/unit/test_main_provider_group.py::test_provider_group_parses`: `_parser().parse_args(["provider", "install"])` gives `verb == "provider"`, `provider_verb == "install"` and `providers == []`; `["provider", "install", "claude", "codex"]` gives `providers == ["claude", "codex"]`; `["provider", "probe"]` gives `provider_verb == "probe"` and `providers == []`; `["provider", "probe", "claude"]` gives `providers == ["claude"]`; and `["provider"]`, `["provider", "install", "--write"]` and `["provider", "probe", "--all"]` raise `SystemExit(2)`. Ruled out: a changed arity or an added option.
2. `tests/unit/test_main_provider_group.py::test_old_names_refuse`: neither `install` nor `probe` is a choice of the top-level subparsers, each is a choice of the `provider` group, and `_parser().parse_args([name])` raises `SystemExit(2)` for each. Ruled out: an alias, hidden parser or argv rewrite that keeps an old name working.
3. `tests/unit/test_main_provider_group.py::test_install_needs_no_config`: in an empty `tmp_path` (no `config.yaml`), with `clutch.__main__.SubprocessExec` replaced by a fake whose `run` raises `ExecutableNotFound`, `main(["provider", "install"], cwd=tmp_path, env={})` returns 0, stderr is empty, the stdout lines other than the `ollama:` line equal `f"{name}: absent, package {adapter.PACKAGE} -- run: clutch provider install {name}"` for each `name, adapter` of `clutch.providers.ADAPTERS` in order, and `tmp_path` is still empty. Ruled out: `provider install` dispatched after the config load, which returns 2 with a `clutch provider:` line containing `config file not found`, and an absent-CLI road naming `clutch install`.
4. `tests/unit/test_main_provider_group.py::test_refusals_name_group`: in an empty `tmp_path`, with the same fake, `main` prints nothing on stdout, returns 2 and prints exactly one stderr line starting `clutch provider: ` for each of `["provider", "probe"]`, whose line contains `config file not found`, and `["provider", "install", "llama"]`, whose line is `clutch provider: unknown provider 'llama' -- name one of claude, codex, gemini, qwen` (built from `sorted(ADAPTERS)`); `tmp_path` is still empty afterwards. Ruled out: the old `clutch probe:` or `clutch install:` prefix, a `clutch provider probe:` prefix, and an uncaught exception.
5. `./dev.py test tests/unit/test_main_help.py tests/unit/test_readme.py` exits 0 with both files unchanged. The parser walk checks the `provider` group and its two subcommands for a description and examples that parse, the top-level help lists `provider install` and `provider probe` once each with their summaries, and every `uv run clutch` line of `README.md` names a top-level command. `uv run clutch help provider install` prints `usage: clutch provider install`, what it does, then `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines that agree with Scope in (no config; `package.json`, `pnpm-lock.yaml` and `node_modules/` with names; no lock; exits 0 when installed or reported, 2 on refusal), its `providers` argument, then `Examples:` with a `clutch provider install` line. `uv run clutch help provider probe` prints the same parts with the facts in Scope in (exits 0, 1 or 2), and `uv run clutch help provider` lists the two subcommands and its examples.
6. `./dev.py test tests/unit/test_host_running.py` exits 0 with that file unchanged, and `grep -cE '^\| .provider (install|probe). \|' clutch/docs/host-running.md` prints `2`. Its `test_verb_table_matches_parser` fails while a row still names a removed top-level command or the `provider` group lacks a row for one of its subcommands.
7. `grep -cE '^\| .provider (install|probe) \[PROVIDER\.\.\.\]. \|' docs/how-clutch-works.md` prints `2`, and `grep -cE '^\| .(install|probe)( [^|]*)?. \|' docs/how-clutch-works.md clutch/docs/host-running.md` prints `0` for each file (at HEAD, `2` each).
8. `git grep -nE 'clutch (install|probe)([^a-z-]|$)' -- README.md clutch/__main__.py clutch/providers.py clutch/docs clutch/specs docs/how-clutch-works.md tests` prints nothing; at HEAD `720ec22b` it prints 35 lines, before or after row 135 merges. ``git grep -nE '`(install|probe)( [^`]*)?`' -- README.md 'clutch/docs/*.md' docs/how-clutch-works.md`` prints nothing (at HEAD, 4 lines). Ruled out: a reference left in a road, the preflight, the suggested config's header, the gemini listing problem, the prompt, a host guide, a document or a test.
9. `./dev.py test tests/unit/test_install_verb.py tests/unit/test_probe_verb.py tests/unit/test_init_config_verb.py tests/unit/test_update_config_verb.py tests/unit/test_gemini_adapter.py` exits 0 with only the argv and pinned text named in Scope in changed: `provider install` with no names still runs no `pnpm`, with a name runs `["pnpm", "add", "-D", "@openai/codex@latest"]` with the same `cwd`, `env` and `timeout`, refuses an unknown name before any process, and never loads config or builds a lock or journal; `provider probe` still exits 0, 1 and 2 as before and never builds a lock or journal; the no-CLI and missing-CLI roads of the config commands name `clutch provider install`; the gemini listing problem names `clutch provider probe gemini`.
10. `./dev.py test tests/integration/test_providers.py tests/integration/test_daemon_composition.py` exits 0: the preflight's stale-CLI notice contains `-- run: clutch provider install codex` and no `pnpm add`, and a failed-probe preflight refusal contains `-- run: clutch provider install `. Nothing is added to `tests/integration/test_daemon_composition.py`, and only its one pinned road changes. Ruled out: a preflight road naming the removed `clutch install`, which an operator following it would see exit 2.
11. `./dev.py test tests/integration/test_ask_plan_drain.py tests/integration/test_host_onboarding_doc.py` exits 0: the rendered plan-ticket-drain prompt contains `clutch provider probe` after `clutch doctor` and before `clutch prompt drain-loop`, and `test_prompts_name_only_existing_verbs` passes unedited (it fails while a rendered prompt names `` `clutch probe``); the host contract's onboarding steps name `clutch provider install` before the config step and `clutch provider probe` after `clutch doctor` and before `clutch core`.
12. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_main_verb_groups.py` exits 0 with those files unchanged; `test_stderr_prints_have_one_prefixed_owner` still finds the owners `_fail`, `handle_issue` and `handle_probe`.
13. `./dev.py test` exits 0; Check's `unit` and `integration` mechanical checks in `config.yaml` run both full suites. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is the known base flake (box-000706-10233120) and is verified on the base commit, not chased.

## Verification
```
./dev.py test tests/unit/test_main_provider_group.py tests/unit/test_main_help.py tests/unit/test_readme.py tests/unit/test_host_running.py tests/unit/test_help.py tests/unit/test_install_verb.py tests/unit/test_probe_verb.py tests/unit/test_init_config_verb.py tests/unit/test_update_config_verb.py tests/unit/test_gemini_adapter.py
./dev.py test tests/integration/test_providers.py tests/integration/test_daemon_composition.py tests/integration/test_ask_plan_drain.py tests/integration/test_host_onboarding_doc.py tests/integration/test_help.py tests/integration/test_main_verb_groups.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- `install` or `probe` still runs as a top-level command through an alias, a hidden or suppressed parser, or argv rewriting in `main`.
- An argument, default, stdout line, process run, written file or exit code of the two commands changes, other than the help text, argparse's usage and error lines, the refusal prefix, and the roads named in Scope in.
- `provider install` needs a loadable config, or `provider probe` runs before config loads or builds a checkout, lock or journal.
- `handle_install` or `handle_probe` is renamed, or `handle_probe`'s `unknown providers:` stderr line changes.
- A file outside the fence changes, including `clutch/hostfiles.py`, `CLAUDE.md`, `AGENTS.md`, `hosts/fixture/CLAUDE.md`, `clutch/help.py`, `clutch/observe.py`, `clutch/author.py`, `vscode-clutchwork/` or a plan under `docs/`.
- A test is added to a do-not-grow file, or an existing assertion is dropped, loosened or changed beyond the argv and pinned text named in Scope in.
- Another command is moved or renamed.

## Time budget
- expected: 20m
- stuck: 40m
