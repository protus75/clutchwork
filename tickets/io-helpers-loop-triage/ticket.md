---
state: draft
source: human
priority: P0
kind: chore
---

## Depends on
- io-helpers-loop-scheduler

## Context
- tests/fakes.py
- tests/git_fake.py
- tests/stage_replies.py
- clutch/docs/host-authoring.md#Unit and integration tests

## On-demand
- tests/integration/test_triage.py

## Goal / Why
On 2026-11-21 one integration run wrote 975 MB in 119,498 files and 1,531 real git repositories and saturated the disk. `integration-disk-io-skip` then skipped 184 integration test files, and `integration-io-guard` fails any integration test outside `REAL_IO_TESTS` that writes disk, starts a process or runs git. The owner wants the skipped files restored onto the shared in-memory fakes in later batch tickets, and most of them import their scaffolding from a few large skipped hub files, so no batch can restore a file until that scaffolding lives in an unskipped module that follows the rules. This ticket is one of five per-hub tickets that replace `io-helpers-loop`, which stopped three runs in a row with an empty diff because 26 names and 48 importers did not fit one run. Each hub's names move together with that hub's importers, so every name still resolves in exactly one place. The five write one module and chain by `## Depends on`: `io-helpers-loop-scheduler` -> `io-helpers-loop-triage` -> `io-helpers-loop-terminal` -> `io-helpers-loop-restart` -> `io-helpers-loop-serve-rig`.

When this ticket is done, `tests/loop_helpers.py` also defines every name that another test file imports from `tests/integration/test_triage.py` (`root_with_box`, `enqueue`, `reply`, `author_reply`, `requisition_reply`, `run`, `escape_rig`, `escape_report`), and each of the 14 importers takes it from `tests.loop_helpers`.

The helpers follow `clutch/docs/host-authoring.md` section "Unit and integration tests": no real git (use `tests/git_fake.py::GitFake`), no process (use `tests.fakes.FakeExec`, or call `clutch.__main__.main` in process), time through `tests.fakes.FakeClock` and `fakes.until`/`fakes.turn` with no sleep, a disk write only under a `tmp_path` the caller passes in. A model-reply helper reuses `tests/stage_replies.py` and config text reuses `tests/config_fixture.py`; a helper never copies either. `tests/loop_helpers.py` imports from no `tests/integration/` test file (it may import `tests/*_helpers.py` modules, `tests/stage_replies.py` and `tests/config_fixture.py`).

## Boundary contract
### Shared triage test helpers
- disposition: extend
- owner: tests/loop_helpers.py
- consumers: the 14 test files listed in `## Scope fence` that import `root_with_box`, `enqueue`, `reply`, `author_reply`, `requisition_reply`, `run`, `escape_rig`, `escape_report` from `tests/integration/test_triage.py`, and the later batch tickets that restore the skipped ones
- observable change: `root_with_box`, `enqueue`, `reply`, `author_reply`, `requisition_reply`, `run`, `escape_rig` and `escape_report` move from `tests/integration/test_triage.py` into `tests/loop_helpers.py`; `escape_rig` runs on `GitFake` instead of git; every importer's import line changes to `tests.loop_helpers`; the hub file imports the names back from the new module for its own tests; no production code, CLI, journal or document changes
- compatibility: every test that runs today still passes and the set of skipped tests is unchanged; a name that a running test reads as a module attribute of the hub stays reachable under the same name on the hub module
- acceptance: `tests/unit/test_loop_helpers.py` imports each name this ticket moves from `tests.loop_helpers` and exercises it without a process, real git or a write outside `tmp_path`; no importer still imports a moved name from the hub
- tests: tests/unit/test_loop_helpers.py
- post-merge source of truth: tests/loop_helpers.py
- ordering: `tests/loop_helpers.py` already exists from the earlier tickets of the chain; this ticket appends to it and to `tests/unit/test_loop_helpers.py` and adds no second module.

## Scope in / Scope out
Scope in:
- Add to `tests/loop_helpers.py` (create it if the earlier ticket of the chain is not merged yet, which `## Depends on` rules out) the names `root_with_box`, `enqueue`, `reply`, `author_reply`, `requisition_reply`, `run`, `escape_rig`, `escape_report`, each rewritten as described, keeping its signature unless a change is named.
- `requisition_reply` is a re-export of `tests.stage_replies.requisition_reply` (which the hub already imports), with no second definition. `tests/stage_replies.py` has no triage-verdict or authored-ticket builder, so `reply` (the triage verdict JSON) and `author_reply` (the authored-ticket JSON) move into `tests/loop_helpers.py` unchanged in body and signature; they do no I/O. Adding builders to `tests/stage_replies.py` is out of scope.
- `root_with_box` and `enqueue` move with their files written only under the `tmp_path` passed in; `run` keeps its signature and calls `main` in process with the `FakeLLM` it is given.
- `escape_rig` runs git today and becomes `tests/git_fake.py::GitFake` with `tests.fakes.FakeExec` and `tests.fakes.FakeFileSystem`. `escape_report` inlines the two values it takes from `tests/integration/test_author.py` (`bug_reply`) and `tests/integration/test_inbox.py` (`arrival`), taking each from `tests/stage_replies.py` or a `tests/*_helpers.py` module when one already has it, because `tests/loop_helpers.py` imports from no integration test file; if neither exists, inline only the lines it needs.
- `tests/integration/serve_rig.py` is an importer here and changes only its `from tests.integration.test_triage import reply` line.
- In every importer listed in `## Scope fence` (the 14 files that import a moved name from `tests/integration/test_triage.py`), change only the import line (also an import line inside a function) so each moved name comes from `tests.loop_helpers`. Names an importer takes from other hubs stay as they are, and a module import (`from tests.integration import <hub>`) is not an import of a name and stays. A file that is both hub and importer here also changes only its import lines.
- The hub `tests/integration/test_triage.py` deletes its definition of every moved name it defines and imports the name back from `tests.loop_helpers` (it keeps its tests, its `pytestmark = pytest.mark.disk_io_skip` line and every name it defines that no other file imports); the hub module keeps each moved name as a module attribute.
- Create or extend `tests/unit/test_loop_helpers.py`: one test per moved name, each running without reading a repo file and calling it with `tmp_path`, in-memory inputs and the shared fakes and asserting what it returns or writes, plus one test that every name this ticket moves is importable from `tests.loop_helpers`. Append only; the earlier tickets' tests stay as they are.
- `tests/loop_helpers.py` starts no process, runs no real git, and calls no real sleep: grep criterion 4 checks it.
- Record the base-commit and candidate integration pass and skip counts in `run.md` (criterion 5). The run adds no new test to a hot test file: the only edits in `tests/integration/test_cli.py`, `test_drain.py`, `test_daemon_composition.py`, `test_stages.py`, `test_mergequeue.py`, `test_watch.py` or `serve_rig.py` are import lines the move forces.
- - Engine-written `# clutch:meta` header lines: the engine's Check meta fill rewrites the header of each edited file after Implement. Those header changes are in scope; the implementer never edits them.
Scope out:
- Restoring any skipped test file (later batch tickets): a hub file stays skipped and its tests are unchanged; skipped importers may still break semantically and their batch ticket fixes that.
- Editing `tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py` or `tests/conftest.py`. A shared fake that lacks a behavior a helper needs stops the run as a premise failure naming the missing behavior (except `Time`, which moves unchanged where Scope in says so).
- Defining in `tests/loop_helpers.py` a class that duplicates `tests/fakes.py` or `tests/git_fake.py`, or a copied reply or config helper.
- Names that other hubs own: each of the other four `io-helpers-loop-*` tickets moves its own hub's names, and this ticket leaves their definitions and importers alone.

## Scope fence
- tests/loop_helpers.py
- tests/unit/test_loop_helpers.py
- tests/integration/test_triage.py
- tests/integration/serve_rig.py
- tests/integration/test_author.py
- tests/integration/test_box.py
- tests/integration/test_box_triage_inbox.py
- tests/integration/test_cli.py
- tests/integration/test_inbox.py
- tests/integration/test_open_tickets_closed.py
- tests/integration/test_requisition_identity_record.py
- tests/integration/test_retro.py
- tests/integration/test_retro_box.py
- tests/integration/test_roadmap_author.py
- tests/integration/test_roadmap_driver.py
- tests/integration/test_roadmap_row_author.py
- tests/integration/test_ticket_write_serialization.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_loop_helpers.py` passes; it checks that each of `reply` and `author_reply` returns the same JSON text as before for a fixed input, that `requisition_reply is tests.stage_replies.requisition_reply`, that `root_with_box(tmp_path)` writes only under `tmp_path`, and that `escape_rig` returns a checkout whose `git` is a `GitFake` and leaves no `.git` directory.
2. `grep -rPzl "from tests\.integration\.test_triage import" tests --include=*.py` lists no file: no file imports a name from the hub.
3. `grep -nE "^(async def|def|class) (root_with_box|enqueue|reply|author_reply|requisition_reply|run|escape_rig|escape_report)\b|^(root_with_box|enqueue|reply|author_reply|requisition_reply|run|escape_rig|escape_report) =" tests/integration/test_triage.py` prints nothing: the hub no longer defines a moved name.
4. `grep -nE "import subprocess|SubprocessExec|time\.sleep|git -C" tests/loop_helpers.py` prints nothing.
5. `./dev.py test tests/unit` and `./dev.py test tests/integration` exit 0, and the integration summary reports the same number of passed and skipped tests as on the base commit, both recorded in `run.md`.
6. `./dev.py test tests/integration/test_shared_fakes_adoption.py tests/integration/test_disk_io_skip_list.py tests/integration/test_serve_rig_fakes.py` passes (a running test that reads a moved name as a hub module attribute still sees the shared object).

## Verification
```
./dev.py test tests/unit/test_loop_helpers.py
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
- A test that runs today fails or is skipped, or a skipped test becomes unskipped.
- A moved name keeps real git, a process, or a write outside `tmp_path`, or `tests/loop_helpers.py` defines a class that duplicates a shared fake or a copied reply or config helper.
- `tests/loop_helpers.py` imports from a `tests/integration/` test file, or a name moved by another of the five tickets is moved here.
- A shared module (`tests/fakes.py`, `tests/git_fake.py`, `tests/stage_replies.py`, `tests/config_fixture.py`, `tests/conftest.py`) is edited.
- An importer changes anything other than its import line, or a hub test is deleted, weakened or restored.

## Time budget
- expected: 20m
- stuck: 40m
- reason: eight names and 14 one-line import edits; only `escape_rig` needs a body rewrite
