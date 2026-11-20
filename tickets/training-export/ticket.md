---
state: draft
source: human
priority: P2
kind: feature
---

## Depends on
- training-config
- training-attempt-manifest

## Context
- docs/training-data-plan.md#3. Export: training records
- docs/training-data-plan.md#Rights and privacy
- clutch/config.py::TrainingData
- clutch/evidence/schema.py::Attempt
- clutch/evidence/store.py::EvidenceStore
- clutch/git.py::Git.merged_subjects
- clutch/redact.py::Redactor
- clutch/__main__.py::_command
- docs/how-clutch-works.md#2.1 Verbs
- tests/unit/test_main_coverage_group.py
- tests/unit/test_evidence_attempt_manifest.py

## On-demand
- clutch/docs/host-running.md
- docs/roadmap.md

## Goal / Why
`clutch training export --out DIR` exists. With `training_data.enabled: true` it turns what the host's own runs left behind into two kinds of labelled training record and writes them as JSONL, so a host can tune a small local model on its own work. Today the attempt manifests that `training-attempt-manifest` writes are read by nothing, and no verb reads the squash commits that carry the accepted side.

This ticket delivers the export core and the two kinds that need only the evidence store and git:
- `implement`: input is the rendered implement prompt, target is the attempt's final diff, label is `merged` (the squash commit with a `clutch-ticket` trailer), `negative` (an attempt manifest whose findings include a code in `logic`, `acceptance`, `scope` or `leak`, the codes of `clutch/specs/review.md`), or `neutral` (any other manifest: `rma`, premise, infra, abandoned).
- `preference`: `{prompt, chosen, rejected}` where `rejected` is a `negative` manifest's diff and `chosen` is the merged diff of the same stem; `reason` joins the manifest's finding messages.

Every record carries `kind`, `stem`, `group` (the stem), `run_seq`, `attempt`, `call_keys`, `engine_version`, `spec`, `spec_version` and `label`, so records can be filtered by the spec that produced them. Spec identity comes from the implement call's start record.

Output in `--out DIR`: `sft.jsonl` (one chat-message record per `implement` record: `{"messages": [{"role": "user", ...}, {"role": "assistant", ...}], <the fields above>}`) and `preference.jsonl` (one `{prompt, chosen, rejected, reason, <the fields above>}` per pair). `--kinds` takes `implement`, `preference` or both (default both) and a file is written only for a requested kind. `--holdout PCT` (0-100) holds out whole tickets: a stem is held out when the integer value of its sha256 hexdigest modulo 100 is below PCT, so the same stem is held out on every run; no record of a held-out stem is written to either file, and `holdout.txt` lists the held-out stems, one per line, sorted. `holdout.txt` is written only when `--holdout` is above 0.

A second scrub runs on every record before it is written. A record is dropped whole, never partly written, and counted when any of these holds: the configured-secret redactor changes its JSON text; its JSON text matches an AWS access key id (`AKIA` plus 16 upper-case letters or digits), a `-----BEGIN ... PRIVATE KEY-----` line, or `Bearer` followed by 20 or more token characters; or a path in a diff header matches a `TrainingData.effective_exclude()` glob (full path or basename), or a diff header cannot be parsed. A kind that cannot be built for a stem because its implement call, blob or diff is missing is skipped and counted separately. The verb prints a provider-terms notice once, then the counts: records written per kind, dropped, skipped, and held-out stems.

Why: the plan's flywheel starts here. Everything after it (`training-eval`, the host guide) reads this output. The rest of plan section 3 is two follow-up rows in `docs/roadmap.md` (see Scope in).

## Boundary contract
### Training export
- disposition: create
- owner: clutch/training.py
- closest existing: `clutch/evidence/store.py::EvidenceStore` (reads and writes evidence records and blobs), `clutch/runner.py::harvest` (writes the attempt manifest), `clutch/git.py::Git.merged_subjects` (lists merged tickets by subject)
- earning reason: no existing symbol joins attempt manifests, call start records, blobs and squash commits into records, and each of those owners is a single-source reader or writer that must not learn the join. The join has three production consumers: this verb, `training-eval` (roadmap row 60), and the two follow-up rows added here.
- consumers: the `clutch training export` handler in `clutch/__main__.py`; later `training-eval`
- observable change: the verb and its output files as in Goal / Why. Inputs: `<state_dir>/evidence/attempts/`, call start records and blobs, and first-parent commits with `clutch-ticket` trailers. Failures: `training_data.enabled` false refuses with exit 2 and the `TrainingData.require_enabled()` message as the paved road; a missing or empty evidence store exports zero records, exit 0. Side effects: writes only the files under `--out`, each replaced whole through the `FileSystem` seam; no journal event, no lock, no git write. The export is a rebuildable projection and never an authority. Ordering: records are written in sorted `(stem, run_seq, attempt)` order so two exports of the same sources are byte-identical.
- compatibility: no existing output, schema or record changes; `training_data` off (the default) keeps every verb as it is.
- acceptance: see criteria 1-9.
- tests: tests/unit/test_training_export.py
- post-merge source of truth: clutch/training.py

### Attempt listing
- disposition: extend
- owner: clutch/evidence/store.py
- consumers: `clutch/training.py`
- observable change: `EvidenceStore.attempts()` returns the sorted `(stem, run_seq, attempt)` triples of manifests under `evidence/attempts/`, read through `fs.entries`; it returns `[]` when the directory is absent.
- compatibility: `write_attempt`, `read_attempt`, `call_keys` and every record are unchanged.
- acceptance: criterion 9.
- tests: tests/unit/test_evidence_attempts_listing.py
- post-merge source of truth: clutch/evidence/store.py

### Merged ticket listing
- disposition: extend
- owner: clutch/git.py
- consumers: `clutch/training.py`
- observable change: `Git.merged_tickets(dir)` returns `(sha, stem)` for each first-parent commit of `HEAD` whose final trailer paragraph has one `clutch-ticket: <stem>` line, oldest first; commits without it are omitted.
- compatibility: `merged_subjects` and every other `Git` method are unchanged; the new method adds no second path for trailer parsing beyond `git log --format=%(trailers:key=clutch-ticket,valueonly)`, which `merged_subjects` already uses.
- acceptance: criterion 10.
- tests: tests/unit/test_git_merged_tickets_parse.py (a fake `ProcessExec` returning canned `git log` output) and tests/integration/test_git_merged_tickets.py (a real repository)
- post-merge source of truth: clutch/git.py

### Command surface
- disposition: extend
- owner: clutch/__main__.py (`_parser`, handlers)
- consumers: operators, `tests/unit/test_main_help.py`, `tests/unit/test_host_running.py`
- observable change: a new top-level group `training` with one subcommand `export` (`--out DIR` required, `--kinds`, `--holdout PCT`), built with `_command` carrying every help field.
- compatibility: no existing verb changes.
- acceptance: criterion 11.
- tests: tests/unit/test_main_training_group.py
- post-merge source of truth: clutch/__main__.py

## Scope in / Scope out
Scope in:
- New `clutch/training.py` holding the pure record building, labelling, scrub and holdout logic. It takes the store, a git object with `merged_tickets` and `diff`, the redactor and the `TrainingData` as parameters and does no I/O of its own beyond them; a `render` helper returns the file contents as bytes, and `report(counts) -> list[str]` returns the output lines (the notice, then the counts line) that the handler only prints.
- Prompt and spec for an attempt: the first `implement` call (lowest `(attempt, call)`) of the manifest's `call_keys`, read through `read_record(key, "start")` and `get_blob(start.prompt.blob)`. For a merged stem it is the implement call with the highest `(run_seq, attempt, call)` among `call_keys(f"llm/{stem}/")`, where `run_seq` strings that are not integers are ignored. A `SKIP` record is ignored.
- Merged diff: `git.diff(repo, f"{sha}^", sha)`.
- `EvidenceStore.attempts()` in `clutch/evidence/store.py`, `Git.merged_tickets` in `clutch/git.py`.
- In `clutch/__main__.py`: the `training` group and `export` subcommand with the help fields (what it does, reads, writes, lock none, exit codes 0 and 2, examples) and a handler. The handler builds the store, calls `training_data.require_enabled()` and raises `runner.Refusal` with the message `training export is off` and the `require_enabled` text as the paved road, builds the redactor with `Redactor.from_config(config, env)`, and prints the notice and counts with `print` to stdout. No `print(..., file=sys.stderr)` is added (`tests/integration/test_main_verb_groups.py::test_stderr_prints_have_one_prefixed_owner`). The provider-terms notice is: `Notice: model outputs come from third-party providers whose terms may restrict training other models on them. Check each provider's terms before training on this export.` Owner approval of the wording is outside this ticket.
- Documents: `docs/how-clutch-works.md` section 2.1 gains one `training export --out DIR [--kinds K ...] [--holdout PCT]` row (lock `no`), and `clutch/docs/host-running.md` gains a `training export` row (works while serve runs: `Yes`, it is read-only). Only those two rows change.
- `docs/roadmap.md`: add two rows to the 0.5.0 table after row 61 (rows 175 and 176), Owner `training plan 3`, Kind `feature`, P2, Depends on `training-export`, so the rest of plan section 3 has a home:
  - 175 `training-export-trajectory`: implement records carry the normalized tool-call events built from the call's raw stdout by the `normalize` function of `clutch/evidence/claude.py`, `codex.py` or `gemini.py` (chosen by the start record's `provider.adapter`), `--no-trajectory` trims them (plan open decision 1), and the `exclude` globs are applied to file paths in tool calls.
  - 176 `training-export-kinds`: the `review`, `ticket` (with `authored_by: human|author`) and `diagnosis` kinds, `--since DATE`, and the `conflict` kind skipped with a count while `merge-model-resolve` is unmerged. The `triage` kind stays out until the owner names a real label source, because no code produces an `override_report` message.
  Neither row's change to the roadmap adds a standing test; the check is that the roadmap parses.

Scope out: trajectory events and `--no-trajectory`, `--since`, the `review`, `ticket`, `diagnosis`, `conflict` and `triage` kinds (rows 175 and 176); `training eval` (`training-eval`); the host guide `host-training.md` and its `clutch docs` entry (`training-docs`); the plan's `./dev.py training-export` wrapper, which the repo's command-surface rule forbids; `clutch/help.py` (it describes extension surfaces, and `training export` is not one); the extension directory (it lists no `training` verb); row 59's own text in `docs/roadmap.md`, which the driver rewrites when the ticket merges; `config.yaml`, which has no `training_data` block, so this repo exports nothing until its owner enables it; any change to the attempt manifest writer, merged-attempt manifests (a merged attempt's code is read from git), or `clutch/evidence/schema.py`.

Merge order: the confirmed unmerged tickets `parallel-enable-repo-config` (fences `config.yaml` and its own test) and `boundary-contract-implementation-review` (fences the implement and review specs and their tests) share no file with this fence, so either order is safe.

## Scope fence
- clutch/training.py
- clutch/__main__.py
- clutch/git.py
- clutch/evidence/store.py
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- docs/roadmap.md
- tests/unit/test_training_export.py
- tests/unit/test_evidence_attempts_listing.py
- tests/unit/test_main_training_group.py
- tests/unit/test_git_merged_tickets_parse.py
- tests/integration/test_git_merged_tickets.py

## Acceptance criteria
1. With `training_data.enabled` false, `clutch training export --out DIR` exits 2, prints a message containing `set training_data.enabled: true`, and `DIR` holds no file; it does not exit 0 with empty files; checked by `./dev.py test tests/unit/test_training_export.py`.
2. `training.report(counts)` returns the provider-terms notice exactly once, as its first line and before the counts line, and the counts line names records written per kind, dropped, skipped and held-out stems; the handler prints those lines and nothing else on success; checked by `./dev.py test tests/unit/test_training_export.py`.
3. A manifest whose findings include code `logic` yields an `implement` record labelled `negative`; a manifest whose findings are only `rma` or empty yields `neutral`, never `negative`; checked by `./dev.py test tests/unit/test_training_export.py`.
4. A merged ticket yields an `implement` record labelled `merged` whose target is `git.diff(repo, f"{sha}^", sha)` and whose prompt is the implement call with the highest `run_seq`, not an earlier one; a merged stem with no implement call is skipped and counted, not written with an empty prompt; checked by `./dev.py test tests/unit/test_training_export.py`.
5. A stem with a `negative` manifest and a merged commit yields one `preference` record with `chosen` equal to the merged diff, `rejected` equal to the manifest diff and `reason` equal to the joined finding messages; a stem with only a `neutral` manifest, or with no merged commit, yields no `preference` record; checked by `./dev.py test tests/unit/test_training_export.py`.
6. A record whose text contains `AKIA` plus 16 upper-case characters, a private-key header, or a long `Bearer` token is dropped and counted, and the written file has one line fewer than without it, never a truncated line; a record whose merged diff touches `.env.local` or `deploy/id_rsa.pub` is dropped and counted; a record the configured-secret redactor would change is dropped; an unparseable diff header drops the record; checked by `./dev.py test tests/unit/test_training_export.py`.
7. `--holdout 50` over 20 stems writes `holdout.txt` listing exactly the held-out stems, sorted, none of those stems appears in `sft.jsonl` or `preference.jsonl`, and two runs hold out the same stems; `--holdout 0` writes no `holdout.txt`; `--holdout 100` writes no record; checked by `./dev.py test tests/unit/test_training_export.py`.
8. `--kinds preference` writes `preference.jsonl` and no `sft.jsonl`; two exports of the same sources produce byte-identical files; checked by `./dev.py test tests/unit/test_training_export.py`.
9. `EvidenceStore.attempts()` returns the sorted triples of every written manifest, and `[]` for a state directory with no `evidence/attempts/`, not an error; checked by `./dev.py test tests/unit/test_evidence_attempts_listing.py`.
10. `Git.merged_tickets` in a repository with two first-parent commits carrying `clutch-ticket: a` and `clutch-ticket: b` trailers and one commit without a trailer returns `[(sha_a, "a"), (sha_b, "b")]` in that order and omits the third, both with a fake `ProcessExec` returning canned `git log --first-parent` output and in a real repository; checked by `./dev.py test tests/unit/test_git_merged_tickets_parse.py tests/integration/test_git_merged_tickets.py`.
11. `training export` parses with `--out` required (`clutch training export` without it exits 2), `--kinds` limited to `implement` and `preference`, and `--holdout` an integer from 0 to 100; every `training` command has a description and examples; the verb tables in `clutch/docs/host-running.md` match the parser; checked by `./dev.py test tests/unit/test_main_training_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py`.
12. `docs/roadmap.md` still parses after the two rows are added; checked by `uv run clutch roadmap status`.

## Verification
```
./dev.py test tests/unit/test_training_export.py tests/unit/test_evidence_attempts_listing.py tests/unit/test_main_training_group.py tests/unit/test_main_help.py tests/unit/test_host_running.py tests/unit/test_roadmap_status.py tests/unit/test_git_merged_tickets_parse.py
./dev.py test tests/integration/test_git_merged_tickets.py tests/integration/test_main_verb_groups.py
uv run clutch roadmap status
```

## Definition of rejected
The branch writes a partly built or truncated record, exports when `training_data.enabled` is false, writes outside `--out`, puts one ticket's records in both the held-out and the written set, adds a `./dev.py` wrapper or a launcher twin, adds a trajectory, `--since` or a kind outside `implement` and `preference`, edits a file outside the fence, or covers `clutch/training.py` below the default 90 percent unit floor in `test-gate.toml` by moving its tests to `tests/integration/`.

## Time budget
- expected: 30m
- stuck: 60m
