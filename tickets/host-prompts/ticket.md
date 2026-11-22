---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Runs before
- extension-prompt-picker

## Context
- clutch/ask.py
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/config.py::Config
- clutch/docs/host-contract.md
- tests/unit/test_main_help.py
- tests/integration/test_config.py

## On-demand
- docs/how-clutch-works.md
- clutch/docs/host-running.md

## Goal / Why
A host can add its own operator prompts and run them through clutch, and every prompt, engine-owned or host-owned, is listed in one place with its description.

Today `clutch prompt` accepts only the fixed engine names in `ask.KINDS`, loads templates only from clutch's packaged `clutch/specs/ask/`, and keeps each prompt's one-line description in a `prompt_details` dict inside `clutch/__main__.py`. A host that writes its own prompt has no way to render it through clutch. Nothing can list the available prompts with descriptions either, which the VS Code prompt picker (`extension-prompt-picker`) needs.

After this ticket:
- `config.yaml` accepts an optional `prompts_dir` key (relative paths resolve against the config file's parent, like `report_inbox`). Each `<prompts_dir>/<name>.md` is a host prompt.
- A host prompt file starts with YAML frontmatter holding exactly two required keys: `description` (non-empty, one line) and `takes` (`none` or `stem`). The body is a `string.Template`: `$state_dir` is always substituted, and `$stem` and `$ticket` are also substituted when `takes: stem`. Rendering appends the `host_notes` block from `ask_notes`, the same as engine prompts.
- `clutch prompt host <name> [stem]` renders a host prompt. Host prompts sit under a fixed `host` subcommand for two reasons. The parser is built before config loads, so host names cannot be subcommands of their own. And the separate namespace means a future engine prompt name can never shadow a host prompt.
- `clutch prompt list` prints every prompt: engine prompts in `ask.KINDS` order, then host prompts sorted by name. Each line is tab-separated: the argv after `clutch` (for example `prompt diagnose` or `prompt host triage-notes`), what it takes (`none`, `stem`, or `box`), and the description.
- Engine prompt descriptions and what each prompt takes move out of `__main__.py` into `clutch/ask.py`. The parser help, the `handle_prompt` argument checks, and `prompt list` all read that one table.

## Boundary contract
### Host prompt files
- disposition: create
- owner: clutch/ask.py
- consumers: `clutch prompt host`, `clutch prompt list`, and the extension prompt picker (`extension-prompt-picker`)
- observable change: `<prompts_dir>/<name>.md` files with `description` and `takes` frontmatter become renderable prompts
- compatibility: hosts without `prompts_dir` see no change
- acceptance: a valid host prompt renders with substitutions; a file missing a key, with an unknown key, with a `takes` value outside `none`/`stem`, with a name failing the stem rule, or with an unknown template placeholder is reported as a problem naming its path, never rendered
- tests: tests/unit/test_ask_host_prompts.py
- post-merge source of truth: clutch/ask.py and clutch/docs/host-contract.md
- closest existing: the engine templates in `clutch/specs/ask/` loaded by `ask.render`, and `config.ask_notes`
- earning reason: engine templates live in clutch's own package and are engine-owned, so a host cannot add one there; `ask_notes` only appends text to engine prompts and cannot define a new one. A host-owned file format is the plugin extension point this request names.

### Prompt catalog
- disposition: create
- owner: clutch/ask.py
- consumers: `clutch prompt list`, the `clutch prompt` parser help, `handle_prompt` argument checks, and the snapshot prompt picker (`extension-prompt-picker`)
- observable change: `ask.catalog(config, repo)` returns `(entries, problems)`. Each entry has `name`, `argv` (the argv after `clutch`), `takes` (`none`/`stem`/`box`), `description`, and `source` (`engine`/`host`). Each problem is a `(path, message)` pair for an invalid host prompt file.
- compatibility: engine prompt names, descriptions and arguments are unchanged
- acceptance: the catalog lists every `ask.KINDS` entry with its existing description, followed by valid host prompts; invalid host files appear only in problems
- tests: tests/unit/test_ask_host_prompts.py
- post-merge source of truth: clutch/ask.py
- closest existing: the `prompt_details` dict and the stem-taking branches in `clutch/__main__.py` `handle_prompt`
- earning reason: those are private to the CLI, and the snapshot picker is a second production consumer that needs the same names, descriptions and argument kinds without copying them

### config.yaml `prompts_dir`
- disposition: extend
- owner: clutch/config.py
- consumers: clutch/ask.py
- observable change: new optional `prompts_dir` path key, default unset, resolved against the config file's parent
- compatibility: existing configs stay valid
- acceptance: absent means `None`; a relative value resolves like `report_inbox`
- tests: tests/unit/test_ask_host_prompts.py
- post-merge source of truth: clutch/config.py and clutch/docs/host-contract.md

### `clutch prompt` CLI
- disposition: extend
- owner: clutch/__main__.py
- consumers: operators, `extension-prompt-picker`
- observable change: new subcommands `prompt host <name> [stem]` and `prompt list`; existing subcommands unchanged
- compatibility: every existing `clutch prompt <kind>` invocation keeps its output and refusals
- acceptance: `prompt host` refuses (exit 2, with a paved road) when `prompts_dir` is unset, when the name is unknown, when the file is invalid, when the stem count does not match `takes`, or when a `takes: stem` ticket file does not exist; `prompt list` prints the catalog and exits 2 listing each problem when any host file is invalid
- tests: tests/unit/test_main_help.py and tests/unit/test_main_prompt_host.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- `clutch/config.py`: add `prompts_dir: PathField | None = None` to `Config` and resolve it in `_resolve_paths` like `report_inbox`.
- `clutch/ask.py`:
  - Add `DESCRIPTIONS` (engine kind to description, text moved verbatim from `prompt_details`) and `TAKES` (engine kind to `none`/`stem`/`box`), both keyed exactly by `KINDS`.
  - Add `catalog(config, repo)` and `render_host(name, stem, config, repo)`. `render_host` raises `ValueError` with the problem message for an invalid or unknown prompt.
  - Parse frontmatter with `yaml.safe_load`, the way `clutch/tickets.py` does, and validate names with `tickets.stem_findings`.
  - Use `Template.substitute`, so an unknown placeholder becomes a problem instead of passing through silently.
- `clutch/__main__.py`:
  - Build the prompt subparsers from `ask.DESCRIPTIONS`/`ask.TAKES` and delete `prompt_details`. Replace the hardcoded no-stem tuples in the example line and in `handle_prompt` with `ask.TAKES[kind] == "none"`.
  - Add the `host` and `list` subcommands through `_command`, with does/reads/writes/lock/exits/examples.
  - `prompt host` and `prompt list` load config as `prompt` already does.
- Docs, updating only the parts this change makes false:
  - `clutch/docs/host-contract.md`: add `prompts_dir: unset` to the defaults block, and add a paragraph next to the `ask_notes` paragraph describing the host prompt file format.
  - `clutch/docs/host-running.md`: the `prompt` row of the verb table names `prompt host` and `prompt list`.
  - `docs/how-clutch-works.md`: add `prompt host <name> [stem]` and `prompt list` rows to the section 2 verb table, and a `prompts_dir` row to the config key table.
- `tests/unit/test_main_help.py`: `test_prompt_group_matches_kinds` expects `set(ask.KINDS) | {"host", "list"}`.
- New `tests/unit/test_ask_host_prompts.py` covering catalog, render, and every invalid-file case under `tmp_path`.
- New `tests/unit/test_main_prompt_host.py` driving `main` for `prompt host` and `prompt list` against a `tmp_path` repo, including each refusal.

Scope out:
- The VS Code picker and the snapshot field (`extension-prompt-picker`).
- Any change to engine prompt templates or their rendered text.
- Making host names top-level `clutch prompt <name>` subcommands.
- Box-id-taking host prompts (`takes: box`); a host needing one files a follow-up.

## Scope fence
- clutch/ask.py
- clutch/config.py
- clutch/__main__.py
- clutch/docs/host-contract.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- tests/unit/test_main_help.py
- tests/unit/test_ask_host_prompts.py
- tests/unit/test_main_prompt_host.py

## Acceptance criteria
1. With `prompts_dir` set and `<prompts_dir>/notes.md` holding `description: Notes` and `takes: stem`, `clutch prompt host notes example` prints the body with `$stem` replaced by `example` and `$ticket` replaced by `tickets/example/ticket.md`, and exits 0, not 2 (`tests/unit/test_main_prompt_host.py`).
2. `clutch prompt host notes` with no stem, `clutch prompt host missing`, and `clutch prompt host notes example` with `prompts_dir` unset each exit 2 with a refusal naming the fix, never printing a prompt (`tests/unit/test_main_prompt_host.py`).
3. A host file missing `description`, with an extra key, with `takes: box`, named `Bad_Name.md`, or using `$nope` in its body appears in `catalog(...)[1]` with its path and is absent from `catalog(...)[0]`. `clutch prompt list` then exits 2, not 0 (`tests/unit/test_ask_host_prompts.py`, `tests/unit/test_main_prompt_host.py`).
4. `catalog(...)[0]` lists every `ask.KINDS` kind first, in `KINDS` order, with `argv == ["prompt", kind]`, followed by host prompts sorted by name with `argv == ["prompt", "host", name]` (`tests/unit/test_ask_host_prompts.py`).
5. `ask.DESCRIPTIONS.keys() == ask.TAKES.keys() == set(ask.KINDS)`, and `prompt_details` no longer appears in `clutch/__main__.py` (`tests/unit/test_ask_host_prompts.py`, `grep -n prompt_details clutch/__main__.py` prints nothing).
6. The prompt subcommand set equals `set(ask.KINDS) | {"host", "list"}` (`tests/unit/test_main_help.py`).
7. A config without `prompts_dir` loads with `prompts_dir is None`, and a relative value resolves against the config file's parent (`tests/unit/test_ask_host_prompts.py`).

## Verification
```
./dev.py test tests/unit/test_ask_host_prompts.py tests/unit/test_main_prompt_host.py tests/unit/test_main_help.py tests/integration/test_ask.py tests/integration/test_config.py
./dev.py test
```

## Definition of rejected
- Any existing `clutch prompt <kind>` output or refusal changes.
- Host prompt names or descriptions are hardcoded anywhere outside `clutch/ask.py`.
- An invalid host prompt file renders, or is silently dropped without appearing in problems.

## Time budget
- expected: 30m
- stuck: 60m
