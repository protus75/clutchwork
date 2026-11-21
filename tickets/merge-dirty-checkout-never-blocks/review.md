# Review: snag

The config.yaml exemption and the 3-way reapply work on the success path, but a failure after the squash deletes the only saved copy of the owner's edit, and the unit test cannot catch a missing or wrong `--ours` merge.

## Findings

- [logic] clutch/merge.py:372 If `git merge-file` raises after `merge_squash` has committed (for example a GitError from a binary or unreadable file, or a negative exit), the `finally` block still removes `merge-config-local`. That file is the only saved copy of the owner's edit, and `config.yaml` is left holding the merged ticket content. The owner's edit is then permanently lost, which the ticket's Definition of rejected names explicitly ('the owner's edit lost or overwritten'). (do instead: On any exception from the merge-file reapply, write `original` back to `config.yaml` before re-raising, as the `merge_squash` failure branch already does. Or only remove `local` once the reapply has succeeded. Add a unit case where the fake `merge-file` raises and assert that `config.yaml` equals the owner's original bytes afterwards.)
- [logic] tests/unit/test_merge_config_local.py:63 Criterion 2 requires the unit test to show 'owner's lines win on conflict', but the fake `merge-file` writes 'owner wins' unconditionally and the test only checks the command names (`show`, `checkout`, `merge-file`). It would still pass if `--ours` were dropped or if the current/base/other paths were swapped so that the ticket's lines won, so it cannot fail on the conflict policy it claims to test. (do instead: Assert the full `merge-file` argv: `("merge-file", "--ours", str(state/merge-config-local), str(state/merge-config-base), str(config))`. That pins the owner-wins flag and the current/base/other order.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "b8bc14344376f3d391f39ea5e2dd5bc08e356582",
  "stem": "merge-dirty-checkout-never-blocks",
  "reviewed_sha": "b8bc14344376f3d391f39ea5e2dd5bc08e356582",
  "summary": "The config.yaml exemption and the 3-way reapply work on the success path, but a failure after the squash deletes the only saved copy of the owner's edit, and the unit test cannot catch a missing or wrong `--ours` merge.",
  "findings": [
    {
      "code": "logic",
      "path": "clutch/merge.py",
      "line": 372,
      "message": "If `git merge-file` raises after `merge_squash` has committed (for example a GitError from a binary or unreadable file, or a negative exit), the `finally` block still removes `merge-config-local`. That file is the only saved copy of the owner's edit, and `config.yaml` is left holding the merged ticket content. The owner's edit is then permanently lost, which the ticket's Definition of rejected names explicitly ('the owner's edit lost or overwritten').",
      "paved_road": "On any exception from the merge-file reapply, write `original` back to `config.yaml` before re-raising, as the `merge_squash` failure branch already does. Or only remove `local` once the reapply has succeeded. Add a unit case where the fake `merge-file` raises and assert that `config.yaml` equals the owner's original bytes afterwards.",
      "kind": null,
      "unit": null
    },
    {
      "code": "logic",
      "path": "tests/unit/test_merge_config_local.py",
      "line": 63,
      "message": "Criterion 2 requires the unit test to show 'owner's lines win on conflict', but the fake `merge-file` writes 'owner wins' unconditionally and the test only checks the command names (`show`, `checkout`, `merge-file`). It would still pass if `--ours` were dropped or if the current/base/other paths were swapped so that the ticket's lines won, so it cannot fail on the conflict policy it claims to test.",
      "paved_road": "Assert the full `merge-file` argv: `(\"merge-file\", \"--ours\", str(state/merge-config-local), str(state/merge-config-base), str(config))`. That pins the owner-wins flag and the current/base/other order.",
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
