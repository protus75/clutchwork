# Review: approve

The seam now spawns with `subprocess.Popen` and reaps each child itself with `os.wait4` on a pidfd reader, which fixes the prior shared-executor finding; it passes rusage per child to `on_rusage` on the normal, timeout and cancellation paths, keeps the `_kill_and_wait(proc)`/`kill_group(proc.pid)` source pins and the return contract, and the new tests and the host-contract sentence cover every acceptance criterion.

## Findings

none

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "3a0430869f310410d51620e30350e2bc97c008aa",
  "stem": "exec-seam-owns-reap",
  "reviewed_sha": "3a0430869f310410d51620e30350e2bc97c008aa",
  "summary": "The seam now spawns with `subprocess.Popen` and reaps each child itself with `os.wait4` on a pidfd reader, which fixes the prior shared-executor finding; it passes rusage per child to `on_rusage` on the normal, timeout and cancellation paths, keeps the `_kill_and_wait(proc)`/`kill_group(proc.pid)` source pins and the return contract, and the new tests and the host-contract sentence cover every acceptance criterion.",
  "findings": [],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "approve"
}
```
