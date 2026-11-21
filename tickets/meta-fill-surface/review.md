# Review: snag

The prior criterion-5 finding is fixed, but `fill` writes the model's `owner` into the block without checking it, so a reply can corrupt or inject content into a file.

## Findings

- [logic] clutch/metafill.py:108 `fields["owner"] = entry.owner.strip()` writes the model's owner into the composed block without any check. `meta._render` emits `owner: {value}` verbatim, and the only purpose-style check (no newline, no `\r`, no `-->`) is applied to `purpose` alone. A reply owner such as `x\n-->\nanything` therefore ends a `.md` block early and writes arbitrary text into the file. On a `.py` file it adds lines that are not part of the block, so the next `meta refresh` or `check` reports the file as malformed. That breaks the ticket's rule that the model is never given a way to edit a file, and it leaves a written file corrupt. (do instead: Before writing, validate a nonblank reply owner the same way as `purpose`: reject the entry with a reason such as `invalid owner` when it contains a newline, `\r` or `-->`. Keep the rule that a blank owner is skipped. Add a case to `tests/unit/test_meta_fill.py` showing that such an owner leaves the file byte-identical and lists it as rejected.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "659ea5eb7e704a03f38962961211cbf5bde4c961",
  "stem": "meta-fill-surface",
  "reviewed_sha": "659ea5eb7e704a03f38962961211cbf5bde4c961",
  "summary": "The prior criterion-5 finding is fixed, but `fill` writes the model's `owner` into the block without checking it, so a reply can corrupt or inject content into a file.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/metafill.py",
      "line": 108,
      "message": "`fields[\"owner\"] = entry.owner.strip()` writes the model's owner into the composed block without any check. `meta._render` emits `owner: {value}` verbatim, and the only purpose-style check (no newline, no `\\r`, no `-->`) is applied to `purpose` alone. A reply owner such as `x\\n-->\\nanything` therefore ends a `.md` block early and writes arbitrary text into the file. On a `.py` file it adds lines that are not part of the block, so the next `meta refresh` or `check` reports the file as malformed. That breaks the ticket's rule that the model is never given a way to edit a file, and it leaves a written file corrupt.",
      "paved_road": "Before writing, validate a nonblank reply owner the same way as `purpose`: reject the entry with a reason such as `invalid owner` when it contains a newline, `\\r` or `-->`. Keep the rule that a blank owner is skipped. Add a case to `tests/unit/test_meta_fill.py` showing that such an owner leaves the file byte-identical and lists it as rejected.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.9",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
