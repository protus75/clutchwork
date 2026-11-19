---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- graphics-kind

## Runs before
- conflict-discard-rerun

## Context
- clutch/stages.py::regression_result
- clutch/stages.py::run_host_command
- clutch/stages.py::check_hosts
- clutch/stages.py::check
- clutch/tickets.py::_render
- clutch/driver.py::Spool
- tests/unit/test_stages_host_lock.py
- docs/gemini-graphics-refactor-plan.md#B2.
- docs/gemini-graphics-refactor-plan.md#B8.

## On-demand
- clutch/specs/implement.md
- clutch/docs/host-authoring.md
- docs/how-clutch-works.md

## Goal / Why
Roadmap row 50 (gemini plan B2). Today a `kind: graphics` ticket with `mode: command` declares a render command in `## Render`, but nothing runs it at Check, and the implementer's spec says nothing about graphics. After this ticket:

- Check runs the render command at the branch head through `run_host_command` and decodes its stdout with a protocol modeled on `regression_result`: exactly one JSON object, either `{"render_result": "ok", "artifacts": [...]}` with exit 0, or `{"render_result": "error"}` (a missing prerequisite, never success). Any other stdout, extra or duplicate keys, a non-list `artifacts`, or an `ok` with a non-zero exit is refused as a hard finding.
- Check verifies the listed artifacts are exactly the declared `- artifact:` paths, each exists, is non-empty, and has content matching its extension (PNG signature, SVG with an `svg` XML root, HTML containing an `<html` tag). Other extensions only need to be non-empty.
- Verified artifacts are copied into the attempt spool directory `ctx.driver.spool.root / stem / str(attempt) / "render"` so the operator and the later visual reviewer can open them. Artifacts are never committed.
- `clutch/specs/implement.md` gains a graphics block for both modes: for `command`, run the render command, open your own artifacts, compare with the references and `visual:` criteria before committing, never commit artifacts; for `generate`, produce the declared number of candidates from the inputs and prompt into the attempt render directory, never commit a candidate, and name in `run.md` what varied between candidates.

The host owns the renderer; the engine runs only the command and gains no browser dependency. `generate` mode has no render command, so Check does nothing new for it.

## Boundary contract
### Render result protocol at Check
- disposition: create
- owner: clutch/stages.py
- consumers: `check` in clutch/stages.py (the only production caller), graphics tickets with `mode: command`, the operator reading the attempt render directory
- observable change: a graphics `command` ticket runs its render command at Check; a bad protocol reply, wrong artifact set, missing or empty file, or content mismatch yields a hard finding with a paved road; an ok run copies artifacts to the attempt spool directory
- compatibility: bug, feature, chore tickets and `generate` graphics tickets take the same Check path as before; no existing report or finding changes
- acceptance: the decoder and content checks are pure functions with unit tests; the Check wiring is covered by a fake-exec test that calls `check` itself
- tests: tests/unit/test_stages_render_check.py
- post-merge source of truth: clutch/stages.py
- closest existing: `regression_result` and `_gather_bug` in clutch/stages.py; they decode a different object (`regression_result`, head/base pair, carried-file overlay) and require a bug ticket, so the render decoder cannot reuse them. Command execution itself reuses `run_host_command`.
- earning reason: a second stdout protocol with a different key set and an artifact list; folding it into `regression_result` would couple two protocols and make each decoder accept the other's shape.

### Ticket render declaration parser
- disposition: extend
- owner: clutch/tickets.py
- consumers: lint inside clutch/tickets.py and the new Check code in clutch/stages.py
- observable change: the private `_render` is renamed `parse_render` so Check can read the declaration; behavior and findings are unchanged
- compatibility: restoration of existing parser behavior; the only callers are the two inside clutch/tickets.py and are updated in the same change (no alias kept)
- acceptance: existing graphics lint tests still pass
- tests: tests/unit/test_graphics_kind.py (unchanged, must pass)
- post-merge source of truth: clutch/tickets.py

### Implement spec graphics block
- disposition: extend
- owner: clutch/specs/implement.md
- consumers: the Implement stage prompt
- observable change: a graphics block inside `## Task` tells the implementer how to behave per mode
- compatibility: non-graphics tickets read the same instructions; the spec version moves to the next minor above main
- acceptance: the spec lints and loads at the new version
- tests: tests/unit/test_specs.py and tests/integration/test_specs_delimiter_note.py
- post-merge source of truth: clutch/specs/implement.md

## Scope in / Scope out
Scope in:
- clutch/stages.py: add a pure `decode_render(stdout, rc)` returning `("ok", artifacts)`, `("error", [])`, or `None` for anything refused; a pure `artifact_problem(path, data)` returning a message or `None`; and `check_render(ctx, ticket, attempt)` returning `(reports, hard)` like `check_hosts`. `check_render` returns empty lists unless `ticket.frontmatter.kind == "graphics"` and the parsed mode is `command`. It runs the single command with `run_host_command` (code `render`, spool name `check/render.txt`), reads each artifact from the worktree, and on success writes the bytes with `ctx.fs.write` under `ctx.driver.spool.root / stem / str(attempt) / "render"` (the text-only `Spool.write` cannot carry binary). Call it from `check` beside `check_hosts` and fold its hard findings into `host_hard` and its reports into the invoice. Every hard finding carries a paved road. Artifact paths from the command are validated as repo-relative without `..` before any read.
- clutch/tickets.py: rename `_render` to `parse_render` and update its two callers; nothing else.
- clutch/specs/implement.md: add the graphics block and bump `version` to the next minor above the version on main.
- tests/unit/test_specs.py: move both implement version pins to the new version: line 25 in `test_spec_lint_accepts_the_implement_and_requisition_specs` and line 129 in `test_implement_spec_consumer_read`; no other expectation changes.
- tests/integration/test_stages.py: move only the `- spec: implement 2.18` pin at line 341 to the new version; no other change and no new tests in that file (the version bump forces this edit).
- tests/integration/test_implement_spec_mutation_check.py: move only its version pin at line 14 (`load_spec(text).meta.version == "2.18"`) to the new version; nothing else in that file changes.
- The graphics block in `clutch/specs/implement.md` is a paragraph or bullet list inside `## Task`, not a new `## ` heading (tests/unit/test_specs.py:136 pins the section list to Role, Task, Inputs, Output format, On-failure), and the spec stays within SPEC_MAX_LINES (200; it is 141 lines at HEAD).
- tests/integration/test_specs_delimiter_note.py: move only its `("implement", ...)` version pin to the bumped version; no other expectation changes.
- clutch/docs/host-authoring.md: in the Graphics tickets section, add the render protocol sentence for `command` mode (one JSON object, `ok` with artifacts and exit 0, `error` for a missing prerequisite). docs/how-clutch-works.md: update only the Check description to say a graphics `command` ticket's render runs there.
- tests/unit/test_stages_render_check.py (new): the tests below, with a fake exec seam built as in tests/unit/test_stages_host_lock.py and artifacts under `tmp_path`, including a test that drives `check` itself so the new lines in `check` run.

Scope out: the `image_quality` gate, the visual judge, candidate selection and the select commit (`image-quality-gate`, `visual-review-surface`, `image-candidates-select`); routing by kind; any renderer or browser dependency; Markdown and flowchart host checks (they need no engine change); `conflict-discard-rerun`, which bumps the implement spec after this ticket.

## Scope fence
- clutch/stages.py
- clutch/tickets.py
- clutch/specs/implement.md
- clutch/docs/host-authoring.md
- docs/how-clutch-works.md
- tests/unit/test_specs.py
- tests/integration/test_specs_delimiter_note.py
- tests/integration/test_stages.py
- tests/integration/test_implement_spec_mutation_check.py
- tests/unit/test_stages_render_check.py

## Acceptance criteria
1. `decode_render('{"render_result": "ok", "artifacts": ["a.png"]}', 0)` returns `("ok", ["a.png"])`, not `None`; the same stdout with rc 1 returns `None`, as do an extra key, duplicate keys, `"artifacts": "a.png"`, trailing prose, and `ok` without `artifacts`; checked by `./dev.py test tests/unit/test_stages_render_check.py`.
2. `decode_render('{"render_result": "error"}', 2)` returns `("error", [])`, and `check_render` reports it as a hard finding, never as success; checked by `./dev.py test tests/unit/test_stages_render_check.py`.
3. `artifact_problem` returns a message, not `None`, for: missing data, empty bytes, `a.png` holding `b"not a png"`, `a.svg` whose XML root is `html`, and `a.html` without an `<html` tag; it returns `None` for a real PNG signature, an `<svg>` root, and an HTML page; checked by `./dev.py test tests/unit/test_stages_render_check.py`.
4. With a fake exec returning a valid `ok` reply whose artifact list differs from the declared `- artifact:` set (one extra, or one missing), `check_render` returns a hard finding with a paved road and writes nothing under the spool render directory; checked by `./dev.py test tests/unit/test_stages_render_check.py`.
5. With a fake exec returning a valid `ok` reply matching the declared set and valid files, `check_render` returns no hard findings and the artifact bytes exist, byte-identical, under `<spool root>/<stem>/<attempt>/render/`; checked by `./dev.py test tests/unit/test_stages_render_check.py`.
6. `check_render` on a `generate` graphics ticket and on a `feature` ticket returns `([], [])` and the fake exec records zero calls; checked by `./dev.py test tests/unit/test_stages_render_check.py`.
7. A listed artifact path `../x.png` or an absolute path is refused as a hard finding and never read; checked by `./dev.py test tests/unit/test_stages_render_check.py`.
8. `clutch/tickets.py` has no `_render` definition or call, and the existing graphics lint tests pass unchanged; checked by `./dev.py test tests/unit/test_graphics_kind.py tests/unit/test_graphics_new.py`.
9. `clutch/specs/implement.md` has a graphics block covering `command` and `generate` modes, its `version` is the next minor above main's, and every implement version pin passes at the new version (`test_spec_lint_accepts_the_implement_and_requisition_specs` and `test_implement_spec_consumer_read` in tests/unit/test_specs.py, the `("implement", ...)` entry in tests/integration/test_specs_delimiter_note.py, line 14 of tests/integration/test_implement_spec_mutation_check.py, and line 341 of tests/integration/test_stages.py); checked by `./dev.py test tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py::test_implement_check_review_all_ok_with_artifacts_and_provenance`.
10. Calling `check` on a graphics `command` ticket with a fake exec returning `{"render_result": "error"}` yields a refused result carrying a hard finding with code `render`, and the invoice contains a `render` report; calling `check` on a `feature` ticket yields no `render` report in the invoice and no finding with code `render`; an implementation that never calls `check_render` from `check` fails the first case; checked by `./dev.py test tests/unit/test_stages_render_check.py`.

## Verification
```
./dev.py test tests/unit/test_stages_render_check.py tests/unit/test_specs.py tests/integration/test_specs_delimiter_note.py tests/integration/test_implement_spec_mutation_check.py tests/integration/test_stages.py::test_implement_check_review_all_ok_with_artifacts_and_provenance tests/unit/test_graphics_kind.py tests/unit/test_graphics_new.py tests/unit/test_stages_host_lock.py
```

## Definition of rejected
Check commits a rendered artifact; a reply that `regression_result` accepts is accepted as a render result (or the reverse); an `error` reply counts as success; the engine imports a browser or image library; `Spool.write` is changed to carry bytes; a `_render` alias is left behind; or a non-graphics ticket's Check output changes.

## Time budget
- expected: 20m
- stuck: 40m
- reason: one new Check path with a pure decoder, a pure content check and a spec block; the pieces share one test file and splitting would leave the protocol undecidable without its wiring.
