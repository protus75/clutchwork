# Review: rma

The flake.py change and its unit tests meet criteria 1-5, but the only engine caller of `Flake.release` (clutch/stages.py:1371-1373, outside the fence) still releases only ticket resolutions with a merged fix, so a declined report never gets released in a real run, and fixing that needs a path outside the fence.

## Findings

- [ticket] clutch/flake.py:128 The goal says the cap-blocking declined quarantines must become releasable and that every resolution kind has a reachable release path. The diff makes `release` accept `declined`, but the only engine consumer, clutch/stages.py:1370-1373, still computes `fix` only for `resolution.kind == "ticket"` and calls `flake.release` only after a merge event. No engine path ever passes `GreenRerunEvidence(..., f"declined:{box_id}", ...)`. The five declined quarantines (000359, 000449, 000450, 000451, 000457) stay active, and `detect` keeps escalating 'quarantine-cap crossed'. The criteria are met only in unit tests while the real code path differs. The boundary contract lists the callers of `Flake.release` as consumers, but clutch/stages.py is not in `## Scope fence`. (do instead: Add clutch/stages.py (and the test that covers the Check release loop) to `## Scope fence`. Have Check call `flake.release` for a declined resolution with a passing observation whose `fix_stem` is `declined:<box_id>`. Add an acceptance criterion that exercises the Check path.)
- [ticket] docs/how-clutch-works.md:371 The added text "Check releases a passing quarantined test when its resolved fix has merged. A supplied green rerun also releases a report resolved as declined." sits in the Check paragraph and implies Check releases declined reports. Check (clutch/stages.py:1371) never does, so the doc describes behavior the code does not have. (do instead: Once Check calls release for declined reports (see the stages.py finding), keep the sentence. Until then, state that only a direct `Flake.release` call with a green rerun releases a declined report.)
- [ticket] docs/how-clutch-works.md:- Stale doc: line 503 still says "Check quarantines unedited fail-then-pass tests and releases them after a merged fix and a passing observation." It does not mention the declined release path this diff adds. (do instead: Update the line 503 bullet in the same change so it also describes the declined-report release (no merge, green rerun with fix_stem `declined:<box_id>`).)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "01b9c8b3be3beccd052ef0f51dc2156473576d51",
  "stem": "flake-release-declined-resolution",
  "reviewed_sha": "01b9c8b3be3beccd052ef0f51dc2156473576d51",
  "summary": "The flake.py change and its unit tests meet criteria 1-5, but the only engine caller of `Flake.release` (clutch/stages.py:1371-1373, outside the fence) still releases only ticket resolutions with a merged fix, so a declined report never gets released in a real run, and fixing that needs a path outside the fence.",
  "findings": [
    {
      "code": "ticket",
      "path": "clutch/flake.py",
      "line": 128,
      "message": "The goal says the cap-blocking declined quarantines must become releasable and that every resolution kind has a reachable release path. The diff makes `release` accept `declined`, but the only engine consumer, clutch/stages.py:1370-1373, still computes `fix` only for `resolution.kind == \"ticket\"` and calls `flake.release` only after a merge event. No engine path ever passes `GreenRerunEvidence(..., f\"declined:{box_id}\", ...)`. The five declined quarantines (000359, 000449, 000450, 000451, 000457) stay active, and `detect` keeps escalating 'quarantine-cap crossed'. The criteria are met only in unit tests while the real code path differs. The boundary contract lists the callers of `Flake.release` as consumers, but clutch/stages.py is not in `## Scope fence`.",
      "paved_road": "Add clutch/stages.py (and the test that covers the Check release loop) to `## Scope fence`. Have Check call `flake.release` for a declined resolution with a passing observation whose `fix_stem` is `declined:<box_id>`. Add an acceptance criterion that exercises the Check path.",
      "kind": null,
      "unit": null
    },
    {
      "code": "ticket",
      "path": "docs/how-clutch-works.md",
      "line": 371,
      "message": "The added text \"Check releases a passing quarantined test when its resolved fix has merged. A supplied green rerun also releases a report resolved as declined.\" sits in the Check paragraph and implies Check releases declined reports. Check (clutch/stages.py:1371) never does, so the doc describes behavior the code does not have.",
      "paved_road": "Once Check calls release for declined reports (see the stages.py finding), keep the sentence. Until then, state that only a direct `Flake.release` call with a green rerun releases a declined report.",
      "kind": null,
      "unit": null
    },
    {
      "code": "ticket",
      "path": "docs/how-clutch-works.md",
      "line": null,
      "message": "Stale doc: line 503 still says \"Check quarantines unedited fail-then-pass tests and releases them after a merged fix and a passing observation.\" It does not mention the declined release path this diff adds.",
      "paved_road": "Update the line 503 bullet in the same change so it also describes the declined-report release (no merge, green rerun with fix_stem `declined:<box_id>`).",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "rma"
}
```
