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
- clutch/config.py::migrate_config
- clutch/config.py::_check_schema_version
- clutch/providers.py::suggest_config
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_main_ticket_verdicts.py

## On-demand
- README.md
- clutch/docs/host-contract.md
- clutch/docs/host-gemini.md
- tests/unit/test_init_config_verb.py
- tests/unit/test_update_config_verb.py
- tests/integration/test_config.py
- tests/integration/test_cli.py
- tests/integration/test_host_onboarding_doc.py

## Goal / Why
Roadmap row 135 (`cli-group-config`), group `config`. `cli-help-standard` (row 129, merged at `e09d9e05`) added `_command` in `clutch/__main__.py` and the repo-local rules in `CLAUDE.md` section A: every command carries help to the standard through `_command`, every command lives under a top-level group, and a command change updates every document that describes it in the same change. Rows 130-134 (merged at `fcefb4f6`, `f2a246d7`, `9de3d083`, `084b9e48` and `8362970e`) built the `engine`, `ticket` and `box` groups that way. At HEAD (`e23b1842`) `init-config`, `update-config` and `migrate-config` are still top-level verbs added with a bare `sub.add_parser` and a one-line `help=`, so `clutch help migrate-config` prints no reads, writes, lock, exit codes or examples, and 42 lines of `README.md`, `clutch/`, `docs/how-clutch-works.md` and `tests/` spell them.

When this ticket is done:
- `clutch config init [--write]`, `clutch config update` and `clutch config migrate` take the same arguments, print the same stdout, write the same files, and exit with the same codes as `clutch init-config`, `clutch update-config` and `clutch migrate-config` do at HEAD. `config init` and `config migrate` still run before config loads, and `config migrate` still honors `--config PATH` before the command. The only visible differences are the help text, argparse's own usage and error lines, the refusal prefix (`clutch config:`), the config loader's roads that name `migrate-config`, the suggested config's header comment, and the documents that name these commands (all in Scope in).
- `clutch init-config`, `clutch update-config` and `clutch migrate-config` no longer parse: argparse exits 2 with an invalid-choice error. There is no alias (`CLAUDE.md` "No dual-path code"). The subcommands drop the `-config` suffix: `init`, `update`, `migrate`.
- The `config` group and its three subcommands carry help to the row 129 standard, so the parser walk in `tests/unit/test_main_help.py` checks them.
- Every caller names the new form in the same change: the config loader's roads, the suggested config's header, `README.md`, the host guides (`host-running.md`, `host-contract.md`, `host-gemini.md`), `docs/how-clutch-works.md`, and the tests.

Why: the owner asked on 2026-11-17 for every command to live under a group with standard help (rows 129-140), so a person or agent setting up a host finds the config commands together under `clutch help config`, each with what it reads, writes and locks and how it exits. Rows 136-140 move the rest.

Transition, once: a host operator or agent following a setup guide, README or host guide from before this merge (including the PyPI README of an earlier release) runs `clutch init-config`, `clutch update-config` or `clutch migrate-config` and gets exit 2 with an argparse invalid-choice error; nothing is printed to stdout or written. Run `clutch config init`, `clutch config update` or `clutch config migrate` instead, or `clutch help config`. No running engine needs a restart: drain and serve never run these commands, no lock verb changes, and neither the snapshot nor the VS Code extension names them. The roads that point at migration (`run clutch config migrate`) come from the installed code, so an operator always sees the form their install accepts. A `config.yaml` written by an earlier `init-config --write` keeps its `# Suggested by clutch init-config ...` comment; it is a comment and nothing reads it. No prompt spec, conduct block or `CORE_TEMPLATE` line names these commands, so no rendered prompt or conduct file goes stale.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `init-config`, `update-config` and `migrate-config` parsers. Add a group `config` where the `migrate-config` parser was, before the `box` group, the way `ticket`, `engine` and `box` are built: a one-line summary (for example "create, check and migrate config.yaml"), a `description` of what the group covers (for example "Suggest a config.yaml from the provider CLIs found, compare its model names with what providers serve, and migrate an older config schema."), an `Examples:` epilog whose `clutch config ...` line parses, and `argparse.RawDescriptionHelpFormatter`. Its subparsers take `dest="config_verb"` and `required=True`; never `dest="config"`, which would overwrite the top-level `--config` path in the namespace. Its three subcommands are built with `_command`, with every field, and keep their arguments exactly. Read each fact from its `docs/how-clutch-works.md` section 2.1 row and its handler before writing it:
  - `init`, option `--write` (`store_true`). Facts: prints a suggested `config.yaml` built from the provider CLIs found and the model names they serve, validated with the real loader; `--write` creates `config.yaml` at the checkout root when none exists. Reads the provider CLIs in the project or on `PATH` and their model listings (`claude` resolves each alias with one small model call); no config is needed. Writes nothing; with `--write`, `config.yaml`. Lock: none. Exits 0 when printed or written, 2 on refusal (no provider CLI found, a suggestion the loader refuses, or `config.yaml` already exists with `--write`). Examples `clutch config init` and `clutch config init --write`.
  - `update`, no arguments. Facts: lists the model names each declared provider serves and says which configured names are current, replaced, not served or unverified. Reads config and each declared provider CLI's model listing. Writes nothing. Lock: none. Exits 0 when every configured name is current, 1 when a suggestion was printed, 2 on refusal. Example `clutch config update`.
  - `migrate`, no arguments. Facts: validates the selected config and migrates `schema_version: 0` to the current schema in place; a current config is a byte-identical no-op. Reads the selected config (`--config` before the command, else `config.yaml` at the checkout root). Writes the original bytes to `<config>.bak`, then the migrated config; nothing for a current config. Lock: none. Exits 0 when migrated or already current, 2 on refusal. Examples `clutch config migrate` and `clutch --config host.yaml config migrate`.
- Dispatch: `handlers` drops the `"init-config"`, `"update-config"` and `"migrate-config"` entries and gains `"config"`, dispatching by `args.config_verb` to the unchanged `handle_init_config`, `handle_update_config` and `handle_migrate_config`. `config init` and `config migrate` still run before config loads: in the pre-config condition, `"init-config"` and `"migrate-config"` leave the set and `or (args.verb == "config" and args.config_verb in {"init", "migrate"})` joins the clauses for `box issue` and `ticket new`. `config update` still runs after `load_config` and before the checkout is built: in the `{"update-config", "probe", "core", "prompt"}` set, `"update-config"` becomes `"config"` (only `config update` reaches that line). The handlers' own refusals and roads (`no provider CLI found`, `config.yaml already exists`, `run: clutch install <name>`) are unchanged.
- Refusals keep going through `_fail(args.verb, ...)`, so a config refusal prints `clutch config: <message>`, as `ticket`, `engine` and `box` refusals print their group. No `print(..., file=sys.stderr)` is added (`tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner`).

In, other code:
- `clutch/config.py`: the six `retry migrate-config` roads in `migrate_config` become `retry config migrate`, and `_check_schema_version`'s older-version road becomes ``run `clutch config migrate` to migrate it (...)``, the parenthesis unchanged. Every other message stays. `migrate_config`, `load_config` and `_check_schema_version` keep their names and behavior.
- `clutch/providers.py::suggest_config`: the first suggested line becomes `# Suggested by clutch config init from the provider CLIs found; edit models, checks and routing, then run clutch doctor and clutch probe.`. Every other suggested line stays.

In, documents. Only references to the command change:
- `README.md`: the Install paragraph's `` `uv run clutch config init --write` ``, and the `# Setup` lines `uv run clutch config init  # print a suggested config.yaml` and `uv run clutch config update  # list current model names per provider`, comments unchanged.
- `clutch/docs/host-running.md`: the first cells of the `init-config`, `update-config` and `migrate-config` rows become `config init`, `config update` and `config migrate`, in place, text unchanged.
- `clutch/docs/host-contract.md`: Install's `` `uv run clutch config init --write` ``; Copyable configuration's `` `clutch config init` prints the same shape ``; Onboarding step 3 `` Use `clutch config init` ``; Version migration's two `` `clutch config migrate` `` and "retry config migrate".
- `clutch/docs/host-gemini.md`: `` `clutch config init` writes that line `` and `` `clutch config update` lists no gemini models ``.
- `docs/how-clutch-works.md`: the section 2.1 rows begin `` `config update` ``, `` `config init [--write]` `` and `` `config migrate` ``, in place, text unchanged; section 8.1's model-names paragraph `` `clutch config update` prints listings ``; section 11 `` `clutch config init` prints a suggestion ``.

In, tests. Only the argv (`"config"` before the subcommand) and the pinned text named here change:
- New `tests/unit/test_main_config_group.py` (criteria 1-3). It builds `_parser()` in memory and calls `main(..., cwd=tmp_path, env={})` in an empty `tmp_path`, replacing `clutch.__main__.SubprocessExec` with a fake whose `run` raises `ExecutableNotFound` where `config init` runs. It reads no repo file and starts no process, and it runs the new parser and dispatch lines of `clutch/__main__.py` (coverage floor 13).
- Argv only: `tests/unit/test_init_config_verb.py` (`cli.main(["config", "init", *args], ...)`), `tests/unit/test_update_config_verb.py` (the two `cli.main(["config", "update"], ...)` calls), and `tests/integration/test_cli.py::test_migrate_config_before_load` (`+ ["config", "migrate"]`). `tests/integration/test_cli.py` is a do-not-grow file, fenced only for that line; nothing is added to it.
- Pinned text: `tests/integration/test_config.py` (`"clutch config migrate" in str(err)` in `test_older_schema_version_is_refused_naming_migrate_config`, and `match="repair.*retry config migrate"` in `test_migrate_config_validates_before_write`), and `tests/integration/test_host_onboarding_doc.py` (`"clutch config init"` in the ordered `verbs` tuple).
- Test function and file names that spell the Python function or the old verb with underscores (`test_migrate_config_*`, `test_init_config_verb.py`, `test_update_config_verb.py`) stay. A scratch prototype of the code change without the test edits failed 6 unit tests in the two verb test files and 8 integration tests in `test_config.py`, `test_cli.py` and `test_host_onboarding_doc.py`; with them, 913 unit and 3,408 integration tests passed at `e23b1842`, the one failure being the base flake named in criterion 11, and `ruff check`, `ruff format --check` and the unit coverage gate passed. The prototype touched exactly the 14 fenced files.

Merge order. No confirmed, unmerged ticket fences a file this ticket fences: `plan-status-sweep-030` (running) fences only four plans under `docs/`. Row 134 (`cli-group-box`) merged at `8362970e` and left the lines this ticket edits next to its own: its `box` group follows the `migrate-config` parser, its `"box"` handler entry sits among the config entries, and it split the pre-config condition into one clause per line. This ticket changes only the words for the config commands there; every other word keeps the form main has when it runs. Rows 136-140 (`install`, `probe`, `doctor`, `core` and the rest) start from this ticket's merged code; row 136 will edit the same pre-config set and the `install` and `probe` parsers beside the new group.

Out:
- An alias of any kind for the old names; and every other command, including `install` and `probe` (row 136, so `run: clutch install <name>` roads stay), `doctor` and `core` (row 138).
- `clutch/hostfiles.py` `CORE_TEMPLATE`, the managed blocks, `CLAUDE.md`, `AGENTS.md`, `hosts/fixture/CLAUDE.md`, `clutch/specs/`, `clutch/help.py`, `clutch/observe.py`, `clutch/doctor.py`, `vscode-clutchwork/` and `tests/harness/`: `git grep -nE '(init|update|migrate)-config' -- clutch/hostfiles.py CLAUDE.md AGENTS.md hosts clutch/specs clutch/help.py clutch/observe.py clutch/doctor.py vscode-clutchwork tests/harness` prints nothing at HEAD, so `clutch core` is not run and no help topic or snapshot argv changes.
- Python names: the handlers `handle_init_config`, `handle_update_config` and `handle_migrate_config`, `clutch.config.migrate_config`, `clutch.providers.suggest_config`, and every test name.
- `CLUTCH_PLAN.md` (frozen), `docs/roadmap.md`, and `tickets/` (historical tickets such as `init-config-verb` and `migrate-config`).
- `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`, `tests/unit/test_readme.py`, `tests/unit/test_help.py`, `tests/integration/test_help.py` and `tests/integration/test_main_verb_groups.py` stay unedited and passing; they already walk the parser and groups, match run-guide rows to parser paths, and check the first word of each `uv run clutch` line.

## Scope fence
- clutch/__main__.py
- clutch/config.py
- clutch/providers.py
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- clutch/docs/host-gemini.md
- docs/how-clutch-works.md
- README.md
- tests/unit/test_main_config_group.py
- tests/unit/test_init_config_verb.py
- tests/unit/test_update_config_verb.py
- tests/integration/test_cli.py
- tests/integration/test_config.py
- tests/integration/test_host_onboarding_doc.py

## Acceptance criteria
1. `tests/unit/test_main_config_group.py::test_config_group_parses`: `_parser().parse_args(["config", "init"])` gives `verb == "config"`, `config_verb == "init"`, `write is False` and `config is None`; `["config", "init", "--write"]` gives `write is True`; `["config", "update"]` gives `config_verb == "update"`; `["--config", "host.yaml", "config", "migrate"]` gives `config_verb == "migrate"` and `config == Path("host.yaml")`; and `["config"]`, `["config", "update", "--write"]` and `["config", "migrate", "--write"]` raise `SystemExit(2)`. Ruled out: a changed arity or option, and a group subparser `dest="config"`, under which `args.config` becomes the subcommand name and `config migrate` loses the `--config` path.
2. `tests/unit/test_main_config_group.py::test_old_names_refuse`: none of `init-config`, `update-config` and `migrate-config` is a choice of the top-level subparsers, `init`, `update` and `migrate` are choices of the `config` group, and `_parser().parse_args([old])` raises `SystemExit(2)` for each old name. Ruled out: an alias, hidden parser or argv rewrite that keeps an old name working, and a subcommand that keeps the `-config` suffix.
3. `tests/unit/test_main_config_group.py::test_refusals_name_group`: in an empty `tmp_path` (no `config.yaml`), `main(argv, cwd=tmp_path, env={})` returns 2, prints nothing on stdout, and prints one stderr line starting `clutch config: ` for each of: `["config", "update"]`, whose line contains `config file not found`; `["config", "migrate"]`, whose line contains `cannot read config file` and not `config file not found`; and, with `clutch.__main__.SubprocessExec` replaced by a fake whose `run` raises `ExecutableNotFound`, `["config", "init"]`, whose line starts `clutch config: no provider CLI found -- `. `tmp_path` is still empty afterwards. Ruled out: the old `clutch init-config:`, `clutch update-config:` or `clutch migrate-config:` prefix, and `config init` or `config migrate` dispatched after the config load, which refuses with `config file not found` instead.
4. `./dev.py test tests/unit/test_main_help.py tests/unit/test_readme.py` exits 0 with both files unchanged. The parser walk checks the `config` group and its three subcommands for a description and examples that parse, the top-level help lists `config init`, `config update` and `config migrate` once each with their summaries, and every `uv run clutch` line of `README.md` names a top-level command. `uv run clutch help config migrate` prints `usage: clutch config migrate`, what it does, then `Reads:`, `Writes:`, `Lock:` and `Exit codes:` lines that agree with Scope in (the selected config; `<config>.bak` then the config; no lock; exits 0 when migrated or already current, 2 on refusal), then `Examples:` with a `clutch config migrate` line. `uv run clutch help config init` and `uv run clutch help config update` print the same parts with the facts in Scope in (`init` lists `--write`), and `uv run clutch help config` lists the three subcommands and its examples.
5. `./dev.py test tests/unit/test_host_running.py` exits 0 with that file unchanged, and `grep -cE '^\| .config (init|update|migrate). \|' clutch/docs/host-running.md` prints `3`. Its `test_verb_table_matches_parser` fails while a row still names a removed top-level command or the `config` group lacks a row for one of its subcommands.
6. `grep -cE '^\| .config (init \[--write\]|update|migrate). \|' docs/how-clutch-works.md` prints `3`, and `grep -cE '^\| .(init|update|migrate)-config' docs/how-clutch-works.md clutch/docs/host-running.md` prints `0` for each file (at HEAD, `3` each).
7. `git grep -nE '(init|update|migrate)-config' -- README.md clutch docs/how-clutch-works.md tests ':!tests/unit/test_main_config_group.py'` prints nothing; at HEAD `e23b1842` the same grep prints 42 lines. Ruled out: a reference left in a document, host guide, loader road, the suggested config's header, or a test.
8. `./dev.py test tests/unit/test_init_config_verb.py tests/unit/test_update_config_verb.py` exits 0 with only the argv changed: `config init` still validates before printing, publishes only with `--write`, refuses an existing `config.yaml`, and never loads config, takes the lock or opens the journal; `config update` still exits 1 when a suggestion was printed and 0 when every name is current.
9. `./dev.py test tests/integration/test_config.py tests/integration/test_cli.py tests/integration/test_host_onboarding_doc.py` exits 0. `test_migrate_config_before_load` runs `["config", "migrate"]` with and without `--config` and still migrates before any config load, git, process or journal work; `test_older_schema_version_is_refused_naming_migrate_config` finds `clutch config migrate` in the older-version refusal; `test_migrate_config_validates_before_write` matches `repair.*retry config migrate`; and the onboarding steps name `clutch config init` between `clutch install` and `clutch doctor`. In those files only the argv and the pinned text named in Scope in change, no assertion is dropped or loosened, and nothing is added to `tests/integration/test_cli.py`.
10. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_main_verb_groups.py` exits 0 with those files unchanged.
11. `./dev.py test` exits 0; Check's `unit` and `integration` mechanical checks in `config.yaml` run both full suites. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is the known base flake (box-000706-10233120) and is verified on the base commit, not chased.

## Verification
```
./dev.py test tests/unit/test_main_config_group.py tests/unit/test_main_help.py tests/unit/test_readme.py tests/unit/test_host_running.py tests/unit/test_help.py tests/unit/test_init_config_verb.py tests/unit/test_update_config_verb.py
./dev.py test tests/integration/test_config.py tests/integration/test_cli.py tests/integration/test_host_onboarding_doc.py tests/integration/test_help.py tests/integration/test_main_verb_groups.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- `init-config`, `update-config` or `migrate-config` still runs as a top-level command through an alias, a hidden or suppressed parser, or argv rewriting in `main`, or a subcommand keeps the `-config` suffix.
- An argument, default, stdout line, written file or exit code of the three commands changes, other than the help text, argparse's usage and error lines, the refusal prefix, and the roads and header line named in Scope in.
- `config init` or `config migrate` needs a loadable config, `config migrate` ignores `--config`, or `config update` runs before config loads.
- A file outside the fence changes, including `clutch/hostfiles.py`, `CLAUDE.md`, `AGENTS.md`, `hosts/fixture/CLAUDE.md`, `clutch/help.py`, `clutch/observe.py`, `clutch/specs/` or `vscode-clutchwork/`.
- A test is added to a do-not-grow file, or an existing assertion is dropped, loosened or changed beyond the argv and pinned text named in Scope in.
- Another command is moved or renamed.

## Time budget
- expected: 20m
- stuck: 40m
