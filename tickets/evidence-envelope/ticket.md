---
state: draft
source: human
priority: P1
kind: feature
---

## Depends on
- evidence-store
- fs-seam-mkdir-remove
- fs-seam-read-size
- git-tree-id

## Context
- docs/evidence-trail-plan.md#1. Record layout
- docs/evidence-trail-plan.md#2. Envelope schema (`clutch.evidence.call`, version 1.0)
- clutch/evidence/schema.py
- clutch/evidence/store.py
- clutch/providers.py::routed_conduct_paths
- clutch/providers.py::CliAdapter
- clutch/providers.py::ProviderLLM
- clutch/llmeffect.py
- clutch/runner.py::harvest
- clutch/driver.py::Driver._run
- clutch/redact.py
- tests/integration/test_daemon_composition.py::ScriptFS
- tests/integration/test_daemon_composition.py::ScriptExec
- tests/integration/test_providers.py::FakeExec
- tests/integration/test_providers.py::PreflightExec
- tests/integration/test_provider_capture_overwrite.py
- tests/unit/test_harvest_redaction.py

## Goal / Why
Raw provider captures are still written by `CliAdapter._write_capture` under `spools/providers/<stem>/<provider>-NNNN/` (and `spools/probe/` for `clutch probe`), numbered by `capture_sequence` from a directory listing. The merged P0 `provider-capture-overwrite` only patched that numbering. This ticket is its cause fix and roadmap row 29: every capture is keyed by the journal identity of the call it captures, the call key `llm/<group>/<run_seq>/<surface>/<attempt>/<call>`, so no later process can write over it. When it is done:

- Every model call that has a journal key leaves one record in the evidence store (`clutch/evidence/`, merged in `evidence-store`). `start.json` is written before the process starts and `end.json` at exit, failure, kill or timeout. The redacted prompt, stdout, stderr and the stdout arrival times are blobs, and the tree ids come through `Git.tree_id` and `Git.tree_changes` (`git-tree-id`).
- The store reads through the `FileSystem` seam (`fs.read_bytes`, `fs.size` from `fs-seam-read-size`), so an in-memory rig never touches the real disk.
- The old writer is gone: no `capture_dir`, `capture_sequence`, `_seq` or `_write_capture`, and nothing writes `spools/providers/` or `spools/probe/`. Calls with no journal key (preflight probes, `clutch probe`, the raw `ProviderLLM.call`) leave no record.
- Harvest's `events_tail`, the one production reader of the old captures, comes from the newest record of the ticket's calls.
- Each per-call `engine.log` event carries `call_key`, so a log line leads to its record.

Two row items are not delivered. `rusage` is written as `null`: `SubprocessExec` spawns through `asyncio.create_subprocess_exec`, whose child watcher reaps the child with `os.waitpid` before the seam could call `os.wait4`, and moving the spawn off asyncio would also break the `tests/waiting.py::ready_before_returning_spawn` timing hook. A follow-up is filed to the Suggestion Box. The prune is not logged to the engine log, because the adapter holds no `EngineLog`.

## Scope in / Scope out
Scope in:

`clutch/providers.py`:
- The call key reaches the adapter. `ProviderLLM.admitted_call`'s `operation(served)` builds a frozen `CallCapture` dataclass, defined in this module: `key` (its `call_key`), `ticket` (its `ticket`), `candidates` (provider names of the route it admitted, after the budget filter, in order), `reason`, `git` and `clock`. It passes it as `capture=` through `ProviderLLM._invoke` to `CliAdapter.invoke(req, model, *, consumer=None, capture=None)`. `reason` is `first` when the served candidate is `route[0]`. It is `failover` when `route[0]`'s provider has an open breaker (`session.thresh.breakers()`) or `session.unavailable(name)[0]` is true. Otherwise it is `spill`. `git` is a `Git` built from `ProviderLLM`'s own `exec_`, `child_env(env, config)`, `PREFLIGHT_TIMEOUT_S` and a `CommitLock(config.state_dir, clock=session.clock, sleep=session.sleep)`. It is built only when a keyed call needs it, so the keyless session stubs in `tests/unit/test_preflight_parallel.py` and `tests/integration/test_fixture_host.py` need no clock. `clock` is `session.clock`. `ProviderLLM.__init__`'s signature does not change, and `exec.run` gets no new keyword.
- Every call, keyed or not, writes its scrubbed prompt with `fs.write` to `<state_dir>/evidence/scratch/<uuid4 hex>.md`. It passes that path as `stdin_path=prompt`; the local name `prompt` stays, because `tests/integration/test_host_contract.py` pins `stdin_path=prompt` in `CliAdapter.invoke`'s source. A keyed call's temporary index is `<same name>.index` in the same directory. The stdin file is written first, so the directory exists before git runs. Both files are removed with `fs.remove` on every path when the call ends.
- The record is stored under the call key. If `calls/<escaped key>` already exists (an intent re-executed after a crash), the store key is `<key>#2`, then `#3` and so on. The record's `id` is always the journal key, and no record file is ever overwritten. The store is `EvidenceStore(config.state_dir, fs, fs.read_bytes, fs.size, redactor.scrub)`.
- `start.json` is written with `write_record` after `tree_before` and before `exec.run`:
  - `id` is the journal key. `group`, `run_seq`, `surface`, `attempt` and `call` are its five segments after `llm/` (`run_seq`, `attempt` and `call` as ints). `stem` is the capture's `ticket` (`null` for a ticketless call).
  - `engine.version` is `importlib.metadata.version("clutchwork")`, read by a module-level `engine_version()` in this module, because an installed clutch has no git tree to hash. `engine.spec` is `<surface>.md`. `engine.spec_version` is that spec's frontmatter `version` under `clutch/specs/`, read by a module-level `spec_version(surface)` in this module. `tests/unit/test_evidence_envelope.py` replaces both functions with fakes, so it reads neither package metadata nor a repo file; the integration test checks the real values.
  - `route`: `tier` and `effort` come from the request, `candidates` and `reason` from the capture, and `chosen` is the served provider's name. `config_sha` is the sha256 hex digest of `repr(snapshot_config(config))`, so a `Config` and its snapshot hash alike.
  - `provider`: `name`, `adapter` (the class name), `kind` and `package` come from the provider config. `cli_version` is the version this process's `preflight` read from `<binary> --version` with `installed_version`, cached on the adapter (`null` when preflight has not run). `billing` is `local` for an adapter with `uses_base_url`, `metered` when the provider declares `auth`, and otherwise `subscription`.
  - `model.requested` is the model.
  - `process`: `argv` is scrubbed element by element. `env_names` is the sorted names of the call env. `cwd`, `timeout_s` (an int), `writes` and `isolated: false`. `conduct_file` is the file name that `routed_conduct_paths` selects, and one helper serves both.
  - `repo`: `main_sha` is `rev_parse(cwd, "main")`, `base_sha` is `rev_parse(cwd, "HEAD")` and `tree_before` is `tree_id(cwd, index)`.
  - `prompt`: the blob of the scrubbed prompt, with its `chars` and `bytes`.
  - `clock`: `wall_start` is `render_ts(clock())`. `mono_start_ns` is the integer nanoseconds of the same reading, because the `Clock` seam is the engine's only clock.
- For a keyed call, or one with a consumer, `on_stdout_line` is passed. Its callback appends each line's offset from `mono_start_ns`, then forwards the line to the consumer if there is one. A keyless call without a consumer still passes no `on_stdout_line`.
- `end.json` is written once on every path that wrote `start.json`, before the result returns or the exception (including `ProviderCallError`) propagates:
  - `exit`, after `exec.run` returns: `ok` (rc 0), `nonzero` (rc > 0), or `killed` (rc < 0, with `signal` = -rc). On an exception from `exec.run`: `timeout` (`TimeoutError`), `spawn_error` (`ExecutableNotFound`), and `killed` for anything else (cancellation, a consumer failure, abort), with `code` and `signal` `null`. `failure_class` is the raised `ProviderCallError`'s, else `null`.
  - `clock`: `wall_end`, `mono_end_ns` and `wall_ms`.
  - `rusage`: `null`.
  - `raw`: the blobs of the scrubbed stdout and stderr (from `process_capture` on an exception, empty when there is none). `stdout_times` is the blob of a UTF-8 JSON array of the integer offsets. `lines` is the stdout line count and `non_json_lines` the count of lines that do not parse as a JSON object.
  - `repo`: for a writing call that returned from `exec.run`, `tree_after` is `tree_id(worktree, index)` and `changed_paths` is `tree_changes(worktree, tree_before, tree_after)`. Otherwise it is `null`.
  - `model.served` is the first top-level string `model` on a stream event, with `served_source` `stream`, else `null` and `none`.
  - `native_ids`: the first top-level string `session_id` and `thread_id` on a stream event, else `null`.
  - `parsed`: `text_chars` (the length of the parsed text), `input_tokens`, `output_tokens` and `usd` as the stream reported them, from `Parsed`. When parsing failed they are `0`, `null`, `null` and `null`.
- After `end.json`, `store.prune(config.evidence.max_gb * 10**9)` runs.
- `ProviderLLM.preflight` stores each adapter's `installed_version` as `adapter.cli_version`. `CliAdapter.__init__` sets `cli_version = None`.
- Delete `capture_sequence`, the `capture_dir` constructor parameter, `_capture_dir`, `_seq` and `_write_capture`. `ProviderLLM` stops passing `capture_dir`.

Other modules:
- `clutch/__main__.py`: the `probe` handler's adapter construction drops `capture_dir=...`. Nothing else in that file changes.
- `clutch/evidence/schema.py`: `End.rusage` becomes `Rusage | None`. `clutch/evidence/store.py`: add `EvidenceStore.latest_stdout(prefix) -> str`. It looks at the `calls/` entries whose unquoted key starts with `prefix` and that hold `end.json`, reads them with `read_record` (skipping `SKIP`), takes the one with the greatest `(clock.wall_end, entry name)`, and returns its stdout blob decoded with `errors="replace"`. It returns `""` when none matches.
- `clutch/runner.py::harvest`: `events_tail` becomes `EvidenceStore(state_dir, ctx.fs, ctx.fs.read_bytes, ctx.fs.size, ctx.driver.redactor.scrub).latest_stdout(f"llm/{stem}/")[-HARVEST_TAIL_CHARS:]`, replacing the `spools/providers` scan.
- `clutch/driver.py::Driver._run`: the per-call `call` dict gains `call_key=llm_key(stem, seq, stage.surface, attempt, call_seq)`, so `llm_call`, `llm_error`, `artifact_invalid`, `gate_failed` and `stuck_budget_kill` carry it. `stage_start` and `stage_end` do not.
- `clutch/redact.py`: in the writer checklist, the `CliAdapter.invoke` attempt-spool line becomes the evidence writer, `clutch/evidence/store.py` `EvidenceStore.put_blob`, for the prompt, stdout, stderr and arrival-time blobs that `clutch/providers.py` `CliAdapter.invoke` hands it.
- `docs/how-clutch-works.md`, in these places only. Section 8.5: "provider captures" becomes the evidence store's blobs. Section 10.1: the `spools/` row drops its `spools/providers/` and `spools/probe/` sentences, and a new `evidence/` row describes `calls/<escaped key>/` (`start.json`, `end.json`, the `#<n>` re-execution suffix, no record for keyless calls), `blobs/`, `scratch/` and the `evidence.max_gb` prune. The `engine.log` row says per-call events carry `call_key`.

Test edits forced by the change (each is the only edit in its file):
- `tests/integration/test_daemon_composition.py`: `ScriptFS` gains in-memory `read_bytes` (absent raises `FileNotFoundError`) and `size`. `ScriptExec.run` answers any argv whose `argv[0]` is `git` first, before recording the call, reading stdin or running `hook`, with `(0, "<a fixed 40-hex id>\n", "")`.
- `tests/integration/test_providers.py`: `FakeExec.run` and `PreflightExec.run` answer `git` argv first with the same reply and record nothing. `classifier_adapter` drops `capture_dir=`. `test_consumer_error_keeps_call_capture`, `test_inflight_events_are_scrubbed_and_capture_is_preserved` and `test_event_callback_unwind_kills_group` drop their `spools/providers` reads and asserts, plus any local those leave unused. A keyless `ProviderLLM.call` has no record; the new unit tests cover capture on those paths for keyed calls.
- `tests/integration/test_watchdog.py::test_watched_result_and_capture_are_preserved`: drop the `spools/providers` listing and its loop.
- `tests/integration/test_watchdog_activation.py::test_eval_owned_budgets_preserve_synthetic_identities`: the `"/providers/"` assertion becomes `state_dir / "evidence" / "calls" / quote(f"llm/baseline-{fixture.name}/0/review/{attempt}/1", safe="") / "end.json" in rig.fs.files`, with the `urllib.parse.quote` import.
- `tests/integration/test_provider_capture_overwrite.py` is rewritten against the store. Two `ProviderLLM` instances (two processes) on stem `t-1` call through `llm_call` with run_seq 0 and then 1, and leave two records whose stdout blobs hold `first run` and `second run`. Stems `t-1` and `t-2` leave separate records. `tests/regress_provider_capture_overwrite.py` runs this file unchanged.
- `tests/integration/test_harvest.py::test_review_snag_commits_closed_harvest_without_code_content_and_wipes`: its `review` callable seeds an `end.json` with an over-long stdout through the new helper, not `spools/providers`.
- `tests/unit/test_qwen_adapter.py` and `tests/unit/test_gemini_adapter.py`: drop `capture_dir=` from each adapter construction. `tests/unit/test_preflight_parallel.py`: `MemoryFS` gains a no-op `remove`. `tests/unit/test_harvest_redaction.py`: its `fs` namespace gains `entries` (returning `[]`), `read_bytes` and `size`.
- `tests/integration/test_fixture_host.py`: `RecordedExec.run` records the stdin file's text when the call is made, because the file is gone once the call ends. The two assertions in `test_fixture_cli_adapter_roundtrip` that read `stdin_path` after a call read that recorded text instead.
- Delete `tests/unit/test_capture_sequence.py`.

New files: `tests/evidence_records.py` (a helper `seed_end(state_dir, key, stdout, wall_end)` that writes a schema-valid `end.json` and its blobs through `EvidenceStore` on `LocalFileSystem`), `tests/unit/test_evidence_envelope.py` (fakes and `tmp_path` only, covering the new lines in `providers.py`, `driver.py`, `runner.py` and `clutch/evidence/`), and `tests/integration/test_evidence_envelope.py`.

Scope out: measuring `rusage` (see Goal), new `exec.run` keywords or return values, the harness fakes (`tests/harness/`, whose provider calls delegate git to a real repository and whose `run` already takes `on_stdout_line`), `eval/`, normalizers and `normalized/` views, `evidence` verbs, the per-attempt `spools/<stem>/<attempt>/` (roadmap row 63), the journal, `Parsed`, `CallMeter`, and the `ProviderLLM` and `Git` constructor signatures.

Simpler approach rejected: keeping `spools/providers/` beside the store is the dual path the plan forbids. Giving `ProviderLLM` a `Git` constructor argument breaks six unfenced construction sites (`tickets/decisions/declined-box-000573-513f33d4.md`). Real-disk readers for the store break every in-memory rig (`tickets/decisions/declined-box-000572-0f2e1a9f.md`).

## Scope fence
- clutch/providers.py
- clutch/runner.py
- clutch/driver.py
- clutch/redact.py
- clutch/__main__.py
- clutch/evidence
- docs/how-clutch-works.md
- tests/evidence_records.py
- tests/unit/test_evidence_envelope.py
- tests/unit/test_capture_sequence.py
- tests/unit/test_qwen_adapter.py
- tests/unit/test_gemini_adapter.py
- tests/unit/test_preflight_parallel.py
- tests/unit/test_harvest_redaction.py
- tests/integration/test_evidence_envelope.py
- tests/integration/test_daemon_composition.py
- tests/integration/test_providers.py
- tests/integration/test_watchdog.py
- tests/integration/test_watchdog_activation.py
- tests/integration/test_provider_capture_overwrite.py
- tests/integration/test_harvest.py
- tests/integration/test_fixture_host.py

## Acceptance criteria
1. `tests/unit/test_evidence_envelope.py::test_start_record_precedes_spawn`: a keyed `llm_call` through `ProviderLLM` with a fake exec (git and provider argv answered with distinct values) finds `start.json` present and `end.json` absent under `calls/<quoted key>/` when the provider argv arrives. `read_record(key, "start")` then has `id` equal to the key, `group`, `run_seq`, `surface`, `attempt`, `call` and `stem` equal to the call's, `repo.main_sha`, `base_sha` and `tree_before` equal to the fake's answers for `rev-parse --verify main`, `rev-parse --verify HEAD` and `write-tree` (not swapped), and a `prompt.blob` whose `get_blob` is the scrubbed prompt. The run fails if no record exists or the record is written after spawn.
2. `tests/unit/test_evidence_envelope.py::test_end_record_on_success`: `end.json` has `exit.status` `ok` and `code` 0, a `raw.stdout` blob equal to the scrubbed stdout, `lines` equal to its line count, a `stdout_times` blob that is a JSON list of that many ints, `parsed` token counts equal to the returned `LLMResult`'s, `repo` `null` for a read-only surface, and Claude's `system/init` `session_id` and `model` in `native_ids.session_id` and `model.served`, with a codex `thread.started` `thread_id` in `native_ids.thread_id` in a second case.
3. `tests/unit/test_evidence_envelope.py::test_writing_call_records_trees_and_cleans_scratch`: an `implement` call records `tree_before` from the first `write-tree`, `tree_after` from the second, and `changed_paths` from `diff --name-only`. Every `add -A` and `write-tree` argv carried `GIT_INDEX_FILE` under `<state_dir>/evidence/scratch/`, and after the call no file remains under `scratch/`.
4. `tests/unit/test_evidence_envelope.py::test_keyless_calls_leave_no_record`: `ProviderLLM.call` and `ProviderLLM.preflight` leave no entry under `<state_dir>/evidence/calls`, nothing under `<state_dir>/spools`, no file under `scratch/`, and issue no `git` argv.
5. `tests/unit/test_evidence_envelope.py::test_records_and_blobs_carry_no_secret`: a configured secret planted in the prompt, stdout and stderr is absent from every record file and every decompressed blob under `<state_dir>/evidence`, and `[REDACTED:<NAME>]` is in the stdout blob.
6. `tests/unit/test_evidence_envelope.py::test_failed_calls_still_end`: a nonzero exit with a classified failure writes `exit.status` `nonzero` and the raised `ProviderCallError`'s `failure_class`. A fake raising `TimeoutError` with `process_capture` writes `timeout` and a stdout blob equal to the scrubbed partial stdout. `asyncio.CancelledError` writes `killed`. In each case the original exception propagates, not a store error.
7. `tests/unit/test_evidence_envelope.py::test_reexecuted_key_never_overwrites`: invoking the same capture key twice leaves `calls/<quoted key>/` byte-identical after the second call, and a second record under `<key>#2` whose `start.json` `id` is the unsuffixed key.
8. `tests/unit/test_evidence_envelope.py::test_route_fields`: a two-candidate route records `candidates` in route order, `reason` `first` when the first candidate serves and `failover` after the session excludes it (`session.auth_excluded`), and `config_sha` equal to `hashlib.sha256(repr(snapshot_config(cfg)).encode()).hexdigest()`.
9. `tests/unit/test_evidence_envelope.py::test_cli_version_from_preflight`: after `preflight` with `--version` answering `1.2.3 (Claude Code)`, a keyed call's `provider.cli_version` is `"1.2.3"`; on a client that never ran preflight it is `null`, not an empty string.
10. `tests/unit/test_evidence_envelope.py::test_llm_call_log_events_carry_call_key`: a `Driver.from_config` driver under `tmp_path` with a `FakeLLM` whose first reply is invalid writes two `llm_call` events to `engine.log`. Their `call_key` values equal `llm_key(...)` for `call_seq` 1 and 2 and differ from each other, and `stage_start` and `stage_end` have no `call_key`.
11. `tests/unit/test_evidence_envelope.py::test_latest_stdout`: with `end.json` records seeded by `tests/evidence_records.py::seed_end` for `llm/a/...` at two times and `llm/b/...` later still, `latest_stdout("llm/a/")` returns the later `a` stdout, not `b`'s, and `latest_stdout("llm/c/")` returns `""`. `./dev.py test tests/unit/test_harvest_redaction.py` passes with the extended fake `fs`.
12. `tests/integration/test_evidence_envelope.py::test_core_rig_records_stay_in_memory`: a `CoreRig` keyed review call returns `ok`, its `start.json` and `end.json` exist in `rig.fs.files`, and no file exists under the real `<state_dir>/evidence` directory. That `start.json` has `engine.version` equal to `importlib.metadata.version("clutchwork")` and `engine.spec_version` equal to the `version` in `clutch/specs/review.md`'s frontmatter. With real-disk readers the prune raises `FileNotFoundError`, so the test catches them.
13. `tests/integration/test_evidence_envelope.py::test_old_capture_path_is_gone`: no `.py` file under `clutch/` contains `capture_sequence`, `capture_dir`, `_write_capture`, `spools/providers` or `spools/probe`, or matches the regex `"spools"\s*/\s*"(providers|probe)"`. The `docs/how-clutch-works.md` section 10.1 table has an `evidence/` row, and its `spools/` row names neither old path.
14. `tests/integration/test_provider_capture_overwrite.py` passes as rewritten: the two processes leave two records holding `first run` and `second run`, and neither is replaced. `tests/integration/test_harvest.py` passes with `events_tail` taken from the seeded record, cut to `HARVEST_TAIL_CHARS` characters and not `""`: `./dev.py test tests/integration/test_provider_capture_overwrite.py tests/integration/test_harvest.py`.
15. The unit and integration suites pass, with no existing test edited beyond Scope in, including the CoreRig drives, `test_provider_cooldown_failover.py`, `test_reliability_battery.py`, `test_shakeout.py`, `test_drain.py`, `test_eval_harness.py` and `test_host_contract.py`: `./dev.py test tests/unit` and `./dev.py test tests/integration`.

## Verification
```
./dev.py test tests/unit/test_evidence_envelope.py tests/integration/test_evidence_envelope.py
./dev.py test tests/unit
./dev.py test tests/integration
```

## Definition of rejected
The branch:
- still writes or reads `spools/providers/` or `spools/probe/`, or keeps `capture_sequence`, `capture_dir`, `_seq` or `_write_capture`;
- gives the store real-disk readers instead of `fs.read_bytes` and `fs.size`;
- overwrites a record file, or writes `start.json` after the process starts;
- changes the `ProviderLLM` or `Git` constructor, or adds an `exec.run` keyword;
- fills `rusage` with zeros or a process-wide `resource.getrusage`;
- leaves a configured secret in any record or blob;
- edits `tests/harness/` or `eval/`, or edits an existing test beyond Scope in.

## Time budget
- expected: 150m
- stuck: 180m
