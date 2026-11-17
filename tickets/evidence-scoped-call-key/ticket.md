---
state: confirmed
source: human
priority: P0
kind: bug
---

## Depends on
none

## Context
- clutch/providers.py::CliAdapter.invoke
- clutch/providers.py::CallCapture
- clutch/evidence/schema.py::Start
- clutch/evidence/store.py::EvidenceStore.write_record
- clutch/evidence/store.py::EvidenceStore.read_record
- clutch/llmeffect.py
- clutch/supervise_idle.py
- docs/evidence-trail-plan.md#2. Envelope schema
- docs/evidence-trail-plan.md#5. Versioning and extension
- tests/unit/test_evidence_envelope.py::config
- tests/unit/test_evidence_envelope.py::stream
- tests/unit/test_evidence_envelope.py::Exec
- tests/unit/test_evidence_envelope.py::Rig
- tests/unit/test_evidence_envelope.py::test_start_record_precedes_spawn
- tests/regress_stale_running.py
- tests/integration/test_regress_scripts_guarded.py::test_regression_scripts_are_guarded

## Goal / Why
The idle-point supervisor step (roadmap rows 89, 96 and 114) fails on its first real-provider call. `clutch/supervise_idle.py` calls `supervise_step(..., key_scope="sup")`, so every Rework call it makes, and every requisition review that Rework runs, is keyed `llm/<stem>/sup-<n>/<surface>/<attempt>/<call>` (`clutch/llmeffect.py::scoped_seq` and `llm_key`). `clutch/providers.py::CliAdapter.invoke` splits that key and writes `"run_seq": int(run_seq)` into `start.json`, which raises `ValueError: invalid literal for int() with base 10: 'sup-3'` before the provider CLI starts (`tickets/evidence-scoped-call-key/evidence/evidence.txt`). `clutch/thresh.py` then journals the call as an `unclassified` provider outcome, which counts toward that provider's breaker. `clutch/evidence/schema.py::Start.run_seq` is a strict `int`, so even the segment string would be refused. The step has not fired yet: the journal has no `sup-` call key. Only `FakeLLM` covers scoped keys today (`tests/unit/test_key_scope.py`), and it never reaches `CliAdapter.invoke`. Reported as box-000730.

After this ticket, a key-scoped call runs its provider and leaves a `start.json` and `end.json` that validate. The record's `id` is the exact effect key, and `run_seq` is that key's run segment: an integer when the key is unscoped, as today, and the scoped string (such as `sup-3`) otherwise.

## Scope in / Scope out
In:
- `clutch/evidence/schema.py::Start`: `run_seq` becomes `int | str`. Nothing else in the module changes. The schema id stays `clutch.evidence.call/1.0`. Every record written before this change still validates and reads back the same, and no record with a string `run_seq` exists, because a scoped call has always failed before its `start.json`. `json_schema` is exposed by no command, so no outside reader expects only integers. `EvidenceStore.write_record` and `read_record` need no change.
- `clutch/providers.py::CliAdapter.invoke`: in the `start.json` dict, `run_seq` is `int(run_seq)` when the segment is all decimal digits, and otherwise the segment string unchanged. `id` stays `capture.key`, and `group`, `surface`, `attempt` and `call` are built as today. Nothing else in the file changes.
- New `tests/unit/test_evidence_scoped_key.py`, one test that reuses `Rig` and `ENV` from `tests/unit/test_evidence_envelope.py` (import them, add nothing to that file). It runs `llm_call(Effects(rig.journal), rig.client, rig.request(), Redactor.from_config(rig.cfg, ENV), ticket="ticket", stem="ticket", run_seq=scoped_seq("sup", 3), attempt=2, call_seq=4)`, so the call goes through `ProviderLLM.admitted_call` into `CliAdapter.invoke` with the fake exec. It asserts the result text is `answer`. It reads back `start.json` and `end.json` for `llm/ticket/sup-3/review/2/4` through `rig.store.read_record` and checks `start.id`, `start.run_seq == "sup-3"`, `run_seq` in the raw `start.json` JSON, `(group, surface, attempt, call) == ("ticket", "review", 2, 4)` and `end.exit.status == "ok"`.
- New reproducer `tests/regress_evidence_scoped_call_key.py`, modelled on `tests/regress_stale_running.py`. All work is inside `main()` under an `if __name__ == "__main__":` guard, as `tests/integration/test_regress_scripts_guarded.py` requires. `main()` inserts the repo root on `sys.path`, builds `Rig(Path(tmpdir), patch)` inside `tempfile.TemporaryDirectory()` and `pytest.MonkeyPatch.context()`, and makes the same scoped `llm_call` as the unit test.
  - A `ValueError` whose message contains `invalid literal for int()` (the defect) prints `{"regression_result": "defect"}` and exits 1.
  - A completed call prints `{"regression_result": "pass"}` and exits 0 when the read-back `start.id` is the key, `start.run_seq == "sup-3"`, `end.exit.status == "ok"`, and the fake exec saw a non-git argv (the provider spawned). Otherwise it prints `defect` and exits 1.
  - Any other exception, including an import failure, prints a traceback to stderr and `{"regression_result": "error"}`, and exits 2.
  Diagnostics go to stderr only. A prototype on a copy of `6e6d9154` printed `defect` (exit 1) before the two code edits and `pass` (exit 0) after them.
- `docs/evidence-trail-plan.md`, section "2. Envelope schema", "Notes on fields": the sentence "`run_seq` is the journal's (`clutch/driver.py:277`)." becomes false for a scoped call. It changes to say that `run_seq` is the key's run segment: the journal's run sequence as an integer, or, for a key-scoped call such as the idle supervisor's (`clutch/llmeffect.py::scoped_seq`), the scoped string such as `sup-3`. The rest of that bullet and the document stay as they are, including the `start.json` example, whose `"run_seq": 3` stays a valid unscoped record.

Rejected, simpler on paper but larger in effect: keep `run_seq` an integer and add a nullable `scope` field. That adds a field to `Start`, which `docs/evidence-trail-plan.md` section 5 makes a minor schema bump (`clutch.evidence.call/1.1`). That bump changes the `schema` literal that `tests/unit/test_evidence_schema.py` writes and that `evidence-record-doc-section` documents. The scope prefix would also have to be parsed back out of the key, and the record's fields would no longer join back into `id`. Also rejected: constraining the string form to `scoped_seq`'s pattern. That copies the scope rule into the schema, and drift between the two would bring back this same failure, a strict `start.json` refusal before spawn.

Merge order:
- `cli-group-config` merged at `3415221a`. `cli-group-provider` (in flight) fences `clutch/providers.py` and changes only string literals: the gemini listing problem, the `suggest_config` header, and the preflight's two install roads (lines 779, 840, 944 and 968 at `6e6d9154`). The `run_seq` line in `CliAdapter.invoke` is line 418, so the hunks do not touch. Either merge order applies cleanly, and no criterion here or there changes.
- `evidence-record-doc-section` (row 149, confirmed, unmerged) fences only the how-clutch-works document, which this ticket leaves alone. Its F6 says `id`, `group`, `run_seq`, `surface`, `attempt` and `call` "come from the key", which stays true under this fix, and its Definition of rejected keeps scoped-key records out of its section. If it merges first, no sentence of its section 10.4 becomes false. If this ticket merges first, its section still describes the code without naming scoped keys. Neither ticket's text or criteria change.

Out:
- The how-clutch-works document: no sentence there describes `run_seq`'s type or scoped keys at `6e6d9154`.
- `clutch/llmeffect.py`, `clutch/supervise_idle.py`, `clutch/thresh.py`, `CallCapture` and the key format. `End`, `Event` and every other `Start` field.
- `tests/unit/test_evidence_envelope.py`, `tests/unit/test_evidence_schema.py`, `tests/unit/test_key_scope.py` and `tests/integration/test_evidence_envelope.py`: they pass unchanged. No test reads document text (box-000676).
- The cause, that `CliAdapter.invoke` re-parses a joined key whose shape `llm_key` owns and no test drives a scoped key past `FakeLLM`, is filed separately in the Suggestion Box.

## Scope fence
- clutch/evidence/schema.py
- clutch/providers.py
- docs/evidence-trail-plan.md
- tests/unit/test_evidence_scoped_key.py
- tests/regress_evidence_scoped_call_key.py

## Acceptance criteria
1. `./dev.py test tests/unit/test_evidence_scoped_key.py` exits 0. Its test makes a `run_seq=scoped_seq("sup", 3)` call through `llm_call` and `ProviderLLM.admitted_call` into `CliAdapter.invoke`, and checks that the call returns `answer` and that `start.json` and `end.json` for `llm/ticket/sup-3/review/2/4` read back with `start.id` equal to that key, `start.run_seq == "sup-3"` in the model and in the raw JSON, and `end.exit.status == "ok"`. Ruled out: a `ValueError` from `int("sup-3")` before spawn, a record that drops the scope and stores `3`, and a record keyed apart from the effect key. At `6e6d9154` the test fails with that `ValueError`.
2. `./dev.py test tests/unit/test_evidence_envelope.py tests/unit/test_evidence_schema.py tests/unit/test_evidence_rusage_record.py tests/unit/test_key_scope.py tests/integration/test_evidence_envelope.py tests/integration/test_regress_scripts_guarded.py` exits 0 with none of those files changed. `test_start_record_precedes_spawn` still reads `run_seq == 3` for the unscoped key `llm/ticket/3/review/2/4`. Ruled out: writing every run segment as a string such as `"3"`, and a reproducer that does work at import.
3. `uv run python tests/regress_evidence_scoped_call_key.py` prints `{"regression_result": "pass"}` and exits 0 on the branch, and prints `{"regression_result": "defect"}` and exits 1 at the merge base with the reproducer copied over. Ruled out: a fix that leaves a scoped call failing before spawn.
4. `git diff main...HEAD -- clutch/evidence/schema.py` changes only the `Start.run_seq` annotation, to `int | str`: no field is added and the schema id stays `clutch.evidence.call/1.0`. `git diff main...HEAD -- clutch/providers.py` changes only the `run_seq` entry of the `start.json` dict in `CliAdapter.invoke`.
5. `git diff main...HEAD -- docs/evidence-trail-plan.md` changes only the `run_seq` sentence in the "Notes on fields" list of section 2, which then names both the integer form and the scoped string form with `clutch/llmeffect.py::scoped_seq`.
6. `git diff --name-only main...HEAD` lists only the five fenced files, and `./dev.py test` exits 0.

## Verification
```
./dev.py test
uv run python tests/regress_evidence_scoped_call_key.py
```

## Definition of rejected
The branch is rejected if it:
- changes the `schema` id, adds a field to `Start`, or changes `id` away from the exact effect key;
- writes an unscoped `run_seq` as a string, or drops or rewrites the scope of a scoped one;
- catches or skips the `start.json` write so a scoped call runs without a record;
- changes `clutch/llmeffect.py`, `clutch/supervise_idle.py`, `clutch/thresh.py`, the key format, or any file outside the fence;
- adds a test to an existing test file or a test that reads document text.

## Time budget
- expected: 15m
- stuck: 30m

## Regression
```
uv run python tests/regress_evidence_scoped_call_key.py
```
- carries: tests/regress_evidence_scoped_call_key.py
