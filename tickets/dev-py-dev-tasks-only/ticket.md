---
state: confirmed
source: human
priority: P2
kind: chore
---

## Depends on
- chupa-verdict-multi-stem
- verdict-submitted-message-verb
- engine-text-names-chupa-verbs

## Context
- dev.py
- tests/integration/test_dev.py
- tests/unit/test_readme.py
- CLAUDE.md#B. Session conduct (interactive chat in this repo)

## Goal / Why
`dev.py` declares 29 subcommands. Four of them are real work that belongs to this repo (`test`, `publish`, `vscode`, `vscode-package`, plus the bare `./dev.py` suite run). The other 25 re-declare a `chupa` verb's arguments in argparse and then run `uv run python -m chupa <verb>`, buying nothing: `uv run chupa <verb>` already bootstraps the same environment without `PATH` or an activated venv. The duplication has already rotted. `chupa stats --tree` exists at `chupa/__main__.py` line 257 but `dev.py` line 84-85 declares only `--window` and `--json`, so the flag is unreachable through the launcher, and five verbs (`covgate`, `doctor`, `migrate-config`, `retro`, `snapshot`) have no `dev.py` subcommand at all. `CLAUDE.md` section B makes this grow on purpose: "A missing command becomes a new `./dev.py` subcommand."

Engine paved roads that name `./dev.py confirm|reject|status|covmap` are not fixed here: `verdict-submitted-message-verb` and `engine-text-names-chupa-verbs` already rewrite every one of them to a bare `chupa <verb>`, and this ticket depends on both, so no hold's road names a deleted subcommand once this lands.

After this change `dev.py` is this repo's build-and-release launcher and nothing else, every ticket and engine task is a `chupa` verb in every host including this one, and the rule says so, so no new verb grows a launcher twin that can drift from it.

## Scope in / Scope out
- In: `dev.py`: delete the subparsers and dispatch branches for `core`, `covmap`, `triage`, `dismiss`, `prompt`, `docs`, `install`, `init-config`, `update-config`, `probe`, `suggest`, `status`, `stats`, `lint`, `new`, `order`, `run`, `serve`, `drain`, `kill`, `stop`, `watch`, `confirm`, `reject`, and `review`, and delete the now-unused `chupa()` helper and the final `else: chupa(args.task)` fallback. Keep the bare `./dev.py` suite run, `test`, `publish`, `vscode`, and `vscode-package` exactly as they behave now, including the `test` fast path at the top of `main` that passes leading options through. Update the module docstring to list only the surviving tasks and to say that every ticket and engine task is a `chupa` verb, run here as `uv run chupa <verb>`. Drop any import left unused by the deletions.
- In: `CLAUDE.md` section B, the `Command surface` bullet: it becomes the inverse rule. `./dev.py` covers only this repo's build and release tasks (`test`, `publish`, `vscode`, `vscode-package`); every ticket and engine task runs as a `chupa` verb, in this repo as `uv run chupa <verb>`. A missing engine task becomes a new `chupa` verb, never a `dev.py` subcommand; a missing build task becomes a new `dev.py` subcommand. This replaces the sentence added on 2026-11-14 that said engine text naming `chupa <verb>` "runs here as the matching `./dev.py` subcommand", which this change makes false. Keep the existing `Why`, and add that the launcher twins had already drifted (`stats --tree` unreachable, five verbs missing).
- In: `CLAUDE.md` section A and `AGENTS.md` section A, the `Guides name verbs, not command lines.` bullet (CLAUDE.md line 98, AGENTS.md line 90): drop "or `./dev.py` subcommand in this repo" from both, because engine verbs no longer have one. The two files carry this bullet identically and stay identical after the edit.
- In: `CLAUDE.md` and `AGENTS.md`, the `Launchers carry no process policy.` bullet (CLAUDE.md line 100, AGENTS.md line 92): it names `dev.py` as a launcher that picks a chupa verb and its flags, which is false once `dev.py` runs no chupa verb. Reword both to name only the extension as the launcher; keep the `drain-survives-editor-reload` incident in the `Why` unchanged. The `Verification uses ./dev.py test.` bullet in both files is unchanged and stays correct, because `test` survives. Both root files are edited in the same change, as the rule-homes rule requires.
- In: `README.md` lines 93-102, the `## Developing chupa` block: the engine rows (`new`, `lint`, `review`, `drain`, `status`, `confirm`/`reject`, `kill`) become `uv run chupa <verb>` rows, and the `./dev.py test [args]` row stays. Keep the block under the one `## Developing chupa` heading so `tests/unit/test_readme.py::test_dev_commands_only_in_developer_section` still holds.
- In: `chupa/docs/host-authoring.md` lines 12, 16, and 25: delete the three "In this repo, use `./dev.py new|lint|review` ..." parentheticals, because those subcommands no longer exist. The surrounding `chupa <verb>` sentences already say what to run.
- In: `chupa/docs/host-qwen.md` lines 49 and 66: delete the `(./dev.py install qwen in the chupa repo)` and `(./dev.py probe qwen in the chupa repo)` parentheticals for the same reason.
- In: `docs/how-chupa-works.md`: in the section 2.2 subcommand table (lines 87-113), delete every row for a deleted subcommand, keeping only the rows for `(none)`, `test`, `publish`, `vscode-package`, and `vscode`. Rewrite lines 29-31 so they say engine verbs run as `uv run chupa <verb>` in this repo too, and that `./dev.py` (section 2.2) covers only this repo's build tasks. The two later mentions at lines 459-460 become `chupa confirm` and `chupa reject`. Its three `./dev.py test` mentions and its `./dev.py vscode-package` mention are unchanged.
- In: `docs/roadmap.md`: the one `./dev.py confirm` mention becomes `chupa confirm`. Line 161, which cites `CLAUDE.md` section B's "a missing command becomes a subcommand", is rewritten to the new rule. Rows 6-8 (lines 299-301), including `dev-surface-completeness` ("`./dev.py` gains `doctor`, `retro`, ..."), are marked superseded by this ticket, because growing dev.py twins is exactly what this change stops. Its three `./dev.py test` mentions and the proposed build verbs (`release`, `publish`, `vscode-publish`, `visual-baseline`, `training-export`) are unchanged, because those are build tasks and stay on `dev.py`.
- In: `docs/journal-sql-refactor-plan.md`: the one `./dev.py status` mention becomes `chupa status`.
- In: `tests/integration/test_dev.py`: delete the ten tests that exercise deleted subcommands -- `test_drain_forwards_detach`, `test_suggest_forwards_summary`, `test_core_forwards_once`, `test_box_verbs_forward_all_ids_once`, `test_docs_forwards`, `test_probe_forwards`, `test_prompt_forwards_once`, `test_install_forwards_providers`, `test_update_config_forwards`, `test_init_config_forwards_write`. Keep the two `publish` tests, `test_test_passes_leading_options_to_pytest`, and the six `vscode_package` tests. Add `test_engine_verbs_are_not_dev_subcommands`: for each of `status`, `lint`, `new`, `confirm`, `drain`, `suggest`, running `dev.main()` with that argv raises `SystemExit` with code 2, and `dev.subprocess.run` is never called.
- In: `tests/unit/test_readme.py`: if `test_chupa_verbs_exist` reads the README's `chupa <verb>` rows, the new rows must satisfy it; adjust only what the new README rows force, and do not weaken either existing assertion.
- Out: `chupa/__main__.py` and every chupa verb's behavior; this ticket deletes launcher duplication and changes no engine code. Out: `chupa drain --detach`, which already lives in the verb (`drain-detach-in-engine`) and is what an operator or the extension passes; nothing here changes the flag or makes it a default. Out: putting a `chupa` console-script on `PATH`, a shim, an alias, or a deprecation message for the deleted subcommands; the paved road is `uv run chupa <verb>`, and recovery is `git revert`. Out: `vscode-chupa/`, whose commands come from the snapshot's argv, and the proposed future build verbs in the plan documents. Out: historical records under `tickets/` and `tickets/retro/`, which describe what was run at the time.

## Scope fence
- dev.py
- CLAUDE.md
- AGENTS.md
- README.md
- chupa/docs/host-authoring.md
- chupa/docs/host-qwen.md
- docs/how-chupa-works.md
- docs/roadmap.md
- docs/journal-sql-refactor-plan.md
- tests/integration/test_dev.py
- tests/unit/test_readme.py

## Acceptance criteria
1. `./dev.py test tests/integration/test_dev.py` exits 0. `test_engine_verbs_are_not_dev_subcommands` fails if any of `status`, `lint`, `new`, `confirm`, `drain`, or `suggest` is still accepted by `dev.py`, and fails if `dev.subprocess.run` is called for one of them. The surviving `publish`, `test`, and `vscode_package` tests still pass, so no build task was lost.
2. `./dev.py test tests/unit/test_readme.py` exits 0, so the README keeps its dev commands under the one `## Developing chupa` heading and every `chupa` verb it names exists.
3. `uv run chupa status` exits 0 and prints the projected state, showing the paved road works without `PATH` or an activated venv.
4. In `dev.py`, `CLAUDE.md`, `AGENTS.md`, `README.md`, `chupa/docs/`, `docs/how-chupa-works.md`, `docs/roadmap.md`, and `docs/journal-sql-refactor-plan.md`, no engine verb follows `./dev.py`. Checked by `grep -rnE "dev\.py (status|lint|new|order|run|serve|drain|kill|stop|watch|confirm|reject|review|suggest|triage|dismiss|prompt|docs|install|init-config|update-config|probe|core|covmap|stats)\b"` over those paths printing nothing and exiting 1. Proposed build verbs (`release`, `vscode-publish`, `visual-baseline`, `training-export`) stay as written wherever a plan document names them.
5. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/integration/test_dev.py
./dev.py test tests/unit/test_readme.py
./dev.py test
```

## Definition of rejected
Reject the branch if any of the following holds:
- a deleted subcommand keeps a shim, alias, deprecation warning, or passthrough instead of being gone;
- `test`, `publish`, `vscode`, or `vscode-package` changes behavior, or the bare `./dev.py` suite run stops working;
- any file under `chupa/` other than the two host guides is edited;
- a historical record under `tickets/` is rewritten;
- `CLAUDE.md` and `AGENTS.md` disagree after the change, or only one of them is edited.

## Time budget
- expected: 45m
- stuck: 90m
