---
priority: P1
kind: chore
agent_tier: medium
agent_effort: medium
source: box:roadmap_row
state: draft
---

## Depends on
- cli-help-standard

## Context
- clutch/__main__.py::_command
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/covgate.py
- clutch/covmap.py
- docs/how-clutch-works.md#2.1 Verbs
- clutch/docs/host-running.md
- tests/unit/test_main_provider_group.py

## On-demand
- clutch/docs/host-contract.md
- clutch/requisition.py
- tests/integration/test_host_contract.py
- tests/integration/test_covgate.py
- tests/integration/test_requisition.py
- config.yaml

## Goal / Why
Roadmap row 140 (`cli-group-coverage`), group `coverage`. `covmap` and `covgate` are top-level verbs added with a bare `sub.add_parser` and a one-line `help=`, so `clutch help covgate` prints no reads, writes, lock, exit codes or examples. When this ticket is done, `clutch coverage map` and `clutch coverage gate` do what `clutch covmap` and `clutch covgate` do at HEAD, carry help to the row 129 standard through `_command`, and the old top-level names no longer parse (argparse exits 2; no alias, per `CLAUDE.md` "No dual-path code"). Every caller and document names the new form, so no road or config tells an operator or the Check stage to run a verb that no longer exists.

Why: the owner asked on 2026-11-17 for every command to live under a group with standard help (rows 129-140). `CLAUDE.md` "Guides name verbs, not command lines" needs every road and guide to name a verb the CLI accepts. The unit check in `config.yaml` and the host-contract example run `python -m clutch covgate`, so they must change in the same commit or the next Check fails with an argparse error.

Transition: a host whose `config.yaml` unit check still says `clutch covgate` gets exit 2 from Check after upgrading clutch; it changes that argv to `clutch coverage gate` (the host contract's example shows it). The managed `CORE_TEMPLATE` names neither verb (`git grep -nE 'covmap|covgate' clutch/hostfiles.py` finds nothing), so no `clutch host core` refresh is needed.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `covmap` and `covgate` parsers. Add a group `coverage` where they were, built the way the `ticket`, `engine`, `box`, `config` and `provider` groups are: a one-line summary, a `description`, an `Examples:` epilog whose `clutch coverage ...` lines parse, and `argparse.RawDescriptionHelpFormatter`. Its subparsers take `dest="coverage_verb"` and `required=True`. Its subcommands `map` and `gate` are built with `_command` with every field. Read each fact from its section 2.1 row in `docs/how-clutch-works.md`, `handle_covmap`, `handle_covgate`, `clutch/covmap.py` and `clutch/covgate.py` before writing it. `map` takes no arguments; `gate` keeps `--gate`, `--report` and the remainder `command` exactly as `covgate` has them.
- Dispatch: `handlers` drops `"covmap"` and `"covgate"` and gains `"coverage"`, dispatching by `args.coverage_verb` to the unchanged `handle_covmap` and `handle_covgate`. The pre-config clause `args.verb == "covgate"` becomes `args.verb == "coverage" and args.coverage_verb == "gate"`; `coverage map` still loads config as `covmap` does at HEAD.
- Roads and refusal prefixes: the `_fail("covgate", ...)` calls become `_fail("coverage gate", ...)`, so the refusal prints the one exact prefix `clutch coverage gate: `. The config-error road set `{"engine retro", "covmap"}` is replaced by a check on the computed `path`: at HEAD `path` is `args.verb` (so `coverage` for this group), and it must become `coverage map` when `args.verb == "coverage"` and `args.coverage_verb == "map"`, matched against the set `{"engine retro", "coverage map"}`, so its `retry` road reads `retry coverage map`. The comment mentioning covgate's group on timeout names `coverage gate`.

In, other code, string literals only:
- `clutch/covmap.py`: the three `retry covmap` roads become `retry coverage map`.
- `clutch/covgate.py`: the four `clutch covgate:` stderr prefixes become `clutch coverage gate:`.
- `clutch/requisition.py`: the road ``run `clutch covmap` `` becomes ``run `clutch coverage map` ``; `tests/integration/test_requisition.py` pins it.

In, config and documents (only references to the two commands change):
- `config.yaml`: the unit check argv `clutch, covgate, --` becomes `clutch, coverage, gate, --`; nothing else changes.
- `clutch/docs/host-contract.md`: the example unit check argv, same edit.
- `clutch/docs/host-running.md`: the first cells of the `covmap` and `covgate` rows become `coverage map` and `coverage gate`, text unchanged.
- `docs/how-clutch-works.md`: the section 2.1 rows begin `coverage map` and `coverage gate [--gate PATH] [--report PATH] -- <argv>`, text unchanged; the artifact table row says `coverage-map.json` is written by `coverage map`.

In, tests: new `tests/unit/test_main_coverage_group.py` (criteria 1-3 and 8), which builds `_parser()` in memory, reads and writes only under `tmp_path` and starts no process. `tests/integration/test_covgate.py`: the four `main(["covgate", ...])` argvs gain `"coverage", "gate"` (argv only). `tests/integration/test_host_contract.py`: the pinned `argv[:7]` becomes `["uv", "run", "python", "-m", "clutch", "coverage", "gate", "--"]` compared against `argv[:8]`.

Out: an alias of any kind; every other command (`release` and `publish` are row 139); Python names (`handle_covmap`, `handle_covgate`, the `clutch/covmap.py` and `clutch/covgate.py` modules and functions); `test-gate.toml` floors and `tests/integration/test_gate_floors.py` (they name modules); `clutch/help.py`, `clutch/observe.py`, `vscode-clutchwork/`, `dev.py` and `clutch/hostfiles.py` (no argv or text names these verbs); `CLUTCH_PLAN.md`, `docs/roadmap.md`, `CHANGELOG.md` and `tickets/`.

## Scope fence
- clutch/__main__.py
- clutch/covmap.py
- clutch/covgate.py
- clutch/requisition.py
- config.yaml
- clutch/docs/host-running.md
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_main_coverage_group.py
- tests/integration/test_covgate.py
- tests/integration/test_host_contract.py
- tests/integration/test_requisition.py

## Acceptance criteria
1. `tests/unit/test_main_coverage_group.py::test_coverage_group_parses`: `_parser().parse_args(["coverage", "map"])` gives `verb == "coverage"` and `coverage_verb == "map"`; `["coverage", "gate", "--gate", "g.toml", "--report", "r.json", "--", "pytest"]` parses with `gate == Path("g.toml")`, `report == Path("r.json")` and `command` ending `["pytest"]`; `["coverage"]` and `["coverage", "map", "--x"]` raise `SystemExit(2)`. Ruled out: an added argument to `map`, or a changed default for `--gate` (`test-gate.toml`) or `--report` (`coverage.json`).
2. `tests/unit/test_main_coverage_group.py::test_old_names_refuse`: `covmap` and `covgate` are not choices of the top-level subparsers, and `_parser().parse_args([name])` raises `SystemExit(2)` for each. Ruled out: an alias, hidden parser or argv rewrite that keeps an old name working.
3. `tests/unit/test_main_coverage_group.py::test_gate_needs_no_config`: in an empty `tmp_path`, `main(["coverage", "gate"], cwd=tmp_path, env={})` returns 2 with a stderr line starting with `clutch coverage gate: ` and containing `name the unit-test command after --`, not `config file not found`. Ruled out: `coverage gate` dispatched after the config load, and a prefix naming `covgate` or only `clutch coverage:`.
4. `tests/integration/test_covgate.py` passes with only the four argvs changed, and `./dev.py test tests/integration/test_host_contract.py tests/integration/test_requisition.py` exits 0 with the pins named in Scope in.
5. `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_main_verb_groups.py` exits 0 with those files unchanged: the parser walk checks the `coverage` group and both subcommands for a description and examples that parse, and the run-guide table has a row for each parser path. `uv run clutch help coverage gate` prints `Reads:`, `Writes:`, `Lock:`, `Exit codes:` and `Examples:` lines that agree with the section 2.1 row (exit 0 on coverage pass, 1 on threshold failures, 2 on refusal, the command's own nonzero code otherwise).
6. `git grep -nE 'clutch covmap|clutch covgate|retry covmap|, covgate, |\"covgate\"|\"covmap\"' -- clutch config.yaml docs/how-clutch-works.md README.md CLAUDE.md AGENTS.md tests ':!tests/unit/test_main_coverage_group.py' ':!tests/integration/test_gate_floors.py'` prints nothing (at HEAD it prints lines in `clutch/__main__.py`, `clutch/covmap.py`, `clutch/covgate.py`, `clutch/requisition.py`, `config.yaml`, `clutch/docs/host-contract.md`, `tests/integration/test_covgate.py`, `tests/integration/test_host_contract.py` and `tests/integration/test_requisition.py`). `tests/integration/test_gate_floors.py` is excluded because it names the `covmap` module for a `test-gate.toml` floor, not the command. Ruled out: a road, config argv, document or test left naming a removed command.
7. `./dev.py test` exits 0. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is a known base flake, verified on the base commit, not chased.
8. `tests/unit/test_main_coverage_group.py::test_map_config_error_road`: in an empty `tmp_path`, `main(["coverage", "map"], cwd=tmp_path, env={})` returns 2 with stderr containing `config file not found` and ending `-- repair the selected config and retry coverage map`. Ruled out: a road reading `retry coverage` or `retry covmap`, and a `path` left as `args.verb` so the config-error set never matches.

## Verification
```
./dev.py test tests/unit/test_main_coverage_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_help.py tests/unit/test_covgate.py
./dev.py test tests/integration/test_covgate.py tests/integration/test_covmap.py tests/integration/test_host_contract.py tests/integration/test_requisition.py tests/integration/test_help.py tests/integration/test_main_verb_groups.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- `covmap` or `covgate` still runs as a top-level command through an alias, a hidden parser or argv rewriting in `main`.
- A read, write, lock, stdout line or exit code of the two commands changes, other than help text, argparse's usage and error lines, the refusal prefixes and the roads named in Scope in.
- `coverage gate` needs a loadable config, or `config.yaml`'s unit check still names `covgate`.
- A Python name or module (`handle_covmap`, `handle_covgate`, `clutch/covmap.py`, `clutch/covgate.py`) is renamed, or another command is moved.
- A file outside the fence changes, or an existing assertion is dropped or loosened beyond the argv and pinned text named in Scope in.

## Time budget
- expected: 20m
- stuck: 40m
