---
state: confirmed
source: box:roadmap_row
priority: P2
kind: feature
agent_tier: medium
agent_effort: medium
---

## Depends on
- provider-capture-overwrite
- fs-seam-mkdir-remove

## Context
- docs/evidence-trail-plan.md#Target design
- clutch/seams.py::FileSystem
- clutch/seams.py::LocalFileSystem
- clutch/config.py::Release
- clutch/config.py::Config
- test-gate.toml

## Goal / Why
A content-addressed evidence store exists as library code, with no caller yet. It holds a blob store under `<state_dir>/evidence/blobs/<aa>/<sha256>` (zstd-compressed, hashed after redaction), versioned `clutch.evidence.*` record schemas, a strict writer, a tolerant reader, JSON Schema generation from the models, and an `evidence.max_gb` prune. Later tickets (`evidence-envelope`, the normalizers, the verbs) build on it, so the record shapes and the retention bound are pinned once here. This is roadmap row 28, release 0.3.0. Nothing in the journal, gates or dispatch reads the store.

## Scope in / Scope out
Scope in:
- New package `clutch/evidence/` with `__init__.py`, `schema.py` and `store.py`.
- `schema.py`: strict pydantic models (`extra="forbid"`) for the `clutch.evidence.call/1.0` `start.json` and `end.json` records and the `clutch.evidence.events/1.0` normalized event, as designed in the envelope and normalized-event subsections of the Target design plan section listed in Context, including the closed event `kind` and tool `class` lists. Schema ids have the form `clutch.evidence.<record>/<major>.<minor>`. A function returns the JSON Schema of each record version, generated from the model.
- `store.py`: `put_blob(data) -> "sha256:<hex>"` (redact, hash, zstd-compress with the standard library `compression.zstd`, publish; an existing blob is not rewritten), `get_blob(ref) -> bytes`, a strict `write_record` that validates against the current model before writing under `calls/<escaped effect key>/`, a tolerant `read_record` that accepts any known major version, ignores unknown fields, and returns a skip marker for an unknown major so callers can count it, and `prune(max_bytes)`.
- All file access goes through an injected `FileSystem` (`clutch/seams.py`) plus two injected callables, `read_bytes(path) -> bytes` and `size(path) -> int`, because the seam has no read or size method. The redactor is injected as a callable `str -> str` applied to decoded text before hashing; this ticket does not change `clutch/redact.py`.
- `prune`: when total blob bytes exceed `evidence.max_gb`, delete blobs referenced only by the oldest `end.json` records first, never delete a record file, and stop once under the bound. A blob referenced by a newer record stays.
- `clutch/config.py`: a new `Evidence(_Strict)` model with `max_gb: int = 20` (positive) and `Config.evidence: Evidence = Evidence()`, so existing configs load unchanged.
- `docs/how-clutch-works.md`: add the `evidence.max_gb` row to the config table only.
- `clutch/docs/host-contract.md`: in the `config-fields` block, add an `Evidence:` row (`required: []`, `defaults: {max_gb: 20}`) and add `evidence: {max_gb: 20}` under `Config.defaults`, so `tests/integration/test_host_contract.py` still matches the `_Strict` models in `clutch.config`. Nothing else in that file changes.

Scope out: writing records from `CliAdapter.invoke`, exec seam timing or rusage, `git.py` tree ids, normalizers, CLI verbs, the attempt manifest schema, moving any reader of `spools/providers/`, changes to `seams.py`, `redact.py`, `Parsed` or the journal.

## Scope fence
- clutch/evidence
- clutch/config.py
- clutch/docs/host-contract.md
- docs/how-clutch-works.md
- tests/unit/test_evidence_schema.py
- tests/unit/test_evidence_store.py
- tests/unit/test_evidence_config.py

## Acceptance criteria
1. A strict `start.json` record carrying an unknown top-level key is rejected by the writer, and the same record read through the reader returns a record with the unknown key ignored, not an error: `./dev.py test tests/unit/test_evidence_schema.py`.
2. A record whose schema id has an unknown major version (`clutch.evidence.call/2.0`) is returned by the reader as a skip marker, not parsed and not raised, so a caller can count it: `./dev.py test tests/unit/test_evidence_schema.py`.
3. The generated JSON Schema for `clutch.evidence.call/1.0` start records lists `id`, `route` and `prompt` under `properties`, sets `additionalProperties` to false, and is the same on two calls: `./dev.py test tests/unit/test_evidence_schema.py`.
4. An event with `kind` outside the closed list (for example `"thought"`) is rejected, and `"unknown"` is accepted: `./dev.py test tests/unit/test_evidence_schema.py`.
5. `put_blob` of the same bytes twice returns the same `sha256:` ref and performs one write, not two; `get_blob(ref)` returns the original bytes, not the compressed bytes: `./dev.py test tests/unit/test_evidence_store.py`.
6. A text blob containing a configured secret is stored redacted: `get_blob` of its ref does not contain the secret, and the ref equals the hash of the redacted bytes, not of the original: `./dev.py test tests/unit/test_evidence_store.py`.
7. With three records whose `end.json` timestamps differ and a bound that fits only two records' blobs, `prune` removes the blobs referenced only by the oldest record, leaves a blob also referenced by a newer record, and removes no record file: `./dev.py test tests/unit/test_evidence_store.py`.
8. `Evidence().max_gb == 20`, `Evidence(max_gb=0)` raises a validation error, and `Config.model_fields["evidence"].default` equals `Evidence()`, so a config with no `evidence` key still loads: `./dev.py test tests/unit/test_evidence_config.py`.
9. Every test file named above reads and writes disk only under `tmp_path` and starts no process: `./dev.py test tests/unit/test_evidence_schema.py tests/unit/test_evidence_store.py tests/unit/test_evidence_config.py`.
10. The `config-fields` block in `clutch/docs/host-contract.md` has an `Evidence:` row with `required: []` and `defaults: {max_gb: 20}` and an `evidence` key under `Config.defaults`, so the `_Strict` subclass check does not fail on the new `Evidence` model: `./dev.py test tests/integration/test_host_contract.py`.

## Verification
```
./dev.py test tests/unit/test_evidence_schema.py tests/unit/test_evidence_store.py tests/unit/test_evidence_config.py
./dev.py test tests/integration/test_config.py
./dev.py test tests/integration/test_host_contract.py
```

## Definition of rejected
The branch adds a caller of the store in engine code, a second capture path, a dependency in `pyproject.toml`, a change to `clutch/seams.py` or `clutch/redact.py`, a compat shim, or a prune that deletes a record file.

## Time budget
- expected: 60m
- stuck: 120m
