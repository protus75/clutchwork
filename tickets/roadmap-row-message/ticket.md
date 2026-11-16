---
state: confirmed
source: human
priority: P1
kind: feature
---

## Depends on
- none

## Context
- clutch/box.py::MessageClass
- clutch/box.py::Message
- clutch/box.py::Box.enqueue
- clutch/config.py::BoxRow
- clutch/config.py::BOX_POLICY_DEFAULTS
- clutch/policy.py::start_state
- clutch/tickets.py::Frontmatter
- clutch/tickets.py::intake_pending
- clutch/author.py
- clutch/triage.py::_settle_pass
- tests/unit/test_author.py
- tests/unit/test_retro_recurrence.py::MemoryJournal
- tests/integration/test_author.py::_run
- tests/integration/test_author.py::_routes
- tests/integration/test_author.py::test_author_uses_baseline_resolution
- tests/integration/test_policy.py::test_bootstrap_without_a_go_or_with_phase_one_no_go_drafts_every_row
- tests/integration/test_closed_sets.py::test_box_closed_sets_and_constants
- tests/integration/test_closed_sets.py::test_config_closed_sets_and_constants
- tests/integration/test_config.py::test_valid_config_loads_from_cwd_with_shipped_defaults
- tests/integration/test_triage.py::author_reply
- tests/integration/test_drain.py::make_root
- docs/how-clutch-works.md#9.1
- docs/how-clutch-works.md#9.3
- docs/roadmap-driver-plan.md#3.

## On-demand
- clutch/specs/author.md
- clutch/help.py
- clutch/docs/host-contract.md

## Goal / Why
`docs/roadmap-driver-plan.md` section 3 (roadmap row 90) has the roadmap driver author `docs/roadmap.md` rows through the one Author stage that already writes tickets from Suggestion Box messages (`clutch/author.py::author`), with "a different shape" of message. That shape does not exist: `clutch/box.py::MessageClass` has five classes, none of which carries a roadmap row or its owning plan, and the Author prompt (`clutch/specs/author.md`) has no block for either. This ticket adds the message and the Author side. The sibling ticket `roadmap-author` adds the table parser and the `clutch roadmap author` verb that files these messages, and it depends on this one.

Starting state: `clutch/policy.py::start_state` makes every Author ticket a draft while the review baseline is not GO, and this repo's journal holds one `review_baseline` signal, `NO_GO`, so every Author ticket here starts as a draft awaiting `confirm`. Release 0.2.0's ship gate (`docs/roadmap.md` section 1) requires the driver to author and run at least three rows with no operator verdict. The owner decided (2026-11-16) that a roadmap row is approved by being in the roadmap, and `requisition_review` still gates every authored ticket. So the `roadmap_row` policy row defaults to `confirmed`, and the baseline condition alone does not apply to it. The other draft conditions still apply: a reopened message, an empty safety inventory, a fence that touches the inventory, and a `gate_bypass`.

After this change:
1. `roadmap_row` is a sixth message class. Its messages carry a `RoadmapRow`: the row's number, release group heading, stem, owner, kind, priority, depends, runs-before, content, and the repo-relative path of its owning plan.
2. For a `roadmap_row` message, Author embeds the row and the plan in two new prompt data blocks. Author declines the message before any model call when the plan is not a tracked file.
3. Author's gate requires the ticket's stem, kind, and priority to equal the row's. It also accepts a `tickets/<stem>/` directory that holds evidence but no `ticket.md`, because a roadmap row's hand-test evidence is dropped there before the row is authored (the roadmap-author refusal). That evidence is committed with the ticket.
4. The ticket starts `confirmed` under a NO_GO or absent baseline, unless another draft condition holds or the operator set `box_policy.roadmap_row: draft`.

## Scope in / Scope out
Scope in:
- `clutch/box.py`: append `"roadmap_row"` to `MessageClass` (so `MESSAGE_CLASSES` ends with it). Add a strict model `RoadmapRow(_Strict)` with fields `number` (int >= 1), `release` (NonBlank), `stem` (NonBlank), `owner` (NonBlank), `kind` and `priority` (typed by the annotations `clutch/tickets.py::Frontmatter` already declares, read through `Frontmatter.model_fields`, not a restated literal; `clutch/tickets.py` imports nothing from `clutch/box.py`, so the import adds no cycle), `depends` (list of NonBlank, default `[]`), `runs_before` (list of NonBlank, default `[]`), `content` (NonBlank), and `plan` (`RepoPath`). Add `Message.roadmap_row: RoadmapRow | None = None`; `Message._coherent` raises `ValueError` unless a row is present exactly when `message_class == "roadmap_row"`. `Box.enqueue` gains a keyword `roadmap_row: RoadmapRow | None = None` passed into the `Message`. Existing box files without the field still load, because the default is `None`.
- `clutch/config.py`: append `"roadmap_row"` to `BoxRow` and `"roadmap_row": "confirmed"` to `BOX_POLICY_DEFAULTS`.
- `clutch/policy.py::start_state`: the `not go` condition drafts every row except `"roadmap_row"`. Every other condition is unchanged. `policy_row` needs no change: it already maps a class in `MESSAGE_CLASSES` to the same-named row.
- `clutch/author.py`:
  - A module constant `PLAN_WHOLE_CHARS = 40_000` and a pure function `plan_excerpt(text: str) -> str`. It returns `text` unchanged when `len(text) < PLAN_WHOLE_CHARS`. Otherwise it returns the plan's `## Target design` and `## Where each piece lives` sections, in document order and joined by a blank line. Each section runs from its heading line (an exact line match) to the line before the next line starting `## `. A `## ` line inside a ```-fenced block does not end a section. When the plan has neither heading, it returns a fixed note that names both section titles and the 40,000-character bound and asks the reader to read the plan file at the row's `plan` path. The note contains none of the plan's text.
  - In `author()`, for a `roadmap_row` message: when `message.roadmap_row.plan` is not in the tracked-file list `author()` already reads, return `failure_declined` with evidence naming the plan path and the row's number and stem, before any `driver.run`. Otherwise read the plan from `checkout.repo / plan`. `render_author` passes two new inputs on every render: `roadmap_row` (the row's `model_dump_json()`) and `plan` (`plan_excerpt` of the plan text). For every other class both inputs are the string `none`.
  - `AuthorGate.check`, only when its message is a `roadmap_row` message:
    - A reply stem that differs from the row's stem is a `ticket_schema` finding naming the row's stem. Paved road: use the row's stem.
    - A parsed frontmatter `kind` or `priority` that differs from the row's is a finding naming the row's value. Paved road: write the row's value.
    - The "stem already exists" finding fires when `tickets/<stem>/ticket.md` exists, not when only the directory does.
  - For every other class the existing directory check is unchanged.
  - The commit inside `author()`: for a `roadmap_row` message, `only` also carries every path that `git ls-files --cached --others --exclude-standard -z -- tickets/<stem>/evidence/` lists, run through `checkout.git._run` as `clutch/tickets.py::intake_pending` does. Other classes make no listing call and commit exactly what they commit today.
- `clutch/specs/author.md`: bump `version` to the next minor above its value on main at the base commit (major unchanged, so the baseline identity's `spec_major` does not move). Add two data blocks after `Request`: `Roadmap row` (`roadmap_row`) and `Owning plan` (`plan`), in the same `<<clutch-data:begin NAME>>` form as the others. Add one Task paragraph: for a `roadmap_row` request, author the ticket for that row; use the row's `stem` as the reply's `stem` and its `kind` and `priority` in the frontmatter; build what the row's `content` names as the `plan` block designs it; and read the plan file at the row's `plan` path for anything the block leaves out. For other requests both blocks read `none`.
- `clutch/help.py`: add a `"roadmap_row"` entry to the `box` vocabulary, saying the message asks Author for the ticket one `docs/roadmap.md` row describes. `tests/unit/test_help.py` derives the expected keys from `MessageClass` and is not edited.
- `clutch/docs/host-contract.md`, section "Complete field inventory": append `roadmap_row: confirmed` to the `Config` `box_policy` default in the `config-fields` block, and append `roadmap_row` as the last `box_row` value in the `config-values` block. `tests/integration/test_host_contract.py` compares both with the code and is not edited.
- `docs/how-clutch-works.md`: in section 9.1, add `roadmap_row` to the class list with one sentence on what it carries. In section 9.3, say three things: for a `roadmap_row` message, Author embeds the row and its plan (whole under 40,000 characters, otherwise the two sections); the ticket uses the row's stem, kind, and priority, and evidence already under `tickets/<stem>/evidence/` is committed with it; the review-baseline condition does not apply to `roadmap_row`, while every other draft condition does. Nothing else in the file changes.
- Existing tests whose assertions flip:
  - `tests/integration/test_closed_sets.py::test_box_closed_sets_and_constants` and `::test_config_closed_sets_and_constants` gain `roadmap_row` in the class tuple, the class set, `BOX_POLICY_DEFAULTS` (`confirmed`), and the `BoxRow` set.
  - `tests/integration/test_config.py::test_valid_config_loads_from_cwd_with_shipped_defaults` gains `"roadmap_row": "confirmed"` in its `box_policy` dict.
  - `tests/integration/test_policy.py::test_bootstrap_without_a_go_or_with_phase_one_no_go_drafts_every_row` skips `roadmap_row` in its loop. Nothing else in that file changes.
  - `tests/integration/test_author.py::test_author_spec_requires_criteria_to_name_wrong_results` pins the new spec version. Nothing else in that file changes.
- New tests: `tests/unit/test_author_roadmap_row.py` and `tests/integration/test_roadmap_row_author.py`. The unit file builds its fakes in the file (or imports `MemoryJournal` and `message` from `tests/unit/test_retro_recurrence.py`). It reads and writes disk only under `tmp_path`, and it runs every new line in `clutch/box.py`, `clutch/policy.py`, and `clutch/author.py`, which have unit floors in `test-gate.toml`.

Scope out:
- Parsing `docs/roadmap.md`, choosing rows, filing `roadmap_row` messages, the `clutch roadmap author` verb, linking or striking rows, and the hand-test refusal: all in `roadmap-author`. No code in this ticket enqueues a `roadmap_row` message outside tests.
- `clutch/triage.py` and `clutch/specs/triage.md`. A roadmap message reaches Author through triage's existing recorded-`author`-verdict path, with no triage model call.
- Any other change to `start_state`'s conditions, to other policy rows, or to `box_policy` loading.
- `docs/roadmap.md`, `docs/roadmap-driver-plan.md`, `README.md`, `CLAUDE.md`, `AGENTS.md`, `vscode-clutchwork/`, and `clutch/observe.py`. The box view already draws any class through its help entry.

## Scope fence
- clutch/box.py
- clutch/config.py
- clutch/policy.py
- clutch/author.py
- clutch/specs/author.md
- clutch/help.py
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_author_roadmap_row.py
- tests/integration/test_roadmap_row_author.py
- tests/integration/test_closed_sets.py
- tests/integration/test_config.py
- tests/integration/test_policy.py
- tests/integration/test_author.py

## Acceptance criteria
1. `tests/unit/test_author_roadmap_row.py::test_roadmap_row_message_shape`:
   - `Message.model_validate` raises `ValidationError` for a `roadmap_row` message without a row, and for a `suggestion` message that carries one.
   - `Box(tmp_path / "box", LocalFileSystem()).enqueue(message_class="roadmap_row", origin="roadmap/sample-row", summary="row text", roadmap_row=row)` returns an id whose `Box.get(id).roadmap_row == row`.
   - A message JSON written without the `roadmap_row` key still loads, with `roadmap_row is None`.

   Ruled out: a roadmap message without its row, a row on another class, a row lost on the round trip, and old box files refused.
2. `tests/unit/test_author_roadmap_row.py::test_roadmap_row_ignores_only_the_baseline` calls `policy.start_state` with a config fake whose inventory is `["config.yaml"]` and whose `box_policy` is `BOX_POLICY_DEFAULTS`.
   - Row `roadmap_row`, `go=False`, fence `["clutch/author.py"]` returns `confirmed`. The same call with row `failure_report` returns `draft`.
   - Row `roadmap_row` with `go=False` returns `draft` for each of: `reopen=True`; `gate_bypass=["scope_fence"]`; fence `["config.yaml"]`; an empty inventory.
   - Row `roadmap_row` with `box_policy["roadmap_row"] = "draft"` and `go=True` returns `draft`.

   Ruled out: exempting another row from the baseline, dropping any other draft condition for `roadmap_row`, and ignoring the configured policy row.
3. `tests/unit/test_author_roadmap_row.py::test_plan_excerpt`:
   - `author.plan_excerpt` returns a 39,999-character plan unchanged.
   - For a plan of at least 40,000 characters with sections `## Status`, `## Target design` (holding a ```-fenced block with a line `## Role: x` and text after the fence), `## Risks`, `## Where each piece lives`, and `## Open decisions`, it returns exactly the Target design section followed by the Where each piece lives section. The fenced line and the text after the fence are kept. No Status, Risks, or Open decisions text appears.
   - For a plan of at least 40,000 characters with neither section, it returns a nonempty note that contains `Target design`, `Where each piece lives`, and `40,000`, and no line of the plan.

   Ruled out: a whole over-bound plan, a section cut at a heading inside a code fence, a wrong section, and an empty block.
4. `tests/unit/test_author_roadmap_row.py::test_gate_holds_roadmap_row_identity` builds an `AuthorGate` over `tmp_path` with an empty journal, a `roadmap_row` message for stem `sample-row` (kind `feature`, priority `P1`), and `validate_ticket` faked to return the reply's kind and priority.
   - A reply for stem `other-row` fails with a finding naming `sample-row`.
   - Kind `chore` fails with a finding naming `feature`.
   - Priority `P2` fails with a finding naming `P1`.
   - A matching reply passes while `tmp_path/tickets/sample-row/evidence/hand.txt` exists and `ticket.md` does not. After every failing check, `hand.txt` still exists.
   - Once `tickets/sample-row/ticket.md` exists, a matching reply fails with `already exists`.
   - For a `suggestion` message, a `tickets/<stem>/` directory without `ticket.md` still fails with `already exists`.

   Ruled out: a roadmap ticket under another stem, kind, or priority; refusing a row whose evidence is already in place; deleting that evidence; and relaxing the directory check for other classes.
5. `tests/unit/test_author_roadmap_row.py::test_author_embeds_row_and_plan` drives `author.author` with fakes, recording `render`'s inputs as `tests/unit/test_author.py::test_author_renders_inputs_and_passes_prior_review` does.
   - For a `roadmap_row` message whose plan `docs/sample-plan.md` is in the faked `ls_files` list, the inputs' `roadmap_row` equals `row.model_dump_json()` and `plan` equals `plan_excerpt` of the plan text.
   - For a `failure_report` message, both inputs are `none`.
   - When the plan is not in `ls_files`, `author` returns the faked `failure_declined` result with evidence naming `docs/sample-plan.md`, and `driver.run` is never called.

   Ruled out: a prompt without the row or plan, a prompt built from an untracked plan, and a render that drops the inputs for other classes (`clutch/specs/__init__.py::render` refuses mismatched inputs).
6. `tests/unit/test_author_roadmap_row.py::test_author_commit_carries_row_evidence` drives `author.author` to its commit with fakes. `driver.run` calls the stage's review with the reply and returns outcome `ok` with that reply. `driver.effects.run` awaits its action. `git.commit` records `only`. `git._run` answers the evidence listing with `tickets/sample-row/evidence/hand.txt\0`. The review is faked to approve.
   - For the roadmap message, the listing argv contains `--others` and `--exclude-standard`. `only` is exactly `["tickets/sample-row/ticket.md", "tickets/sample-row/evidence/hand.txt"]`, and the box resolution is `ticket` -> `sample-row`.
   - For a `failure_report` message, no `ls-files` call is made and `only` is the ticket path alone.

   Ruled out: a roadmap ticket committed without its evidence, and other classes sweeping extra files into their commit.
7. `tests/integration/test_roadmap_row_author.py::test_triage_authors_roadmap_row_confirmed_under_no_go`. Setup:
   - a repo from `tests/integration/test_drain.py::make_root` with `tests/integration/test_author.py::_routes`, `engine_plane_safety_inventory: [config.yaml]`, and one `NO_GO` `review_baseline` signal carrying the current `baseline_identity`;
   - a committed `docs/sample-plan.md` and an untracked `tickets/sample-row/evidence/hand.txt`;
   - a pending `roadmap_row` message for stem `sample-row` (kind `feature`, priority `P2`, plan `docs/sample-plan.md`), whose `author` verdict is recorded with `clutch/specs/triage.md`'s version.

   `main(["triage", id])` runs with a FakeLLM holding only `tests/integration/test_triage.py::author_reply("sample-row")` and an approving requisition review, and it returns 0. Then:
   - the Author prompt's `roadmap_row` block parses to the row and its `plan` block equals the plan text;
   - HEAD's subject is `clutch(sample-row): ticket` and HEAD lists exactly `tickets/sample-row/ticket.md` and `tickets/sample-row/evidence/hand.txt`;
   - the committed ticket has `state: confirmed` and `source: box:roadmap_row`, and the message resolves `ticket` -> `sample-row`;
   - no request has surface `triage`.

   Ruled out: a draft under NO_GO, a triage model call for a pre-approved row, evidence left untracked, and spec blocks that do not render.
8. `./dev.py test tests/integration/test_closed_sets.py tests/integration/test_config.py tests/integration/test_policy.py tests/integration/test_host_contract.py tests/integration/test_author.py tests/integration/test_help.py tests/unit/test_help.py` exits 0 with these values:
   - `box.MESSAGE_CLASSES` ends with `roadmap_row`;
   - `config.BOX_POLICY_DEFAULTS["roadmap_row"] == "confirmed"`, and `BoxRow` lists `roadmap_row` last;
   - `clutch/docs/host-contract.md`'s `config-fields` default and `config-values` `box_row` list carry `roadmap_row`;
   - `clutch/help.py`'s `box` vocabulary has a `roadmap_row` entry;
   - `clutch/specs/author.md`'s version is the next minor above its value on main.
9. The docs command in `## Verification` exits 0: `docs/how-clutch-works.md` section 9.1 names `roadmap_row`, and section 9.3 names `roadmap_row` and the word `baseline`.
10. The unit check (`clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`) passes, with `clutch/author.py`, `clutch/box.py`, `clutch/policy.py`, and `clutch/config.py` at or above their `test-gate.toml` floors.
11. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_author_roadmap_row.py tests/unit/test_author.py tests/unit/test_help.py
./dev.py test tests/integration/test_roadmap_row_author.py tests/integration/test_author.py tests/integration/test_closed_sets.py tests/integration/test_config.py tests/integration/test_policy.py tests/integration/test_host_contract.py tests/integration/test_help.py
uv run python -c "import pathlib; t = pathlib.Path('docs/how-clutch-works.md').read_text(); q = chr(96); m = t.split('### 9.1 Messages')[1].split('### 9.2')[0]; a = t.split('### 9.3 Author and starting state')[1].split('### 9.4')[0]; assert q + 'roadmap_row' + q in m; assert q + 'roadmap_row' + q in a and 'baseline' in a"
./dev.py test
```

## Definition of rejected
The branch is rejected if:
- it exempts any class but `roadmap_row` from the baseline condition, or drops another draft condition for `roadmap_row`;
- a `roadmap_row` message reaches a triage model call or a `clutch/specs/triage.md` change;
- Author can commit a roadmap ticket under a stem, kind, or priority other than the row's;
- any class's ticket commit carries files outside its own `tickets/<stem>/` directory;
- the gate or its cleanup deletes evidence it did not copy;
- it bumps `clutch/specs/author.md`'s major version;
- it adds the roadmap parser, the `roadmap` verb, or any edit to `docs/roadmap.md`.

## Time budget
- expected: 90m
- stuck: 180m
