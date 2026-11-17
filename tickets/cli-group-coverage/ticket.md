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
Roadmap row 140 (`cli-group-coverage`), group `coverage`. `covmap` and `covgate` are top-level verbs added with a bare `sub.add_parser` and a one-line `help=`, so `clutch help covgate` prints no reads, writes, lock, exit codes or examples. When this ticket is done, `clutch coverage map` and `clutch coverage gate` do what `clutch covmap` and `clutch covgate` do at HEAD, carry help to the row 129 standard through `_command`, and the old top-level names no longer parse (argparse exits 2; no alias, per `CLAUDE.md` "No dual-path code"). Their refusals print the group prefix `clutch coverage: `, as every group since row 130 does through `_fail(args.verb, ...)` (row 139's `release` group prints `clutch release:`). Every caller and document names the new form, so no road or config tells an operator or the Check stage to run a verb that no longer exists.

Why: the owner asked on 2026-11-17 for every command to live under a group with standard help (rows 129-140). `CLAUDE.md` "Guides name verbs, not command lines" needs every road and guide to name a verb the CLI accepts. The unit check in `config.yaml` and the host-contract example run `python -m clutch covgate`, so they change in the same commit; otherwise every Check after the merge fails with an argparse error.

Run precondition (the owner's, before confirming; not implementation work). Check and the merge queue run the `review.mechanical` argv of the `config.yaml` the engine loads from the main checkout at dispatch (`clutch/drain.py` reloads it before each dispatch; `clutch/stages.py::check_hosts` runs it with the ticket's worktree as cwd), never the branch's copy. At `b3e91afa` that argv is `uv run python -m clutch covgate -- ...`, and `python -m clutch` in the worktree imports this branch's code, where `covgate` no longer parses. So this ticket's own unit check exits 2 (`invalid choice: 'covgate'`, reproduced on a scratch copy of this change) while the merge base passes, and Check fails on every attempt. The ticket can run only once the unit check argv the engine loads no longer runs this branch's `covgate` parser. box-000743-5a8ed2ca proposes running the gate through the engine's installed `clutch` (`[clutch, covgate, --, uv, run, python, -m, pytest, ...]`; in a scratch copy, main's `clutch covgate` passed this change's 947 unit tests); that change's stem then joins `## Depends on`. If a Check finding shows `invalid choice: 'covgate'`, the precondition is unmet and only the owner can clear it; never keep or add a `covgate` parser.

Transition. After the merge the drain reloads `config.yaml` before its next dispatch and, because `clutch/**` changed, re-execs into the merged code, so later Checks run `clutch coverage gate` against code that has it. A host whose `config.yaml` unit check says `clutch covgate` gets exit 2 from every Check once it upgrades clutch past this change; it edits that argv to `clutch coverage gate` in the same step as the version pin (the host contract's example shows the new form). A road printed before the merge (`retry covmap`, ``run `clutch covmap` ``) names the old form; run `clutch coverage map`. The managed `CORE_TEMPLATE` names neither verb (`git grep -nE 'covmap|covgate' clutch/hostfiles.py` finds nothing), so no `clutch host core` refresh is needed.

Merge order. Row 139 (`cli-group-release`, confirmed at `b3e91afa`) runs first. Its `release` group replaces the `publish` and `release` parsers directly above the `covmap` parser, so this ticket's worktree starts from that merged text and adds the `coverage` group right below it. A scratch copy that applied row 139's prototype and then this change, and one that applied them in the other order, ended in identical trees. Only a run started from the same base as row 139 conflicts, in `clutch/__main__.py` alone, where the two parser hunks touch. Neither ticket names the other's commands, and both tickets' criteria held in both orders.

## Scope in / Scope out
In, `clutch/__main__.py`:
- Remove the top-level `covmap` and `covgate` parsers. Add a group `coverage` where they were (below row 139's `release` group), built the way the `view`, `host` and `release` groups are: a one-line summary, a `description`, an `Examples:` epilog whose `clutch coverage ...` line parses, and `argparse.RawDescriptionHelpFormatter`. Its subparsers take `dest="coverage_verb"` and `required=True`. Its subcommands are built with `_command` with every field and keep today's one-line summaries. Read each fact from its section 2.1 row in `docs/how-clutch-works.md`, `handle_covmap`, `handle_covgate`, `clutch/covmap.py` and `clutch/covgate.py` before writing it. Help strings stay within `ruff check`'s 200-character line limit.
  - `map`, no arguments. Facts: runs `review.coverage_map.argv` and writes `<state_dir>/coverage-map.json`, mapping each covered source file to the test files that ran it, for requisition review. Reads config (`review.coverage_map`), the JSON report its command writes and the `main` commit. Writes `coverage-map.json`, replaced whole; deletes the configured report before and after the run. Lock: none. Exits 0 on success, 2 on refusal (config fails to load, no `review.coverage_map`, the command fails, or its report is missing or invalid). Example `clutch coverage map`.
  - `gate`, keeping `--gate`, `--report` and the remainder `command` exactly as `covgate` has them. Facts: runs the unit-test command after `--` in the invocation directory, then checks its fresh coverage report against the gate file, printing one line per threshold failure. Reads the gate file (`--gate`, default `test-gate.toml`) and the report (`--report`, default `coverage.json`), relative to the invocation directory; no config. Writes nothing itself; deletes the report before the run. Lock: none. Exits 0 on coverage pass, 1 on threshold failures, 2 on refusal (no command after `--`, command not found, invalid gate file, missing or invalid report), otherwise the command's own nonzero code. Example `clutch coverage gate -- python -m pytest tests/unit --cov=clutch --cov-report=json:coverage.json`.
- Dispatch: `handlers` drops `"covmap"` and `"covgate"` and gains `"coverage"`, dispatching by `args.coverage_verb` to the unchanged `handle_covmap` and `handle_covgate`. The pre-config clause `args.verb == "covgate"` becomes `(args.verb == "coverage" and args.coverage_verb == "gate")`; `coverage map` still loads config and builds the checkout as `covmap` does at HEAD.
- Refusals and roads: the two `_fail("covgate", ...)` calls in `handle_covgate` become `_fail(args.verb, ...)`, so they print `clutch coverage: `. No `print(..., file=sys.stderr)` is added to `clutch/__main__.py` (`tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner`). In the config-error road, `path` becomes `coverage map` when `args.verb == "coverage"` and `args.coverage_verb == "map"` (otherwise as at HEAD), and the set `{"engine retro", "covmap"}` becomes `{"engine retro", "coverage map"}`, so a config error prints `clutch coverage: <error> -- repair the selected config and retry coverage map`. The comment naming covgate's group on timeout names `coverage gate`.

In, other code, string literals only:
- `clutch/covmap.py`: the four `retry covmap` roads become `retry coverage map`.
- `clutch/covgate.py`: the four `clutch covgate:` stderr prefixes in `run_gate` become `clutch coverage:`.
- `clutch/requisition.py`: the road ``run `clutch covmap` `` becomes ``run `clutch coverage map` ``.

In, config and documents (only references to the two commands change):
- `config.yaml`: in the unit check argv, `clutch, covgate, --` becomes `clutch, coverage, gate, --`; nothing else changes.
- `clutch/docs/host-contract.md`: the example unit check argv, same edit.
- `clutch/docs/host-running.md`: the first cells of the `covmap` and `covgate` rows become `coverage map` and `coverage gate`, in place, text unchanged.
- `docs/how-clutch-works.md`: the section 2.1 rows begin `coverage map` and `coverage gate [--gate PATH] [--report PATH] -- <argv>`, in place, text unchanged; the section 10.1 row says `coverage-map.json` is written by `coverage map`.

In, tests (only the argv and the pinned text named here change):
- New `tests/unit/test_main_coverage_group.py` (criteria 1-3 and 8). It builds `_parser()` in memory and calls `main(..., cwd=tmp_path, env={})` in an empty `tmp_path`, as `tests/unit/test_main_provider_group.py` does; it reads no repo file and starts no process.
- `tests/integration/test_covgate.py`: the three `main(["covgate", ...])` calls and the `args = ["covgate", ...]` list in `test_cli_invalid_inputs` start `"coverage", "gate"` instead.
- `tests/integration/test_host_contract.py`: `unit.argv[:7] == ["uv", "run", "python", "-m", "clutch", "covgate", "--"]` becomes `unit.argv[:8] == ["uv", "run", "python", "-m", "clutch", "coverage", "gate", "--"]`.
- `tests/integration/test_requisition.py`: the pinned road ``run `clutch coverage map` ``.

A scratch prototype of exactly this change touched the 12 fenced files. On row 139's prototype at `b3e91afa`, `clutch coverage gate` passed 950 unit tests with every `test-gate.toml` floor, 3,410 integration tests passed, and `ruff check` and `ruff format --check` passed. Alone on `b3e91afa`: 947 unit tests, 3,410 integration tests and both ruff checks passed.

Out: an alias of any kind; every other command (`release` and `publish` are row 139); Python names (`handle_covmap`, `handle_covgate`, the `clutch/covmap.py` and `clutch/covgate.py` modules and functions, and the `covgate` module import in `tests/integration/test_host_contract.py`); `test-gate.toml` floors and `tests/integration/test_gate_floors.py` (they name modules); `clutch/help.py`, `clutch/observe.py`, `vscode-clutchwork/`, `dev.py`, `README.md`, `CLAUDE.md`, `AGENTS.md` and `clutch/hostfiles.py` (no argv or text names these verbs); `CLUTCH_PLAN.md`, `docs/roadmap.md`, `CHANGELOG.md` and `tickets/`.

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
1. `tests/unit/test_main_coverage_group.py::test_coverage_group_parses`: `_parser().parse_args(["coverage", "map"])` gives `verb == "coverage"` and `coverage_verb == "map"`; `["coverage", "gate"]` parses with `gate == Path("test-gate.toml")`, `report == Path("coverage.json")` and `command == []`; `["coverage", "gate", "--gate", "g.toml", "--report", "r.json", "--", "pytest"]` parses with `gate == Path("g.toml")`, `report == Path("r.json")` and `command == ["--", "pytest"]`; `["coverage"]` and `["coverage", "map", "--x"]` raise `SystemExit(2)`. Ruled out: an added argument to `map`, or a changed default for `--gate` or `--report`.
2. `tests/unit/test_main_coverage_group.py::test_old_names_refuse`: `covmap` and `covgate` are not choices of the top-level subparsers, the `coverage` group's choices are exactly `{"map", "gate"}`, and `_parser().parse_args([name])` raises `SystemExit(2)` for each old name. Ruled out: an alias, hidden parser or argv rewrite that keeps an old name working.
3. `tests/unit/test_main_coverage_group.py::test_gate_needs_no_config`: in an empty `tmp_path`, `main(["coverage", "gate"], cwd=tmp_path, env={})` returns 2, prints nothing to stdout, prints exactly `clutch coverage: name the unit-test command after --` and a newline to stderr, and leaves `tmp_path` empty. Ruled out: `coverage gate` dispatched after the config load (stderr would say `config file not found`), and a prefix naming `covgate` or `coverage gate`.
4. `tests/integration/test_covgate.py` passes with only the four argvs changed, and `./dev.py test tests/integration/test_host_contract.py tests/integration/test_requisition.py` exits 0 with the pins named in Scope in.
5. `./dev.py test tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_help.py tests/integration/test_help.py tests/integration/test_main_verb_groups.py` exits 0 with those files unchanged: the parser walk checks the `coverage` group and both subcommands for a description and examples that parse, and the run-guide table has a row for each parser path. `uv run clutch help coverage gate` prints `Reads:`, `Writes:`, `Lock:`, `Exit codes:` and `Examples:` lines that agree with the section 2.1 row (exit 0 on coverage pass, 1 on threshold failures, 2 on refusal, the command's own nonzero code otherwise).
6. `git grep -nE 'clutch covmap|clutch covgate|retry covmap|clutch, covgate|"covgate"|"covmap"' -- clutch config.yaml docs/how-clutch-works.md README.md CLAUDE.md AGENTS.md tests ':!tests/unit/test_main_coverage_group.py' ':!tests/integration/test_gate_floors.py'` prints nothing (at `b3e91afa` it prints lines in `clutch/__main__.py`, `clutch/covmap.py`, `clutch/covgate.py`, `clutch/requisition.py`, `config.yaml`, `clutch/docs/host-contract.md`, `tests/integration/test_covgate.py`, `tests/integration/test_host_contract.py` and `tests/integration/test_requisition.py`). `tests/integration/test_gate_floors.py` is excluded because it names the `covmap` module for a `test-gate.toml` floor, not the command, and the pattern skips the `covgate` module import in `tests/integration/test_host_contract.py`. Ruled out: a road, config argv, document or test left naming a removed command.
7. `./dev.py test` exits 0. A failure of `tests/integration/test_exec_seam_reap.py::test_usage_and_independent_peak_memory` alone is a known base flake, verified on the base commit, not chased.
8. `tests/unit/test_main_coverage_group.py::test_map_config_error_road`: in an empty `tmp_path`, `main(["coverage", "map"], cwd=tmp_path, env={})` returns 2, prints nothing to stdout, and prints one stderr line that starts `clutch coverage: `, contains `config file not found` and ends `-- repair the selected config and retry coverage map`. Ruled out: a road reading `retry coverage` or `retry covmap`, and a `path` left as `args.verb` so the config-error set never matches.

## Verification
```
./dev.py test tests/unit/test_main_coverage_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_help.py tests/unit/test_covgate.py
./dev.py test tests/integration/test_covgate.py tests/integration/test_covmap.py tests/integration/test_host_contract.py tests/integration/test_requisition.py tests/integration/test_help.py tests/integration/test_main_verb_groups.py
```

## Definition of rejected
The branch is rejected, even if it passes, when:
- `covmap` or `covgate` still runs as a top-level command through an alias, a hidden parser or argv rewriting in `main`, including one kept to get past Check.
- A read, write, lock, stdout line or exit code of the two commands changes, other than help text, argparse's usage and error lines, the refusal prefix `clutch coverage: ` and the roads named in Scope in.
- `coverage gate` needs a loadable config, or `config.yaml`'s unit check still names `covgate`.
- A Python name or module (`handle_covmap`, `handle_covgate`, `clutch/covmap.py`, `clutch/covgate.py`) is renamed, or another command is moved.
- A file outside the fence changes, or an existing assertion is dropped or loosened beyond the argv and pinned text named in Scope in.

## Time budget
- expected: 20m
- stuck: 40m
