---
state: confirmed
source: human
priority: P1
kind: chore
---

## Depends on
none

## Context
- docs/how-clutch-works.md#10. State on disk
- docs/how-clutch-works.md#6.2 Harvest
- docs/how-clutch-works.md#8.5 Spend and redaction
- clutch/providers.py::CliAdapter.invoke
- clutch/providers.py::CallCapture
- clutch/providers.py::WRITING_SURFACES
- clutch/providers.py::engine_version
- clutch/providers.py::conduct_file
- clutch/providers.py::_events
- clutch/providers.py::ProviderLLM.admitted_call
- clutch/providers.py::ProviderLLM.call
- clutch/providers.py::ProviderLLM.preflight
- clutch/llmeffect.py
- clutch/evidence/store.py
- clutch/evidence/schema.py
- clutch/evidence/claude.py
- clutch/evidence/codex.py
- clutch/evidence/gemini.py
- clutch/seams.py::SubprocessExec.run
- clutch/seams.py::rusage_figures
- clutch/seams.py::reap_outcome
- clutch/seams.py::_reap
- clutch/git.py::Git.tree_id
- clutch/runner.py::harvest

## Goal / Why
Roadmap row 149, added by the 0.3.0 acceptance review. `docs/evidence-trail-plan.md` "Where each piece lives" promises a new `docs/how-clutch-works.md` section on the evidence record. At HEAD (`5c2c1e0e`) that document has only the section 10.1 `evidence/` row and the section 11 `evidence.max_gb` row. A reader cannot learn from it what a call record holds, when each file is written, which calls leave no record, how blobs are stored and pruned, or what the normalizers do, without reading `clutch/providers.py` and `clutch/evidence/`.

After this ticket, a new section `### 10.4 Evidence records` states those facts as the code at HEAD behaves, and the 10.1 `evidence/` row points to it the way the `journal/` row points to section 10.2. `docs/how-clutch-works.md` describes the code, so where the plan's target design and the code differ, the section follows the code.

## Scope in / Scope out
In, `docs/how-clutch-works.md` only, two edits:

1. Insert `### 10.4 Evidence records` after the last line of section 10.3 (the list item "7. The current retro window's scorecard and provenance.") and before `## 11. Config`. Prose, bullets or tables are the implementer's choice. Read each owner before writing its fact, and state every fact below, F1 to F19, with nothing the code does not show:
   - F1 (`clutch/providers.py::CliAdapter.invoke`, `clutch/runner.py::harvest`, `clutch/evidence/store.py::EvidenceStore.latest_stdout`). Each keyed provider call leaves one record under `<state_dir>/evidence/`. The record keeps the provider's redacted stdout and stderr, plus an envelope of facts about the call. `CliAdapter.invoke` is the only writer. The only engine reader is harvest's provider event tail (section 6.2), which `latest_stdout` builds from the stdout of the newest `end.json` (by `clock.wall_end`) whose key starts with `llm/<stem>/`. The journal, gates and dispatch never read the store.
   - F2 (`CliAdapter.invoke`, `clutch/providers.py::CallCapture`, `clutch/providers.py::ProviderLLM.admitted_call`, `clutch/llmeffect.py::llm_call`, `clutch/llmeffect.py::llm_key`). `invoke` writes a record only when it is given a `CallCapture`. `admitted_call` builds one from the journal Effect key that `llm_call` passes (section 10.2): `llm/<group>/<run_seq>/<surface>/<attempt>/<call>`, where `<group>` is the ticket stem or, for a ticketless call, the surface name.
   - F3 (`clutch/providers.py::ProviderLLM.preflight`, `handle_probe` in `clutch/__main__.py`, `clutch/providers.py::ProviderLLM.call`, `clutch/effects.py::Effects.run`). Keyless calls leave no record. These are the preflight's probe calls (section 8.1), the calls the probe verb in section 2.1 makes (its handler `handle_probe`), and any call through the raw seam `ProviderLLM.call`. A key that already has a completed Effect replays its result, makes no provider call, and writes nothing. Every call, keyed or not, writes its redacted prompt to a temporary file under `evidence/scratch/`, which is the CLI's stdin. That file and the temporary index are removed when the call ends.
   - F4 (`clutch/evidence/store.py::EvidenceStore._record_path`, `CliAdapter.invoke`). A record is `calls/<escaped key>/start.json` and `end.json`. The key is escaped with `urllib.parse.quote(key, safe="")`. A key that runs again finds its directory already there and writes under `<key>#2`, then `#3`, and so on. Only a key with no journaled completion can run again. The record's `id` keeps the key without the suffix.
   - F5 (`CliAdapter.invoke`). `start.json` is written after the tree id is taken and before the CLI is spawned, so a call that crashes, hangs or is killed still leaves one. A `start.json` with no `end.json` means the call never finished recording, for example because the engine died mid-call.
   - F6 (`CliAdapter.invoke`, `clutch/evidence/schema.py::Start`, `clutch/providers.py::engine_version`, `clutch/providers.py::conduct_file`, `clutch/providers.py::WRITING_SURFACES`, `clutch/git.py::Git.tree_id`). The `start.json` fields:
     - `schema` is `clutch.evidence.call/1.0`.
     - `id`, `group`, `run_seq`, `surface`, `attempt` and `call` come from the key. `stem` is null for a ticketless call.
     - `engine`: `version` is the installed `clutchwork` package version. `spec` is `<surface>.md`, and `spec_version` is that spec's frontmatter version.
     - `route`: `tier`, `effort`, `candidates` (provider names in route order), the `chosen` provider, `reason` (`first`, `spill` or `failover`), and `config_sha`, the SHA-256 of the config snapshot's `repr`.
     - `provider`: `name`, `adapter` (the adapter class), `kind` and `package`. `cli_version` is the version the preflight read in this process, else null. `billing` is `local` for a `base_url` provider, `metered` for one with `auth`, and otherwise `subscription`.
     - `model.requested`.
     - `process`: the redacted `argv`. `env_names` holds the sorted names of the child environment, never its values. `cwd` is the ticket worktree for a writing call and the checkout otherwise. `timeout_s`. `writes` is true only for `implement`. `isolated` is always false today. `conduct_file` is the file name `conduct_file` returns for the provider, the conduct file section 8.1 says that provider reads.
     - `repo`: `main_sha` and `base_sha` are `main` and `HEAD` resolved in that directory. `tree_before` is a git tree id of that directory's working tree, written through a temporary index (`git add -A`, then `write-tree`, with `GIT_INDEX_FILE` in `evidence/scratch/`). The real index, the branch and the reflog are untouched.
     - `prompt`: the `blob`, `chars` and `bytes` of the redacted prompt.
     - `clock`: `wall_start` and `mono_start_ns`.
   - F7 (`CliAdapter.invoke`). `end.json` is written when the call ends, whenever `start.json` was written: at exit, nonzero exit, kill, timeout, spawn error, or a stream that fails to parse.
   - F8 (`CliAdapter.invoke`, `clutch/evidence/schema.py::Exit`). `exit.status` is one of five values:
     - `ok` for exit 0.
     - `nonzero` for an exit above 0.
     - `killed` for a signal exit, or for any other unwind before the process returned.
     - `timeout`.
     - `spawn_error`, when the CLI was not found.
     `status` describes the process, so a call that exits 0 but fails to parse is `ok` and has a `failure_class`. `code` is the exit code or null. `signal` is the signal number for a signal exit. `failure_class` is the class of the `ProviderCallError` the call raised, else null.
   - F9 (`CliAdapter.invoke`). `clock` holds `wall_end`, `mono_end_ns` and `wall_ms`. `mono_start_ns` and `mono_end_ns` hold the engine clock seam's wall time as epoch nanoseconds, not a monotonic counter.
   - F10 (`clutch/seams.py::_reap`, `clutch/seams.py::reap_outcome`, `clutch/seams.py::rusage_figures`). `rusage` comes from `os.wait4` when the exec seam reaps the provider process, including after a kill or a timeout. It is null when no process was reaped, as for `spawn_error`. `user_s` and `sys_s` are CPU seconds. `max_rss_kb` is the kernel's `ru_maxrss` in kilobytes. On Linux that figure is the larger of the provider's own peak and the engine's peak at spawn, because exec carries the spawning process's high-water mark into the child. It is the provider's own peak only when that peak exceeds the engine's. The section must not call it the provider's peak without this qualification.
   - F11 (`CliAdapter.invoke`, `clutch/seams.py::SubprocessExec.run`, `clutch/providers.py::_events`). `raw` holds these fields:
     - `stdout` and `stderr` are blob refs to the redacted output that the exec seam returned. For a call that raised, they hold the output the seam attached to the exception as `process_capture`, and are empty when it attached none.
     - `stdout_times` is a blob of a JSON list with one integer nanosecond offset from the call's start time for each stdout line, recorded as the seam delivered the line.
     - `lines` is the stdout line count.
     - `non_json_lines` counts the lines that are not a JSON object.
   - F12 (`CliAdapter.invoke`, `clutch/git.py::Git.tree_changes`). `repo` holds `tree_after` and `changed_paths` (`git diff --name-only` between the two trees) for a writing call whose process returned. Otherwise it is null.
   - F13 (`CliAdapter.invoke`). `model.served` is the first string `model` in the stream's JSON events, and `served_source` is `stream` or `none`. `native_ids.session_id` and `native_ids.thread_id` are the first such strings in the stream. `parsed` (`text_chars`, `input_tokens`, `output_tokens`, `usd`) is what the adapter's `parse` returned, or 0 and nulls when nothing parsed.
   - F14 (`clutch/evidence/store.py::EvidenceStore.put_blob`, `EvidenceStore.get_blob`). Blobs live at `blobs/<first two hex digits>/<sha256 hex>`, and records name them as `sha256:<hex>`. `put_blob` redacts UTF-8 text with the configured secrets before hashing, so a secret never reaches the store, not even as a hash. Bytes that are not UTF-8 are stored as given. Blobs are stored zstd-compressed (`compression.zstd`). Each digest is written once, so identical content in many calls, such as a prompt re-sent on a retry, is stored once.
   - F15 (`clutch/evidence/store.py::EvidenceStore.prune`, `CliAdapter.invoke`). After each `end.json` write, `invoke` calls `prune` with `evidence.max_gb` × 10^9 bytes. When the blob files' on-disk (compressed) size is over that bound, `prune` walks the records that have an `end.json`, oldest `clock.wall_end` first. For each record, it deletes the blobs its `end.json` names (stdout, stderr, arrival times), except a blob that a record not yet walked still names: a newer record, or one with no `end.json`. It stops once the size is under the bound. Records are never deleted. Prune never removes a blob that only a `start.json` names, such as a prompt.
   - F16 (`clutch/evidence/schema.py`, `EvidenceStore.write_record`, `EvidenceStore.read_record`, `clutch/evidence/schema.py::json_schema`). `write_record` validates each record against the strict pydantic `Start` or `End` model (`extra="forbid"`, strict types) before writing it. `read_record` accepts any `clutch.evidence.call/1.<minor>` record, drops fields the current model does not know, and returns `SKIP` for another major version. `json_schema` generates the JSON Schema of `start`, `end` and `event` from the models. No command exposes it yet.
   - F17 (`clutch/evidence/claude.py`, `clutch/evidence/codex.py`, `clutch/evidence/gemini.py`, `clutch/evidence/schema.py::Event`, `clutch/evidence/schema.py::Tool`). Each normalizer is a pure function `normalize(stdout, times_ns, put_blob)` that turns raw stdout bytes and arrival offsets into `clutch.evidence.events/1.0` events. The `NORMALIZER_ID`s are `claude-stream/1`, `codex-stream/1` and `gemini-stream/1`. A normalizer does no I/O: large text (assistant text, thinking, tool output) goes to a blob through `put_blob`, and the event carries the ref. Every event has a `kind` from the closed `Event.kind` list. Tool events carry a `class` from the closed `Tool.class_` list and the native tool name. A line or content block a normalizer cannot map becomes an `unknown` event with its native payload, and a line that is not JSON is kept as `{"line": ...}`. `t_ms` is the line's arrival offset in milliseconds, or 0 when no offsets are given.
   - F18 (`clutch/evidence/claude.py::VERIFIED_PROVIDERS`, `clutch/evidence/codex.py::INPUT_INCLUDES_CACHED`). The claude normalizer is verified only for `claude`, so qwen's Claude-shaped stream is unverified. Codex's `input_tokens` includes cached tokens, so its `input_uncached` is `input_tokens` minus `cached_input_tokens`. Each normalizer has a golden fixture under `tests/fixtures/evidence/<provider>/`.
   - F19. No engine code calls a normalizer yet. No call record has a `normalized/` directory, and the normalizers run only in their tests.
2. In the section 10.1 table, the `evidence/` row's Holds cell begins "Call records (section 10.4) in `calls/<escaped key>/`". That cell gains only the words "(section 10.4)", and the row still begins `` | `evidence/` | `` (`tests/integration/test_evidence_envelope.py` reads it).

Merge order. Rows 135 (`cli-group-config`) and 136 (`cli-group-provider`) are confirmed, unmerged and queued, and both fence `docs/how-clutch-works.md`. They edit the section 2.1 verb rows, section 8.1 (the `install` road and the model-names paragraph) and the section 11 sentence naming `init-config`. Their criteria grep the whole document for `clutch install`, `clutch probe`, `` `install` ``, `` `probe` `` and `(init|update|migrate)-config`, and expect no match. This ticket edits none of their lines. Its insertion ends on the line before `## 11. Config`, and the section 11 sentence that row 135 changes sits six lines below that heading, so the hunks do not touch in either merge order. The new section names the probe verb only as "the probe verb in section 2.1", never in a form those greps match. Their criteria hold whether this ticket merges before or after them, and this ticket's text is the same either way.

Out:
- Every other part of `docs/how-clutch-works.md`: the section 11 `evidence.max_gb` row, section 8.5, section 6.2, every heading and every number. Every other file, including `docs/evidence-trail-plan.md`, code and tests. No test reads document text (owner ruling, box-000676).
- The plan's target design differs from the code in places, and the section follows the code. `engine.version` is the package version, not a tree sha. `mono_*_ns` are wall clock. `isolated` is always false and `start.json` always has `repo`. Nothing writes `normalized/`. `cli_version` comes from the preflight, not a `--version` probe on each call. A timed-out call's raw output is what the seam attached, not necessarily its partial output.
- Second problems filed, neither fixed nor described here as intended behavior:
  - box-000730: a key-scoped `run_seq` such as `sup-<n>` fails `int(run_seq)` in `invoke`. The section does not describe scoped keys.
  - box-000731: a plain timeout attaches no `process_capture`.
  - box-000732: the `mono_*` fields hold wall-clock values.
  - box-000727: `max_rss_kb` over-reports.
  The ticket that fixes any of these updates this section.

## Scope fence
- docs/how-clutch-works.md

## Acceptance criteria
1. Reading `docs/how-clutch-works.md` shows a heading `### 10.4 Evidence records` after section 10.3's list and before `## 11. Config`, stating F1 to F4. The store's only writer is `CliAdapter.invoke` and its only engine reader is harvest's event tail. A record is written only for a call with a `CallCapture`, built from an `llm/<group>/<run_seq>/<surface>/<attempt>/<call>` key. The preflight probes, the probe verb's calls and `ProviderLLM.call` leave none. Records sit in `calls/<escaped key>/`, a key that runs again gets the `#<n>` suffix, and `id` stays unsuffixed.
2. Reading `docs/how-clutch-works.md#10.4 Evidence records` shows F5 and F6: `start.json` is written before spawn, and every block of `start.json` is listed with the meanings given in Scope in. `engine.version` is the package version, `env_names` holds names only, and `tree_before` comes from a temporary index.
3. Reading `docs/how-clutch-works.md#10.4 Evidence records` shows F7 to F13. The five `exit.status` values carry their conditions. The `mono_*_ns` fields are wall-clock epoch nanoseconds. `max_rss_kb` is qualified as the larger of the provider's own peak and the engine's peak at spawn, never stated bare as the provider's peak. Raw output is described as what the seam returned or attached, with no claim that a timed-out call keeps its partial output. `repo` in `end.json` exists only for a writing call whose process returned.
4. Reading `docs/how-clutch-works.md#10.4 Evidence records` shows F14 and F15. The blob path and ref form, redaction before hashing, zstd, and one write per digest are all stated. Prune runs after each `end.json` against `evidence.max_gb` × 10^9 bytes and walks oldest `wall_end` first. It deletes only blobs an `end.json` names that no record not yet walked names. Records and prompt-only blobs are never pruned.
5. Reading `docs/how-clutch-works.md#10.4 Evidence records` shows F16 to F19. The writer is strict and the reader tolerant: it skips another major version. The three `NORMALIZER_ID`s and the pure `normalize(stdout, times_ns, put_blob)` signature are given, along with the closed `kind` and `class` lists and `unknown` events, qwen unverified, and Codex input including cached tokens. No engine code runs a normalizer, so no `normalized/` directory is written.
6. In `docs/how-clutch-works.md#10.1 Files`, the `evidence/` row's Holds cell begins "Call records (section 10.4) in". `git diff main...HEAD -- docs/how-clutch-works.md` shows only that row's change and the inserted section. No existing heading, row or sentence is otherwise changed.
7. Either merge order with rows 135 and 136 holds, because the new section names no command in a form their greps match. ``sed -n '/^### 10\.4 /,/^## 11\. /p' docs/how-clutch-works.md | grep -cE 'clutch (install|probe)|`(install|probe)|(init|update|migrate)-config'`` prints `0`.
8. `git diff --name-only main...HEAD` lists only `docs/how-clutch-works.md`.
9. `./dev.py test` exits 0.

## Verification
```
./dev.py test
```

## Definition of rejected
The branch is thrown away if any of these hold:
- A sentence in the new section states a fact its owner in Scope in does not show. Or it copies a plan claim the code contradicts: a tree-sha engine version, monotonic `mono_*` fields, partial output kept on timeout, `normalized/` views written, a per-call `--version` probe, or `max_rss_kb` as the provider's own peak.
- The section describes scoped-key records or presents a fix for box-000727, box-000730, box-000731 or box-000732 as current behavior.
- A file other than `docs/how-clutch-works.md` changes, an existing heading is renamed or renumbered, or a test that reads document text is added.

## Time budget
- expected: 10m
- stuck: 20m
