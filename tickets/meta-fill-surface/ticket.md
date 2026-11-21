---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- meta-schema-and-refresh-r2

## Context
- clutch/meta.py
- clutch/specs/__init__.py
- tests/unit/test_meta_refresh.py
- tests/unit/test_meta_cli.py
- tests/unit/test_step_names_cover_surfaces.py
- docs/annotations-index-plan.md

## On-demand
- clutch/__main__.py
- clutch/observe.py
- clutch/help.py
- tests/unit/test_main_meta_group.py
- tests/integration/test_closed_sets.py
- vscode-clutchwork/extension.js
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- README.md

## Goal / Why
Roadmap row 70, ticket 2 of `docs/annotations-index-plan.md`. After this ticket `clutch meta fill [paths]` exists. For the files `clutch meta check` lists (missing block, empty `purpose`, or drifted `hash`), it computes the generated fields in memory (no file is written yet), then asks a read-only model in batches of at most 20 files, on a new `meta` surface with its own spec `clutch/specs/meta.md`, for `purpose` and, where the generator left them empty, `relates` and `owner`. The engine validates the reply, composes the block itself, and writes a file only after its entry validates, stamping `verified` and `hash`. The model never edits a file. Today `meta check` reports empty purposes that only a person can fill, so every annotated file stays unfinished and the index in later tickets has nothing to search on.

The reply is one JSON object `{"files": {"<path>": {"purpose": str, "relates": [str], "owner": str}}}` with exactly the asked paths. Rules the engine enforces: `purpose` is one nonblank line and contains no `-->`; every `relates` path is tracked (so exists); `relates` is applied only where the file's current `relates` is empty; `owner` is applied only where the current owner is the generator default `engine`; a path with a bad entry is not written, is named with its reason on stderr, and the command exits 1 after the other paths are written. The meta surface routes by `(tier, meta)` and falls back to the `review` row like every surface.

## Boundary contract
### meta fill verb
- disposition: extend
- owner: clutch/__main__.py (the `meta` group, `handle_meta`, `_run_meta`)
- consumers: operators and agent tasks running `clutch meta fill`; later tickets `meta-drift-lint` and `index-build` read the filled blocks
- observable change: new subcommand `meta fill` with optional `paths`; writes blocks under the writer lock; exit 0 when every target was filled, 1 when any file was rejected, 2 on refusal (malformed block, over-bound render, or provider failure)
- compatibility: `meta refresh` and `meta check` behave exactly as before; `purpose` of a file that already has one is never overwritten because such a file is a target only when drifted, and a drifted file keeps its existing nonempty `purpose` unless the reply supplies a new valid one
- acceptance: valid replies are written with `verified` and `hash` stamped; invalid replies leave the file byte-identical, including a file that had no block
- tests: new unit tests with a fake model, an inline spec and the in-memory filesystem
- post-merge source of truth: clutch/meta.py (block composition and validation), clutch/__main__.py (verb)

### meta LLM surface
- disposition: create
- owner: clutch/specs/meta.md and `ENGINE_LLM_SURFACES` in clutch/specs/__init__.py
- consumers: `meta fill`; routing, `observe.STEP_NAMES`, help and stats vocabulary that list surfaces
- observable change: a new closed surface name `meta`, a spec with the five required sections and data blocks `files` and `retry_findings`, read-only, medium tier
- compatibility: existing surfaces and routing rows unchanged; a host with no `meta` route resolves to its `review` row
- acceptance: spec lints clean; the surface is in the step vocabulary; the closed-set test lists it
- tests: spec load integration test, step-name coverage test, closed-set pin
- post-merge source of truth: clutch/specs/meta.md
- closest existing: clutch/specs/resolve.md and clutch/specs/retro.md (other read-only JSON-reply surfaces)
- earning reason: neither can be reused because each has its own reply schema, inputs and consumer; the plan names `meta` as its own surface so routing and cost are attributable, and the model call is an external effect that tests fake at the LLM seam

## Scope in / Scope out
Scope in:
- `clutch/meta.py`: extract the generated-field computation and block composition that `refresh` does inline into one shared pure helper that composes the block from fields and body, including the `.py` `# relates: [...]` 160-character trim, and that both `refresh` and `fill` call, with no change to `refresh` behavior (`tests/unit/test_meta_refresh.py` and `tests/unit/test_meta_cli.py` stay green). `fill` never splices a block itself (no `body[:offset] + render + body[offset:]` in `clutch/metafill.py`); model-supplied `relates` therefore pass through the same trim as generated ones. Add the pure fill pieces: target selection from `check` findings, request payload per batch of at most 20 files (path, content with block removed, generated fields computed in memory, never by calling `refresh` before validation), reply validation, and block composition that stamps `verified` (first 8 characters of the supplied sha) and `hash`. A reply `owner` that is blank or whitespace-only after strip is not applied, so the file keeps `engine` and stays stable under `meta refresh`. `fill` writes a file only after its reply entry validates, so a rejected file, including one with a missing block, is never touched. All file access goes through the injected filesystem.
- `clutch/metafill.py` (new): the batch loop is `async def fill(...)`. It takes the loaded `Spec` and an `ask` callable as parameters and never loads a spec file. `ask` is `async (paths: list[str], files_json: str) -> MetaReply | None`, where `MetaReply` is a pydantic model `{files: dict[str, MetaEntry]}` declared in this module and `None` means the driver ended without an ok outcome. The loop calls `ask` once per batch and returns written and rejected paths. It has no retry loop of its own: reply-shape validation and its single re-prompt belong to the driver. The module also holds `review_reply(expected_paths, reply) -> GateReport`, a pure function that fails a reply whose path set differs from the asked paths and names each missing or extra path as a finding. It also holds the adapter factory that builds `ask` from `driver`, `spec`, `repo` and a run sequence, exactly as `clutch/acceptance.py` builds its call: `driver.run(LlmStage(surface="meta", emits=MetaReply, gates=[], render=<spec.render with files=files_json and retry_findings=the driver's findings>, review=<review_reply bound to the asked paths>), None, ticket=None, run_seq=<count of journal events, as acceptance does>, attempt=<batch number>, workspace=repo, tier=spec.meta.tier, effort=spec.meta.effort, stuck_budget=<the ticket's stuck budget in seconds>, expected_budget="surface", scope_fence=())`. A result outcome other than `ok` makes `ask` return `None`, and the batch's paths are rejected with that outcome as the reason. `clutch/__main__.py` stays thin.
- `clutch/__main__.py`: add `fill` to the `meta` group with full `_command` help (what it does, reads, writes, lock, exit codes, examples). `_run_meta` becomes `async def _run_meta(verb, config, root, fs, tracked, sha, paths=(), ask=None)`, and its `check` and `refresh` bodies are unchanged; `fill` awaits the metafill loop with the spec and `ask`. `handle_meta` already runs inside `async def execute()` under `asyncio.run`, so it now awaits `_run_meta`. It adds only a single lock condition (`args.meta_verb in ("refresh", "fill")`) and one call that loads `clutch/specs/meta.md` from `SPECS_DIR` and builds `ask` with the factory from `clutch/metafill.py`, taking `driver` and the checkout from the same place `roadmap accept` takes them; no other new logic lands there.
- `tests/unit/test_meta_cli.py`: its `_run_meta(...)` calls become `asyncio.run(_run_meta(...))`, the one edit the async signature forces; no assertion changes.
- `clutch/specs/meta.md` (new) at version `1.0`, and add `meta` to `ENGINE_LLM_SURFACES`.
- `clutch/observe.py`: add `meta` to `STEP_NAMES`; `clutch/help.py`: add `meta` to the step entries; `vscode-clutchwork/extension.js`: only the icon entry the step-icons test requires for the new step, nothing else.
- Update the documents that name the meta verbs: the verb tables in `docs/how-clutch-works.md` section 2 and `clutch/docs/host-running.md`, and `README.md`, each only where it lists `meta refresh` and `meta check`, keeping the existing wording and list punctuation intact. README.md reads: 'Use `clutch meta refresh` to update configured file metadata, `clutch meta check` to report missing, empty or drifted blocks, and `clutch meta fill` to fill them using a read-only model.'
- Update the two existing tests that pin changed sets: `tests/integration/test_closed_sets.py` (the `ENGINE_LLM_SURFACES` set gains `meta`) and `tests/unit/test_main_meta_group.py` if it lists the group's subcommands.

Scope out: the `meta_drift` gate and Check-time refresh (`meta-drift-lint`); the index and `context suggest`; annotating this repo's files (the `meta-annotate-*` tickets); routing rows in `config.yaml`; any change to `refresh` or `check` behavior; Implement ever running `meta fill`.

## Scope fence
- clutch/meta.py
- clutch/metafill.py
- clutch/__main__.py
- clutch/specs/meta.md
- clutch/specs/__init__.py
- clutch/observe.py
- clutch/help.py
- vscode-clutchwork/extension.js
- docs/how-clutch-works.md
- clutch/docs/host-running.md
- README.md
- tests/integration/test_closed_sets.py
- tests/unit/test_main_meta_group.py
- tests/unit/test_meta_cli.py
- tests/unit/test_meta_fill.py
- tests/integration/test_meta_fill_spec.py
- tests/unit/test_main_meta_fill.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_meta_fill.py` proves a valid reply for a file with an empty `purpose` writes that purpose, sets `verified` to the first 8 characters of the supplied sha and `hash` to `meta.digest` of the body, and that `meta.check` then returns `[]`, not `[(path, "empty_purpose")]`. The test passes an inline spec text with `files` and `retry_findings` data blocks; it does not read `clutch/specs/meta.md`.
2. `./dev.py test tests/unit/test_meta_fill.py` proves a reply whose `purpose` contains `-->` or a newline, or whose `relates` names an untracked path, leaves that file byte-identical and lists it as rejected, while a valid sibling in the same batch is written; the result is not an all-or-nothing write. It also proves a rejected file that had no block at all stays byte-identical, not carrying a generated block.
3. `./dev.py test tests/unit/test_meta_fill.py` proves `relates` supplied by the model does not replace a nonempty generated `relates`, and a non-`engine` `owner` is kept, not overwritten. It also proves a long model `relates` list on a `.py` file is trimmed exactly as `meta.refresh` would trim it, and a blank or whitespace-only reply `owner` leaves `engine` so a following `meta.refresh` changes nothing.
4. `./dev.py test tests/unit/test_meta_fill.py` proves 45 target files produce 3 `ask` calls of 20, 20 and 5 files, not one call of 45, and that `review_reply` returns a failing `GateReport` naming the path for a reply that is missing or adds a path, and a passing one for the exact asked set. The test uses multi-character paths such as `docs/asked.md` and `docs/added.md` and asserts the exact set of finding messages. The driver owns the re-prompt; `retry_findings` reaching the rendered prompt is proved by criterion 6.
5. `./dev.py test tests/unit/test_main_meta_fill.py` proves `asyncio.run(_run_meta("fill", ..., ask=fake))` returns 0 when all targets are filled and 1 when any file was rejected. The same file also proves, on a MemoryFS input, that `meta check` and `meta refresh` outputs are unchanged by asserting exact return codes and captured stdout: `asyncio.run(_run_meta("check", ...))` prints `<path>: missing` and returns 1 before refresh; `asyncio.run(_run_meta("refresh", ...))` prints the changed path and returns 0; a later `check` prints `<path>: empty_purpose` and returns 1.
6. `./dev.py test tests/integration/test_meta_fill_spec.py` proves, with the spec path anchored through `Path(__file__)`, that `load_spec` on `clutch/specs/meta.md` returns `llm_surface == "meta"`, the data blocks `files` and `retry_findings`, and that `render` with those two inputs succeeds.
7. `./dev.py test tests/unit/test_step_names_cover_surfaces.py tests/integration/test_closed_sets.py tests/integration/test_step_icons.py` passes with `meta` in `ENGINE_LLM_SURFACES` and `STEP_NAMES`; the closed-set pin lists `meta`, not the old eleven-name set.
8. `./dev.py test tests/unit/test_help.py tests/integration/test_help.py tests/unit/test_main_help.py tests/unit/test_main_meta_group.py` passes, with `clutch meta fill` carrying a description, exit codes and an example and the group epilog listing it.

## Verification
```
./dev.py test tests/unit/test_meta_fill.py tests/unit/test_main_meta_fill.py tests/unit/test_meta_refresh.py tests/unit/test_meta_cli.py tests/unit/test_meta_block.py
./dev.py test tests/unit/test_step_names_cover_surfaces.py tests/unit/test_help.py tests/unit/test_main_help.py tests/unit/test_main_meta_group.py tests/unit/test_specs.py
./dev.py test tests/integration/test_meta_fill_spec.py tests/integration/test_closed_sets.py tests/integration/test_step_icons.py tests/integration/test_help.py
```

## Definition of rejected
The model is given any way to edit a file, or a block is written without validating `relates` paths and the one-line `purpose`. `meta fill` overwrites a nonempty `purpose` without a valid reply for it, or writes any file before its reply entry validates. `meta refresh`, `meta check` or the gate/Check flow changes. A new config knob, extra block key, or a second code path for composing blocks is added. An acceptance criterion is proved only in a file other than the one it names.

## Time budget
- expected: 25m
- stuck: 50m