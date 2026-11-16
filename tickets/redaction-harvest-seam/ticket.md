---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
- none

## Context
- clutch/runner.py::harvest
- clutch/runner.py::harvest_failure
- clutch/redact.py
- clutch/driver.py::Spool
- clutch/retro.py::Retro.commit_report
- clutch/seams.py::CommandNotifications
- clutch/llmeffect.py::llm_call
- clutch/enginelog.py
- clutch/artifacts.py::Finding
- clutch/artifacts.py::Harvest
- clutch/stages.py::ScopeFenceGate
- tests/unit/test_stale_running.py::test_reap_reconciles_with_harvest
- docs/how-clutch-works.md#8.5

## Goal / Why
Configured secret values are meant to be redacted from every captured stream at the write seam (CLAUDE.md, "The journal is the record"). `attempts/<n>/harvest.json` is the one captured record that skips it: `clutch/runner.py::harvest` builds the `Harvest` and writes `artifact.model_dump_json(indent=2)` through `ctx.fs.write` with no redactor, and `lift_outbox` then commits it to main as `clutch(<stem>): harvest`, where the next attempt's prompt and the diagnosis prompt read it. Two of its inputs are never scrubbed upstream: `diff_stat` is raw `git diff --stat` output, and findings such as `clutch/stages.py::ScopeFenceGate`'s carry the changed path verbatim in `path` and `message`. A probe at HEAD that calls `harvest` with a fake git whose diff stat names `clutch/<secret>.py` and a redactor holding that secret writes the secret into `harvest.json` in clear text.

The writer checklist in `clutch/redact.py`'s module docstring, which says to extend it "in the same change that adds a writer of a captured stream", still says "harvest serialization: not built" and calls the LLM effect result the journal's "one secret-bearing producer", and it omits two writers that already scrub (the retro report and notification output).

After this change `harvest` passes the serialized record through the run's redactor (`ctx.driver.redactor`, the one every production `StageContext` already carries and `harvest_failure` already uses) before it writes, so every field, including any field `Harvest` gains later, reaches disk scrubbed; the checklist names each writer that exists; and `docs/how-clutch-works.md` section 8.5 lists harvests among the scrubbed outputs.

## Scope in / Scope out
Scope in:
- `clutch/runner.py::harvest`: the one `ctx.fs.write` call writes `ctx.driver.redactor.scrub(artifact.model_dump_json(indent=2))` plus the trailing newline, encoded, instead of the unscrubbed dump. This is the pattern `clutch/driver.py::Spool.write` and `clutch/retro.py::Retro.commit_report` use: scrub the text at the write. Nothing else in `harvest` changes: no field is scrubbed separately, the tails are still cut at `HARVEST_TAIL_CHARS`, and the `lift_outbox` call is unchanged.
- `clutch/redact.py` module docstring only (the `Redactor` class does not change). Rewrite the checklist so it lists the writers that exist at HEAD:
  - keep the `clutch/driver.py` `Spool`, `clutch/enginelog.py` `EngineLog`, and `clutch/providers.py` `CliAdapter.invoke` lines as they are;
  - replace "harvest serialization: not built" with a line naming clutch/runner.py `harvest` (attempts/<n>/harvest.json);
  - add a line naming clutch/retro.py `Retro.commit_report` (the retro report) and a line naming clutch/seams.py `CommandNotifications` (notify stdout and stderr, scrubbed before the effect result is journaled);
  - replace the journal line's "NOT YET WIRED; its one secret-bearing producer ..." with the truth: clutch/journal.py does not scrub, so each producer that journals captured text scrubs it before the append, naming clutch/llmeffect.py `llm_call` and clutch/runner.py `harvest_failure` (the `harvest_failed` signal).
- `docs/how-clutch-works.md` section 8.5 ("Spend and redaction") only: the redaction bullet's list "spools, the engine log, provider captures, notifications, and retro reports" gains harvests (`attempts/<n>/harvest.json`). Section 6.2 and the rest of the file do not change.
- New file `tests/unit/test_harvest_redaction.py`, built like `tests/unit/test_stale_running.py::test_reap_reconciles_with_harvest`: a `SimpleNamespace` context whose `config.state_dir` and `repo` name directories that do not exist (so the spool and provider-capture globs find nothing and nothing is read), `worktree` a lambda returning a path under a nonexistent root, `git` an object whose async `diff_stat` returns a stat line naming `clutch/<SECRET>.py`, `fs` an in-memory recorder of `write(path, data)` calls, and `driver=SimpleNamespace(redactor=Redactor({"FAKE_KEY": SECRET}))`; `runner.lift_outbox` is monkeypatched to an `AsyncMock`; the test calls `asyncio.run(runner.harvest(...))` with one `Finding(code="scope_fence", path=f"clutch/{SECRET}.py", message=f"clutch/{SECRET}.py is outside ...", paved_road=...)`. It spawns no process and writes no file.

Scope out: scrubbing individual `Harvest` fields or cutting tails after scrubbing; the `Harvest` model and its fields; `ScopeFenceGate` and every other finding producer, which stay as they are because the write seam covers them; `lift_outbox` and every other writer; the `Redactor` class, including any structured or JSON-aware scrub (a secret containing a character JSON escapes survives a serialized scrub, as it already does in `EngineLog`; filed separately); `docs/how-clutch-works.md` section 6.2; `tests/integration/test_harvest.py` and the other harvest tests, whose fixtures plant no secret in a harvested field and so see byte-identical output.

## Scope fence
- clutch/runner.py
- clutch/redact.py
- docs/how-clutch-works.md
- tests/unit/test_harvest_redaction.py

## Acceptance criteria
1. `tests/unit/test_harvest_redaction.py::test_harvest_json_carries_no_configured_secret` asserts that the bytes `harvest` passes to `fs.write` for `attempts/0/harvest.json` do not contain `SECRET`. Ruled out: the secret in clear text in `diff_stat`, `findings[0].path` and `findings[0].message`, which is HEAD's result.
2. The same test parses those bytes with `Harvest.model_validate_json` and asserts `"[REDACTED:FAKE_KEY]"` appears in `diff_stat`, in `findings[0].path` and in `findings[0].message`, and that `findings[0].code == "scope_fence"` and `terminal == "gate_failed"`. Ruled out: a record that no longer validates as `Harvest`, and a secret removed by blanking or dropping the field rather than replacing it with the redaction marker.
3. The same test asserts `runner.lift_outbox` was awaited once with `only="attempts/0/harvest.json"`. Ruled out: a fix that skips or reroutes the lift.
4. `./dev.py test tests/integration/test_harvest.py tests/integration/test_harvest_orphans.py` exits 0 unchanged: harvests whose inputs carry no configured secret are written byte-for-byte as before.
5. The `## Verification` command that reads `clutch.redact.__doc__` exits 0: the docstring no longer contains `not built`, `NOT YET WIRED`, or `one secret-bearing producer`, and contains ``clutch/runner.py `harvest` ``, ``clutch/retro.py `Retro.commit_report` ``, ``clutch/seams.py `CommandNotifications` ``, ``clutch/llmeffect.py `llm_call` `` and ``clutch/runner.py `harvest_failure` ``. Ruled out: the stale checklist left in place, and a checklist that drops the journal line instead of correcting it.
6. The same command asserts that the text of `docs/how-clutch-works.md` from the `### 8.5 ` heading to the next `## ` heading contains `harvest`. Ruled out: the redaction list left without harvests, and section 8.5 deleted.
7. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_harvest_redaction.py
./dev.py test tests/integration/test_harvest.py tests/integration/test_harvest_orphans.py
uv run python -c "import pathlib, clutch.redact as r; d = r.__doc__; assert all(s not in d for s in ('not built', 'NOT YET WIRED', 'one secret-bearing producer')), d; assert all(s in d for s in ('clutch/runner.py `harvest`', 'clutch/retro.py `Retro.commit_report`', 'clutch/seams.py `CommandNotifications`', 'clutch/llmeffect.py `llm_call`', 'clutch/runner.py `harvest_failure`')), d; t = pathlib.Path('docs/how-clutch-works.md').read_text(); assert '### 8.5 ' in t; s = t.split('### 8.5 ', 1)[1].split('\n## ', 1)[0]; assert 'harvest' in s, s"
./dev.py test
```

## Definition of rejected
The branch is rejected if it scrubs selected `Harvest` fields instead of the serialized record at the write, if it adds a method, parameter, or constructor to `Redactor` or a new seam or config knob, if it builds a second `Redactor` inside `harvest` instead of using `ctx.driver.redactor`, if it changes the `Harvest` model, `lift_outbox`, or any finding producer, or if the new unit test spawns a process, runs git, or writes a file.

## Time budget
- expected: 25m
- stuck: 60m
