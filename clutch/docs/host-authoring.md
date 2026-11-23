<!-- clutch:meta
schema: clutch.meta/1.0
kind: guide
purpose: Host guide to writing ticket content: the authoring workflow, what each section holds, how to keep tickets apart, unit vs integration test I/O rules, path matching, and how graphics and bug tickets prove their results
relates: [clutch/docs/host-running.md]
owner: clutch/docs/host-running.md
verified: 981eb002
hash: 1c700ddafbc93ba37961a52a22135f69950fef6499fface70c21018cca0c5bf7
-->
# Host ticket authoring

What to put in a clutch ticket, and the rules the code cannot explain on its own. The ticket
FORMAT (frontmatter keys, section names, list and block syntax) is owned by `clutch/tickets.py`
alone: start from the skeleton clutch writes and fix what its lint reports. A host's own docs say
what content its tickets carry, never the format. See the [host run guide](host-running.md) for invocation and operation.

## Workflow

1. Start with `clutch ticket new <stem> --kind feature|bug|chore|graphics`, choosing one kind (default `feature`).
   For a bug, first save the observed failure to a file and pass it with `--evidence <file>`.
   It writes
   `tickets/<stem>/ticket.md` with section placeholders and lints it. Every finding names the fix
   to apply. A bug includes `## Regression` and copies the evidence files into the ticket.
2. Fill each section with the content below, run `clutch ticket lint <stem>`, and repeat until it is
   clean. Omit stems to check all tickets that are
   not settled or rejected in the journal (all tickets when there is no journal). In a linked
   worktree, lint with no stems uses the main checkout's journal. Lint applies
   intake's claims, evidence and time budget checks and the `drain.max_ticket_minutes` stuck ceiling without taking the lock or writing anything; it prints
   findings with fixes and a valid/total summary. Exit 0 means all valid, 1 means findings, and
   2 means a named ticket is missing or the tickets directory is unreadable.
3. Before review, check that no criterion contradicts merged behavior or an existing test outside
   the fence, and that all criteria can hold together. Check that every invariant the ticket states
   or cites has a criterion whose test fails when the invariant is dropped.
   Run `clutch ticket review <stem>`, repair every finding,
   and repeat until it prints `approve`. Reviews with unmerged dependencies are provisional and not
   journaled; repair their findings, and the drain reviews again after the dependencies merge.
4. Intake commits a new ticket authored `state: draft` (as `clutch ticket new` writes it) and its evidence together, leaving it draft. Once review prints `approve` and any audit is done, its author runs `clutch ticket confirm <stem>` or names that command for the owner; only then can a running `engine serve` or `clutch engine drain` pick it up.

## What each section is for

- `Depends on`: tickets whose merged code this ticket needs. Use it only for that: a failed
  dependency blocks every ticket behind it. Merged code includes a test helper, fixture, fixture
  data set, or check rule another ticket creates. A ticket that uses one depends on the ticket that creates it.
  Never state a precondition that a person must perform outside the pipeline. Instead, add a
  `## Depends on` edge to a ticket that delivers it, or fence the file and put the edit in Scope in.
  For a `tickets/` path, use `## Depends on`; Implement cannot edit ticket files.
- `Runs before`: stems this ticket runs ahead of when both are eligible. This soft order never
  blocks; use it, not `Depends on`, for any other ordering. Use `clutch ticket order` to change it or priority.
  `Depends on` and `Runs before` stems name existing tickets, never the ticket itself, and never close a cycle.
  In `Depends on`, a stem with no `tickets/<stem>/ticket.md` is refused.
- `Context`: files the implementing agent reads before starting; they are embedded in its prompt.
  They must be existing UTF-8 text files; lint renders each entry exactly as Implement does.
  A file the ticket creates belongs in `Scope fence` only; name binary files by path in
  `Goal / Why` or `Scope in / Scope out`. Select a Python
  top-level definition, assignment, or class method with `path.py::Name` or `path.py::Class.method`;
  select a Markdown heading with `path.md#Heading` (a heading beginning with that text and a space
  also matches). A selection must resolve uniquely; list a file whole or by sections, not both.
  Author's prompt carries a `context_suggest` block of index-matched `path#Heading` and `path::Name` selectors (`none` or `unavailable: ...` when the index has nothing or cannot be read); prefer such a selector to listing a whole document, keep only entries the implementer needs, and treat the block as a hint. Once a draft has a `## Scope fence`, `clutch context suggest <stem>` also names files that past tickets changed together with the fence.
  Authors must never list a prompt spec in `Context`; list it under `On-demand` and fence it.
- `On-demand`: existing files the agent may need but that are too large to embed; it reads them
  from its worktree.
  Lint requires that an `On-demand` path is fenced and never also in `Context`.
- `Goal / Why`: what is true when the ticket is done that is not true now, and why it matters.
- `Boundary contract`: required for every non-settled ticket; declare each affected boundary
  with a `### <boundary>` heading and non-empty labeled bullets for `disposition`, `owner`,
  `consumers`, `observable change`, `compatibility`, `acceptance`, `tests`, and
  `post-merge source of truth`. Disposition is `reuse`, `extend`, `replace`, or `create`.
  `reuse` declares no contract change and identifies composition when relevant. Describe inputs,
  outputs, failures, side effects, invariants, ordering, persistence, atomicity, and composition
  when relevant. For breaking changes identify old and replacement contracts, consumer migrations,
  removal, and ordering. Bug fixes and refactors explicitly claim restoration or preservation.
  A `create` entry also has `closest existing` and `earning reason` bullets: name the closest
  existing symbols or artifacts in Context and why each cannot be reused. Earn creation through
  multiple production consumers, an external-effect fake, a named plugin or provider extension,
  consolidation of evidenced duplicates, or a process, storage, package, or independently deployed
  boundary. For example:

  ```markdown
  ### Ticket parser
  - disposition: extend
  - owner: clutch/tickets.py
  - consumers: intake and lint
  - observable change: accept the optional section
  - compatibility: existing tickets remain valid
  - acceptance: malformed declarations are refused
  - tests: parser shape tests
  - post-merge source of truth: clutch/tickets.py
  ```

  If no boundary changes, use `none` followed by `- reason: <preservation statement>`. Valid
  reasons are documentation corrections without behavior change; comments, spelling, formatting or
  metadata only; tests encoding an existing contract; regeneration with unchanged generator and
  generated contract; dependency or version updates proven not to change a consumed boundary;
  private implementation with callers, outputs, failures, side effects, construction and formats
  unchanged; or unreachable private code with no consumers. Repair malformed declarations using
  the lint finding; repair unsupported claims by identifying the canonical owner and true reason.
- `Scope in / Scope out`: what the agent changes, and what it must leave alone. When Scope in
  limits changes in a fenced file with "only" or "nothing else changes", it names every edit the change forces there.
  Include an import a new name needs and the expected set or skip list of every test that loops
  over a registry the ticket extends.
  Lint requires that a document named in `Scope in` is fenced; say which part to update or drop the mention.
  For a roadmap-row request whose Goal calls the work a slice, deliver the whole row, or fence
  `docs/roadmap.md` and add a follow-up row for the remaining parts in Scope in.
  Work deferred to separate tickets or left to an operator, owner, user, person, or later setup step needs an existing ticket stem in backticks or a fenced follow-up roadmap row, because no person runs the pipeline.
- `Scope fence`: every path the agent may write. Fence every file the acceptance criteria force
  it to change, including existing tests whose assertions flip; a forced file outside the fence
  makes the ticket impossible. Before replying, grep the repo for each changed name or value.
  When Scope in adds, removes, renames, or moves a member of a set (CLI subcommand, file or directory path, spec name, or an entry of an in-code registry, table, mapping, or closed vocabulary such as a menu, verb, kind, or adapter table), grep `tests/` and `docs/` for files that list that set or hardcode the old path, and fence every hit that asserts against the changed set or hardcodes the moved path. For an in-code entry, also grep `tests/` for the collection's name, and fence every test that compares that collection or a filtered subset of it for exact equality or lists it in full, and every file holding a table that a test requires to match the collection entry for entry. A mere textual mention, a path built under `tmp_path`, or a historical form the ticket keeps valid is not a hit. A test that only imports or iterates the collection, or reads one entry the change leaves alone, is not a hit. A ticket that changes documented behavior also fences that
  document and says in `Scope in / Scope out` which part to update, so docs and code land
  together. A ticket that bumps a prompt spec's `version` states it as the next minor above the version on main,
  never a literal target such as `3.4 -> 3.5`, and fences a test pin for the bumped file.
  Lint requires that a bumped prompt spec needs a fenced test pin.
  Lint requires every carried prefix to be fenced. When a fenced file has a positive
  `[coverage.files]` floor in `test-gate.toml`, lint requires a fenced path under `tests/unit/`.
  When a `Depends on` ticket is not merged yet, the author reads its fence and criteria. Fence
  any test it creates that asserts behavior this ticket changes, and Scope in names the one expectation that may change.
- `Acceptance criteria`: each criterion is a check someone can run or a path someone can read,
  never a judgment word. A criterion checked by a test names the wrong result the test rules out,
  for example, `parse('')` returns `[]`, not `None`. A test that also passes on the wrong result
  checks nothing. Before writing a criterion, check any case that must come from real code, such
  as a loader, builder, or test helper, in that code. A case the code filters out or cannot build
  is marked hand-built with its reason, and the Goal does not promise it.
  The words `improved`, `better` and `cleaner` are refused as unmeasurable.
  Lint requires that every criterion names a check in backticks.
  A changed-files check against main uses `main...HEAD`, never `main`.
- `Verification`: the commands Check runs; every one must exit 0.
- `Definition of rejected`: outcomes that mean the branch is thrown away even if it passes.
- `Time budget`: `expected` is your estimate; `stuck` is the deadline that stops the run.
  Both `expected` and `stuck` are AI time: the actual Implement minutes on the model that runs the ticket, never human working time.
  Estimate from the latest calibration table, which `clutch engine calibrate` journals and prints and Author's prompt carries as its `calibration` block: per provider and model, the median estimate and the median and 90th-percentile actual Implement minutes of recent runs.
  `stuck` is twice `expected`. Over 30m, split when possible or add `- reason: <why it is not split>`; over 60m, always split into more tickets, each its own stem. Never raise the budget instead.

## Keeping tickets apart

A file that many tickets fence makes their changes collide. Keep new work out of shared files:

- Put a ticket's new tests in a new test file named for the behavior it covers. Fence an
  existing test file only when the change forces an edit there (see `Scope fence`) or the file
  covers the edited unit and nothing else. Never add tests to a file just because it is the
  closest match.
- Put a new fixture, helper, rig, or data set in a new module next to its tests. Change a shared
  fixture, `conftest.py`, harness, or rig only when that fixture is the ticket's subject: do that
  in its own ticket, and the tickets that use it list it in `Depends on`.
- A ticket fences only the files its change forces. A fence that spans more than one subsystem
  is usually two tickets: link them with `Depends on` when the second needs the first's merged
  code, otherwise with `Runs before`.
- A documentation update edits only the section the change makes false.
- A ticket editing the roadmap or a plan document verifies the edit in review; never add a
  standing test or criterion pinning current text, including rows, exact commands, or phrases.
  The driver and `roadmap accept` rewrite roadmap rows and the owner revises plans, so such
  tests break main during normal work. The one allowed standing roadmap check is that the
  roadmap parses and its gate commands are valid. Write a criterion checking structure, such
  as parsing, or a one-time review check instead.

## Unit and integration tests

A test under `tests/unit/` reads and writes disk only under `tmp_path`; it never reads or writes a repo file, starts a process, or opens a network connection. In the unit suite `clutch.testguard` blocks processes and network connections but not disk, so reviewers check the disk part. Place a test that reads a repo file under `tests/integration/` and fence that file. An integration test never writes to disk, starts a process, runs git, or opens a network connection or an on-disk database; it drives the code through in-memory fakes. Only a test whose subject is a real I/O function touches real disk or processes, and its file is in the host's explicit allowlist (in clutch's own repo, `REAL_IO_TESTS` in `tests/integration/conftest.py`). Test temporary files never go to `/tmp`. A test using only `tmp_path`, in-memory buffers, or fakes stays under `tests/unit/`, as does a test that reaches a repo file only through an injected seam or fake. Updating a pinned value in an existing unit test that already reads a repo file does not move that test.

When Scope in adds lines to a file with a floor above 0 under `[coverage.files]` in `test-gate.toml`, a fenced `tests/unit/` test runs those lines. When running those lines needs a repo file, a process, or the network, Scope in names an in-fence seam, such as an injected reader or a parameter carrying the bytes, through which a fenced `tests/unit` test runs those lines with a fake, and covers the real disk, process, or network site only in an allowlisted real-I/O test. No seam is required for an I/O site where Scope in adds no line.

## Path matching

A fence entry matches a file when the file IS that path or lives under it as a directory:
`src/app` admits `src/app/views.py` but not `src/application.py`. A string prefix of a name never
matches. The same rule applies to `carries`.

## Graphics tickets

Choose `kind: graphics` for a visual deliverable. `clutch ticket new hero --kind graphics --reference mock.png --input product.png` copies regular files into `tickets/hero/reference/`; names must be distinct. References are optional mockups or baselines; inputs are images supplied to a generator.

A graphics ticket requires `## Render` and one or more `- artifact: <path>` output bullets. In `- mode: generate`, artifacts are committed deliverables; add up to three `- input: <path>` bullets or write the prompt in `## Goal / Why`. Optional `- reference: <path>` bullets name baselines and `- candidates: 1` through `5` selects the count (default 3). In `- mode: command`, artifacts live under a gitignored render directory. Include one fenced argv command and `- carries: <prefix>` bullets for its test or fixture paths; the command names a carried path and each prefix is in the scope fence. Inputs and candidates are generate only. The command prints exactly one JSON object: `{"render_result": "ok", "artifacts": [...]}` with exit 0, or `{"render_result": "error"}` for a missing prerequisite.

Add `- presence: embedding` to check input presence with embeddings; this requires `clutchwork[images-embed]`.

Write visual criteria as `- visual: <artifact>: <observable>`, naming a declared artifact and a concrete visible outcome. A declared artifact counts as the check for this form, without backticks. Include at least one non-visual mechanical criterion naming its check in backticks; prefer mechanical criteria wherever a test can decide the result.

## Bug tickets

A `kind: bug` ticket must prove the defect existed and is fixed. Three things carry the proof.

### Evidence

`ticket new` copies the supplied files into `tickets/<stem>/evidence/`. At least one file there must be
committed with the ticket before it runs:
the observed wrong output, a log excerpt, or the failing command's captured output. The file
must be a regular, non-symlink file. Every ticket read (intake, lint, confirm, drain, serve, run,
and Author) refuses a bug without evidence. Intake and lint also require evidence that is not
gitignored; intake commits new or changed evidence with the ticket. Settled and rejected tickets
are exempt, including at intake when the journal records settlement. Supply real evidence, never a placeholder.
Save the evidence before any change that destroys it, such as deleting a file, reloading data, or a manual fix.

`## Regression` appears only in a `kind: bug` ticket.

### The regression command

`## Regression` names one command, plus the test or fixture paths it carries. The command
must name a path under a `carries:` prefix; lint checks this before review. It
prints exactly one JSON object to stdout and nothing else; diagnostics go to stderr.
The command runs again in a fresh base worktree without `.venv`, so start with a program on PATH (such as `uv run python`) or a carried script, never `.venv/bin/...`.

- `{"regression_result": "pass"}` with exit 0: the defect is absent.
- `{"regression_result": "defect"}` with a non-zero exit: the defect is present.
- `{"regression_result": "error"}`: the run could not decide, for example a missing prerequisite.
  It never counts as either.

Any other stdout, extra keys, or a result whose exit code disagrees is refused. A bare test
runner (`pytest -q`) does not speak this protocol: write a small reproducer under a test or
fixture directory that checks its prerequisites, exercises the defect, and prints the object.

### How Check proves it

Check runs the regression command twice:

1. On the branch head: it must print `pass` and exit 0.
2. On the merge base, with the carried files copied over it: it must print `defect` and exit
   non-zero.

So the reproducer added with the fix is run against the old code. A reproducer that fails at
base only because its own inputs are missing proves nothing; have it check those inputs and
report `error`. Only files under a `tests/`, `test/`, `fixtures/`, or `fixture/` directory can be
carried; implementation files never are.
