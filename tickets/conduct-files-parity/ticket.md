---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- CLAUDE.md
- AGENTS.md
- clutch/hostfiles.py::CORE_TEMPLATE
- clutch/hostfiles.py::render
- clutch/hostfiles.py::refresh
- clutch/__main__.py::main
- tests/integration/test_hostfiles.py::test_core_template_order_and_budget
- tests/integration/test_hostfiles.py::test_core_golden_uses_branch_template
- tests/integration/test_hostfiles.py::test_core_activation_first_adoption
- tests/integration/test_fixture_host.py::test_fixture_profile_loads

## Goal / Why
`CLAUDE.md` says `AGENTS.md` is its curated subset for non-Claude agent CLIs (codex runs Implement here), and that a rule add, change, or removal touches both files in the same change. Outside the managed `clutch:core` block the two files have drifted. `AGENTS.md`'s `## Engine conduct` section lacks three rules that `CLAUDE.md`'s `## A. Engine conduct` carries: "The plan is the seed.", "Lean ticket frontmatter.", and "Phase order.". Its preamble also lacks the sentence "When a rule gains its gate, compress it to one line in the same change." So codex never reads that `CLUTCH_PLAN.md` is frozen, or that a phase waits for the previous phase's exit.

"Lean ticket frontmatter." is not a repo rule. It restates the managed block's frontmatter bullet ("Frontmatter holds only fields read by scheduling, gates, or authoring/triage policy. ..."), and the restatement is stale. It says "all other ordering lives in `priority`, never in prose", while the managed block in the same file says "put all other ordering in priority or `## Runs before`". Under `CLAUDE.md`'s rule "A rule has one of two homes", a rule every host follows lives only in `CORE_TEMPLATE`. Copying this bullet into `AGENTS.md` would put a contradiction into a file that has none today. So parity for this rule means deleting the stale copy from `CLAUDE.md`. The rule stays in force through the managed block, which both files already carry.

Separately, `CORE_TEMPLATE` says "`clutch docs` prints the installed paths of all host guides (authoring, running, config contract)". `clutch docs` (`clutch/__main__.py::main`, the `docs` branch) prints four guides, including `host-qwen.md`. The parenthetical is wrong, and it goes stale again with each new guide. Dropping it leaves "all host guides", which stays true. It also frees 38 bytes of the 8,192-byte template budget that `test_core_template_order_and_budget` enforces (7,855 to 7,817 bytes).

When this ticket is done:
- `AGENTS.md`'s repo `## Engine conduct` section and `CLAUDE.md`'s `## A. Engine conduct` section have identical bodies.
- `AGENTS.md`'s preamble carries the compress-to-one-line sentence.
- Neither file carries the stale "Lean ticket frontmatter." bullet.
- `CORE_TEMPLATE` no longer lists guides, and every managed block in this repo (`CLAUDE.md`, `AGENTS.md`, `hosts/fixture/CLAUDE.md`) matches it.

Rule homes, as `CLAUDE.md` "A rule has one of two homes" requires:
- "The plan is the seed.", "Phase order.", and the compress-to-one-line sentence are about working on clutch itself (`CLUTCH_PLAN.md`, its phases, these two files' rules). Their home is `CLAUDE.md` and `AGENTS.md`, outside the managed block.
- "Lean ticket frontmatter." is host-wide. Its home is `CORE_TEMPLATE`, which already carries it, so it leaves `CLAUDE.md`.
- The `clutch docs` sentence is host-wide and stays in `CORE_TEMPLATE`.

## Scope in / Scope out
Scope in:
- `clutch/hostfiles.py`, `CORE_TEMPLATE`: in the bullet that begins `- HARD: Never write a ticket from memory.`, delete exactly the 38 bytes ` (authoring, running, config contract)`. The sentence then reads "`clutch docs` prints the installed paths of all host guides; read them locally, never from a URL." No other byte of the template changes.
- `AGENTS.md`, outside the `clutch:core` markers only. Every added line is copied byte for byte from `CLAUDE.md`:
  - Append ` When a rule gains its gate, compress it to one line in the same change.` to the line `Every rule below is behavioral (no gate checks it yet): the prose is the only enforcement.`.
  - Insert the two-line `- **The plan is the seed.**` bullet (the bullet line and its `Why:` line). It goes directly after the `- **A rule has one of two homes.**` bullet and before `- **All git through \`git.py\`.**`.
  - Append the two-line `- **Phase order.**` bullet as the last bullet, after `- **The journal is the record, never a debug log.**`.
- `CLAUDE.md`, outside the `clutch:core` markers only: delete the two-line `- **Lean ticket frontmatter.**` bullet (the bullet line and its `Why:` line).
- Refresh the managed blocks from the edited template with the `core` verb. Run `uv run clutch core` at the repo root, which rewrites the blocks in `CLAUDE.md` and `AGENTS.md`. Then run `uv run clutch core` again with `hosts/fixture` as the working directory, which rewrites `hosts/fixture/CLAUDE.md`, the only conduct file that fixture's config routes. Never hand-edit a managed block.
- `tests/integration/test_hostfiles.py`: regenerate `GOLDEN` with the module's own `if __name__ == "__main__":` block (`uv run python -m tests.integration.test_hostfiles`). No other line of the file changes.
- `tests/unit/test_hostfiles.py` is fenced only because `clutch/hostfiles.py` has a `[coverage.files]` floor in `test-gate.toml`. Edit it only if the template change breaks it.

Scope out:
- `## B. Session conduct` in `CLAUDE.md` stays out of `AGENTS.md`: those rules govern interactive chat, which non-Claude CLIs do not run here. `AGENTS.md`'s first three paragraphs stay as they are, because they are the curated wording for that audience.
- The other `CLAUDE.md` section A rules that restate a `CORE_TEMPLATE` rule ("Simplest thing that satisfies the ticket.", "File second problems; never fold them in.", "Read before write.") are in both files already. They stay; removing them is separate work.
- The managed block's own frontmatter bullet, and every other `CORE_TEMPLATE` bullet.
- `clutch/__main__.py` and the `docs` verb's guide list; `docs/roadmap.md`; `CLUTCH_PLAN.md`; `hosts/fixture/` beyond its `CLAUDE.md` managed block.
- Any new test or gate that checks the two files stay in parity.

## Scope fence
- clutch/hostfiles.py
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- tests/integration/test_hostfiles.py
- tests/unit/test_hostfiles.py

## Acceptance criteria
1. The first `uv run python -c` command in `## Verification` exits 0. That command checks four things. First, the body of `CLAUDE.md`'s `## A. Engine conduct` section (up to `## B. `) equals, after stripping, the body after `AGENTS.md`'s last `## Engine conduct` heading. Second, `AGENTS.md` text after `<!-- clutch:core end -->` contains `When a rule gains its gate, compress it to one line in the same change.`. Third, `AGENTS.md` contains `- **The plan is the seed.**` and `- **Phase order.**`. Fourth, neither file contains `Lean ticket frontmatter`. Ruled out: today's files, which fail the equality check; a missing or misplaced bullet; the preamble sentence left out; the stale bullet copied into `AGENTS.md` instead of removed from `CLAUDE.md`; and parity reached by deleting "The plan is the seed." or "Phase order." from `CLAUDE.md`.
2. The second `uv run python -c` command in `## Verification` exits 0. That command checks two things. First, `clutch.hostfiles.CORE_TEMPLATE` contains `prints the installed paths of all host guides; read them locally, never from a URL.`. Second, it does not contain `(authoring, running, config contract)`. Ruled out: the parenthetical left in place, and the whole `clutch docs` sentence deleted with it.
3. `./dev.py test tests/integration/test_hostfiles.py tests/unit/test_hostfiles.py` exits 0.
   - `test_core_golden_uses_branch_template` fails if `GOLDEN` was not regenerated from the edited template.
   - `test_core_activation_first_adoption` fails if the managed block in `CLAUDE.md` or `AGENTS.md` is not exactly `hostfiles.render` of the edited template, whether stale or hand-edited.
   - `test_core_template_order_and_budget` fails if the template exceeds 8192 bytes or stops starting with `## Ticket authoring`.
4. `./dev.py test tests/integration/test_fixture_host.py` exits 0. `test_fixture_profile_loads` fails if `hosts/fixture/CLAUDE.md`'s block was not refreshed, because `classify_core` then reports it `drifted`, not `current`.
5. The `core_drift` gate passes at Check. The committed `CLAUDE.md` and `AGENTS.md` classify `current` against the branch's `CORE_TEMPLATE`, and neither file's text outside the block is refused as a process override.
6. `./dev.py test` exits 0.

## Verification
```
uv run python -c "import pathlib; c = pathlib.Path('CLAUDE.md').read_text(); a = pathlib.Path('AGENTS.md').read_text(); assert c.split('## A. Engine conduct\n', 1)[1].split('## B. ', 1)[0].strip() == a.rsplit('## Engine conduct\n', 1)[1].strip(); assert 'When a rule gains its gate, compress it to one line in the same change.' in a.split('<!-- clutch:core end -->', 1)[1]; assert '- **The plan is the seed.**' in a and '- **Phase order.**' in a; assert 'Lean ticket frontmatter' not in c + a"
uv run python -c "from clutch.hostfiles import CORE_TEMPLATE as t; assert b'prints the installed paths of all host guides; read them locally, never from a URL.' in t; assert b'(authoring, running, config contract)' not in t"
./dev.py test tests/integration/test_hostfiles.py tests/unit/test_hostfiles.py
./dev.py test tests/integration/test_fixture_host.py
./dev.py test
```

## Definition of rejected
- Any managed block is edited by hand, or is not byte-equal to `hostfiles.render` of the branch's `CORE_TEMPLATE`.
- `CORE_TEMPLATE` changes by anything other than the 38-byte deletion.
- `CLAUDE.md` changes outside its managed block by anything other than deleting the "Lean ticket frontmatter." bullet.
- `AGENTS.md` changes outside its managed block by anything other than the one appended sentence and the two copied bullets.
- Any of these happens: a section B rule is copied into `AGENTS.md`; the copied bullets are reworded; the stale frontmatter bullet is kept or corrected in place instead of removed.
- A parity test, lint, or gate is added.
- `clutch/__main__.py`, `docs/roadmap.md`, or `CLUTCH_PLAN.md` changes.

## Time budget
- expected: 25m
- stuck: 75m
