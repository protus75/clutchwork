# Review: snag

The registry, coverage, links, and tests meet the criteria, but an unresolved heading or verb row escapes help_map as a bare, message-less StopIteration instead of a proper error naming the topic and missing target.

## Findings

- [logic] chupa/help.py:227 A missing verb row in the run guide surfaces as a bare `StopIteration` from `next(...)`, with no message naming the verb or the doc. A StopIteration leaking from a plain function is also a known hazard. Inside a generator it becomes `RuntimeError`, and inside an iterator-consuming caller such as `map(...)` it silently ends iteration, which defeats the ticket's rule that the builder never returns a partial map. The operator gets no paved road to the stale row. (do instead: Use `next(..., None)`. When it returns None, raise a real exception (e.g. `ValueError`/`LookupError`) whose message names the topic key, the verb, and the doc path, and says to restore the row or update `chupa/help.py`. Update `tests/unit/test_help.py::test_unresolved_link_raises` (lines 62 and 66) to expect that exception type instead of `StopIteration`.)
- [logic] chupa/help.py:232 A renamed or missing packaged-doc heading surfaces as a bare `StopIteration` from `next(...)`, with no message naming the topic or heading. This is the same message-less, iteration-unsafe failure as the verb-row lookup. (do instead: Use `next(..., None)` and raise a real exception (e.g. `ValueError`/`LookupError`) naming the topic key, the expected heading, and the doc path. Have the unit test assert that exception type.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "8422e25c92785462c481a70c1cabb8d7536de090",
  "stem": "vscode-help-catalog",
  "reviewed_sha": "8422e25c92785462c481a70c1cabb8d7536de090",
  "summary": "The registry, coverage, links, and tests meet the criteria, but an unresolved heading or verb row escapes help_map as a bare, message-less StopIteration instead of a proper error naming the topic and missing target.",
  "findings": [
    {
      "code": "logic",
      "path": "chupa/help.py",
      "line": 227,
      "message": "A missing verb row in the run guide surfaces as a bare `StopIteration` from `next(...)`, with no message naming the verb or the doc. A StopIteration leaking from a plain function is also a known hazard. Inside a generator it becomes `RuntimeError`, and inside an iterator-consuming caller such as `map(...)` it silently ends iteration, which defeats the ticket's rule that the builder never returns a partial map. The operator gets no paved road to the stale row.",
      "paved_road": "Use `next(..., None)`. When it returns None, raise a real exception (e.g. `ValueError`/`LookupError`) whose message names the topic key, the verb, and the doc path, and says to restore the row or update `chupa/help.py`. Update `tests/unit/test_help.py::test_unresolved_link_raises` (lines 62 and 66) to expect that exception type instead of `StopIteration`.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "chupa/help.py",
      "line": 232,
      "message": "A renamed or missing packaged-doc heading surfaces as a bare `StopIteration` from `next(...)`, with no message naming the topic or heading. This is the same message-less, iteration-unsafe failure as the verb-row lookup.",
      "paved_road": "Use `next(..., None)` and raise a real exception (e.g. `ValueError`/`LookupError`) naming the topic key, the expected heading, and the doc path. Have the unit test assert that exception type.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.5",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
