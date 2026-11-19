# Review: snag

The fix in `handle_install` and the reproducer meet the ticket, but the new unit test checks the real filesystem outside `tmp_path`.

## Findings

- [logic] tests/unit/test_install_verb.py:92 `test_install_refuses_broken_binary` calls `cli.main(["provider", "install", "claude"], cwd=Path("/repo"), ...)` without patching `Path.is_file`. `cli_status` then runs `Path("/repo/node_modules/.bin/claude").is_file()` against the real disk, outside `tmp_path`. This makes the unit test depend on the machine's filesystem. The existing `test_install` and `test_status` patch `Path.is_file` to avoid exactly this. (do instead: Add `monkeypatch.setattr(Path, "is_file", lambda self: False)` (or `True` for the project path) in `test_install_refuses_broken_binary` before calling `cli.main`, as `test_install` does.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "1946a1346b1efb53dbe963cde3285cb4c78e3072",
  "stem": "provider-install-verifies-binary",
  "reviewed_sha": "1946a1346b1efb53dbe963cde3285cb4c78e3072",
  "summary": "The fix in `handle_install` and the reproducer meet the ticket, but the new unit test checks the real filesystem outside `tmp_path`.",
  "findings": [
    {
      "code": "logic",
      "path": "tests/unit/test_install_verb.py",
      "line": 92,
      "message": "`test_install_refuses_broken_binary` calls `cli.main([\"provider\", \"install\", \"claude\"], cwd=Path(\"/repo\"), ...)` without patching `Path.is_file`. `cli_status` then runs `Path(\"/repo/node_modules/.bin/claude\").is_file()` against the real disk, outside `tmp_path`. This makes the unit test depend on the machine's filesystem. The existing `test_install` and `test_status` patch `Path.is_file` to avoid exactly this.",
      "paved_road": "Add `monkeypatch.setattr(Path, \"is_file\", lambda self: False)` (or `True` for the project path) in `test_install_refuses_broken_binary` before calling `cli.main`, as `test_install` does.",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.7",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
