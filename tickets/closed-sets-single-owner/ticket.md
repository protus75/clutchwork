---
state: draft
source: box:roadmap_row
priority: P2
kind: chore
agent_tier: medium
agent_effort: medium
---

## Depends on
none

## Context
- clutch/llm.py
- clutch/artifacts.py::NonBlank
- clutch/artifacts.py::_Strict
- clutch/box.py::_repo_path
- clutch/inbox.py::relative
- clutch/stages.py::ticket_blob
- clutch/stages.py::_major
- clutch/tickets.py::Frontmatter

## On-demand
- docs/roadmap.md

## Goal / Why
Roadmap row 19 (section 2.2 and 2.3 of `docs/roadmap.md`). After this change each of the following has exactly one definition and every other site imports or derives from it, so adding a member or fixing a validator is one edit instead of a hunt across modules:

- Tiers `low|medium|high|max`: owner `clutch/llm.py` (`AgentTier`, `AgentEffort`, plus a new `TIERS = get_args(AgentTier)`). The copies in `config.py` (`Tier`), `tickets.py` (`Level`), `caps.py` (`LEVELS`), `providers.py` (local `tiers` tuple) and the two tier tuples in `__main__.py` go away. `policy.TIERS` already derives from `AgentTier` and stays as is.
- Priorities `P0..P3`: owner `clutch/tickets.py` (a new `Priority` Literal and `PRIORITIES = get_args(Priority)`); the `--priority` choices in `__main__.py` use it.
- Kinds `feature|bug|chore`: owner `clutch/tickets.py` (a new `Kind` Literal and `KINDS = get_args(Kind)`); `Frontmatter.kind`, `template()`, the `--kind` choices and the kind set in `__main__.py`, and the kind loop in `stats.py` (`(*KINDS, "unknown", "all")`) use it.
- `NonBlank`: owner `clutch/artifacts.py`; the copies in `author.py`, `triage.py`, `box.py` and `inbox.py` are deleted and those modules import it.
- Strict pydantic bases: owner `clutch/artifacts.py`, as `StrictModel` (strict, `extra="forbid"`) and `FrozenModel(StrictModel)` (adds `frozen=True`). The `_Strict` in `artifacts.py` and `stages.py` becomes `FrozenModel`; the `_Strict` in `config.py` and `box.py` and `Strict` in `inbox.py` become `StrictModel`. Their current `frozen` setting is preserved. Models elsewhere that set their own `model_config` (retro, thresh, timers, mergequeue, gates, merge, requisition, rework, tickets, author, triage) are not rebased; only the five shared bases are unified.
- Repo-relative path validation: owner `clutch/artifacts.py::is_repo_relative(value) -> bool`, true only for a nonblank value that does not start with `/`, has no `..` segment, and contains no backslash or NUL. The validators in `box.py`, `inbox.py` and `config.py` and the fence-entry check in `tickets.py` call it and keep their own error message. `covgate.py` calls it and keeps its extra normalization check (`str(p) == path`, no `.` segment). This tightens `box.py`, `config.py` and `tickets.py` to also refuse backslash and NUL, which `inbox.py` already did.
- Git blob SHA: owner `clutch/git.py::blob_sha(data: bytes) -> str`. `stages.ticket_blob` is deleted; `stages.py`, `serve.py`, `requisition.py` and `hostfiles.py` call `git.blob_sha`. (It lives in `git.py` because `hostfiles.py` is imported by `stages.py`, so `stages.py` cannot own it.)
- Spec-major: `stages._major(spec)` is the one helper. The inline `int(spec.meta.version.split(".")[0])` in `requisition.py`, `rework.py`, `policy.py` and `baseline.py` call it. If a module-level import creates a cycle, import it inside the function in that module only.

`AuthorReply.ticket` must keep its final newline. The shared `NonBlank` strips whitespace, so `ticket` in `clutch/author.py` is typed `str` with a validator that rejects a blank value without stripping.

## Scope in / Scope out
In: the definitions and call sites listed in Goal. Update the existing tests and harness modules that pin a deleted name: `tests/integration/test_closed_sets.py` (`caps.LEVELS`, `config.Tier` and `tickets.Level` pins now assert `llm.TIERS`, `llm.AgentTier` and `llm.AgentEffort`), `tests/integration/test_host_contract.py` (the `config._Strict` subclass scan becomes `artifacts.StrictModel`, and `config.Tier` becomes `llm.AgentTier`), and the four harness modules `tests/harness/shakeout/run.py`, `tests/harness/daemon_soak.py`, `tests/harness/reliability_battery.py` and `tests/harness/host_loop.py`, each of which imports `FrozenModel` from `clutch.artifacts` instead of `_Strict` and subclasses it. In `docs/roadmap.md` add one new row, number 94 (the next unused master-table number), to the `### 0.3.0` table (the one that holds row 19), appended directly after row 34 and before the blank line and the `gate` block that follow it. The row has Stem `closed-sets-remaining`, Owner `roadmap`, Kind chore, P `P3`, Depends on `closed-sets-single-owner`, empty Runs before, no authored marker, and Content naming the sets left in section 2.2 (settled and retired states, failed-attempt terminals, surfaces, spike kinds, box classes, triage verdicts, control verbs, ask kinds, finding codes, conduct-file routing) plus the kind tuple in `author.py` and the version split in `artifacts.py`. Section 2.2 and 2.3 prose is not edited.

Out: the CORE_TEMPLATE `--kind` list in `hostfiles.py` stays as it is (decision 5); the `("feature", "chore", "bug")` skeleton-order tuple in `author.py` stays; `eval/harness.py`'s own `_Strict` stays; `int(...split(".")[0])` on a version string in `artifacts.py` and `roadmap.py` stays (it takes no `Spec`); `drain.PRIORITY` stays; `policy.TIERS` stays; other models with their own strict `model_config` stay. No behavior change other than the path-validator tightening named above and the stripping of `NonBlank` values in `box.py`, `inbox.py`, `triage.py` and `author.py` models other than `AuthorReply.ticket`.

## Scope fence
- clutch/llm.py
- clutch/artifacts.py
- clutch/git.py
- clutch/config.py
- clutch/tickets.py
- clutch/caps.py
- clutch/providers.py
- clutch/__main__.py
- clutch/stats.py
- clutch/box.py
- clutch/inbox.py
- clutch/author.py
- clutch/triage.py
- clutch/stages.py
- clutch/covgate.py
- clutch/serve.py
- clutch/requisition.py
- clutch/hostfiles.py
- clutch/rework.py
- clutch/policy.py
- clutch/baseline.py
- docs/roadmap.md
- tests/integration/test_closed_sets.py
- tests/integration/test_host_contract.py
- tests/harness/shakeout/run.py
- tests/harness/daemon_soak.py
- tests/harness/reliability_battery.py
- tests/harness/host_loop.py
- tests/unit/test_closed_sets_single_owner.py
- tests/integration/test_closed_sets_single_owner.py

## Acceptance criteria
1. `tests/unit/test_closed_sets_single_owner.py::test_author_reply_keeps_final_newline`: `AuthorReply(stem="s", ticket="x\n").ticket == "x\n"`, not `"x"`; `AuthorReply(stem="s", ticket=" \n")` raises `ValidationError`.
2. `tests/unit/test_closed_sets_single_owner.py::test_is_repo_relative`: `is_repo_relative` returns `False`, not `True`, for `""`, `"  "`, `"/a"`, `"a/../b"`, `"a\\b"` and `"a\0b"`, and `True` for `"a/b"` and `"tickets/x/"`; a `box.RepoPath` validation of `"a\\b"` raises.
3. `tests/unit/test_closed_sets_single_owner.py::test_blob_sha`: `git.blob_sha(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"`.
4. `tests/unit/test_closed_sets_single_owner.py::test_owner_constants`: `llm.TIERS == ("low", "medium", "high", "max")`, `tickets.PRIORITIES == ("P0", "P1", "P2", "P3")` and `tickets.KINDS == ("feature", "bug", "chore")`; `tickets.Frontmatter` rejects kind `"graphics"` and priority `"P4"`; `template("graphics")` still raises.
5. `tests/integration/test_closed_sets_single_owner.py::test_single_definitions` (an `ast` scan of `clutch/*.py`): no class named `_Strict` or `Strict` is defined in any `clutch/*.py`, and `StrictModel` and `FrozenModel` are defined only in `artifacts.py`; `NonBlank` is assigned only in `artifacts.py`; `hashlib.sha1` is called only in `git.py`; `requisition.py`, `rework.py`, `policy.py` and `baseline.py` contain no `.split(".")[0]`; the pre-change tree (five `_Strict`/`Strict` base classes, five `NonBlank` copies, three sha1 sites) fails the test.
6. `tests/integration/test_closed_sets_single_owner.py::test_closed_set_literals_have_one_home`: outside `llm.py`, no tuple, list, set or `Literal[...]` of string constants in `clutch/*.py` equals the four tier strings; outside `tickets.py` and `author.py`, none contains all of `feature`, `bug` and `chore`, or all of `P0` to `P3`; `hostfiles.py` is not scanned for the CORE_TEMPLATE string.
7. `tests/integration/test_closed_sets_single_owner.py::test_follow_up_row`: in `docs/roadmap.md` the `### 0.3.0` table has exactly one row numbered 94 whose Stem is `closed-sets-remaining`, whose Owner is `roadmap` and whose Depends on is `closed-sets-single-owner`, and no other table holds that stem; row 19 and row 49 still name `closed-sets-single-owner` unchanged.
8. `./dev.py test tests/integration/test_closed_sets.py tests/integration/test_host_contract.py` exits 0 after the pin updates.

## Verification
```
./dev.py test tests/unit/test_closed_sets_single_owner.py tests/integration/test_closed_sets_single_owner.py
./dev.py test tests/integration/test_closed_sets.py tests/integration/test_host_contract.py tests/unit/test_roadmap_table.py tests/integration/test_roadmap_table.py
./dev.py test tests/unit
```

## Definition of rejected
A second definition of any helper or set named in Goal remains in `clutch/`; `AuthorReply.ticket` loses its final newline; `hostfiles.py` CORE_TEMPLATE or `author.py` skeleton order changes; a compat alias keeps a deleted name (`ticket_blob`, `caps.LEVELS`, `config.Tier`, `tickets.Level`, `_Strict`) importable; or a test is weakened to pass instead of updated to the new owner.

## Time budget
- expected: 120m
- stuck: 170m
