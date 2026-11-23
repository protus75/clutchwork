# Review: snag

The fallback notice and its test do what the ticket asks, but `except ValueError` also catches `UnicodeDecodeError` from the file read inside `render_context`, so it hides errors other than the selector error, which the ticket's Definition of rejected forbids.

## Findings

- [logic] clutch/stages.py:657 `render_context` is `context_excerpt(entry, (repo / context_path(entry)).read_text())`, so the try block also covers the file read. `UnicodeDecodeError` is a subclass of `ValueError`. A ticket Context file that is not valid UTF-8, with or without a selector, used to raise. It now becomes the notice `selector does not resolve in this worktree: 'utf-8' codec can't decode ...`. That hides an error other than the selector ValueError and labels it wrongly as a selector problem. The Definition of rejected says: "The branch swallows errors other than the selector ValueError." (do instead: Narrow the guard to selector resolution. In `implement_inputs`, read the text outside the try with `text = (repo / context_path(p)).read_text()`, then wrap only `context_excerpt(p, text)` in try/except ValueError. Both are already in `clutch/tickets.py`, which this change leaves alone. Decode errors and missing files then still raise as before. Alternatively, re-raise when `isinstance(exc, UnicodeDecodeError)`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "5390734314a3313e8c0f8d0f43fd0abf3e2bd4da",
  "stem": "implement-context-unresolved-selector-notice",
  "reviewed_sha": "5390734314a3313e8c0f8d0f43fd0abf3e2bd4da",
  "summary": "The fallback notice and its test do what the ticket asks, but `except ValueError` also catches `UnicodeDecodeError` from the file read inside `render_context`, so it hides errors other than the selector error, which the ticket's Definition of rejected forbids.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/stages.py",
      "line": 657,
      "message": "`render_context` is `context_excerpt(entry, (repo / context_path(entry)).read_text())`, so the try block also covers the file read. `UnicodeDecodeError` is a subclass of `ValueError`. A ticket Context file that is not valid UTF-8, with or without a selector, used to raise. It now becomes the notice `selector does not resolve in this worktree: 'utf-8' codec can't decode ...`. That hides an error other than the selector ValueError and labels it wrongly as a selector problem. The Definition of rejected says: \"The branch swallows errors other than the selector ValueError.\"",
      "paved_road": "Narrow the guard to selector resolution. In `implement_inputs`, read the text outside the try with `text = (repo / context_path(p)).read_text()`, then wrap only `context_excerpt(p, text)` in try/except ValueError. Both are already in `clutch/tickets.py`, which this change leaves alone. Decode errors and missing files then still raise as before. Alternatively, re-raise when `isinstance(exc, UnicodeDecodeError)`.",
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
