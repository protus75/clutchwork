# Review: snag

The ticket kind is implemented correctly and the tests cover every acceptance criterion, but the source mapping makes its own copy of the `box:<class>` pattern instead of using the existing `clutch/tickets.py::Source` owner.

## Findings

- [scope] clutch/training.py:145 `re.fullmatch(r"box:[a-z][a-z0-9_]*", source)` repeats the `box:` branch of the `Source` pattern in clutch/tickets.py (`^(human|seed|box:[a-z][a-z0-9_]*)$`). The ticket lists `clutch/tickets.py::Source` in Context, so this is a second parser for a closed vocabulary that already has an owner, and the two copies will drift if `Source` changes. (do instead: Check the value against `Source`, for example with `pydantic.TypeAdapter(Source).validate_python(source)` and a `ValidationError` mapped to skipped. Then map `human` to human and a `box:` prefix to author, and skip `seed` and any value that fails validation.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "fe614526fdf7dbf66537e51cdc1a1973d1e84c04",
  "stem": "training-export-ticket",
  "reviewed_sha": "fe614526fdf7dbf66537e51cdc1a1973d1e84c04",
  "summary": "The ticket kind is implemented correctly and the tests cover every acceptance criterion, but the source mapping makes its own copy of the `box:<class>` pattern instead of using the existing `clutch/tickets.py::Source` owner.",
  "findings": [
    {
      "code": "scope",
      "path": "clutch/training.py",
      "line": 145,
      "message": "`re.fullmatch(r\"box:[a-z][a-z0-9_]*\", source)` repeats the `box:` branch of the `Source` pattern in clutch/tickets.py (`^(human|seed|box:[a-z][a-z0-9_]*)$`). The ticket lists `clutch/tickets.py::Source` in Context, so this is a second parser for a closed vocabulary that already has an owner, and the two copies will drift if `Source` changes.",
      "paved_road": "Check the value against `Source`, for example with `pydantic.TypeAdapter(Source).validate_python(source)` and a `ValidationError` mapped to skipped. Then map `human` to human and a `box:` prefix to author, and skip `seed` and any value that fails validation.",
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
