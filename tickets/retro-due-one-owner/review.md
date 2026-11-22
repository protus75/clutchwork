# Review: rma

The diff does what the ticket says, but the ticket's pure no-I/O `due_trigger` built only on `measurements(window)` cannot keep the `override` spike trigger, which `production_evidence` alone counts from invoices read with `git show`, so the ticket's 'trigger kinds unchanged' promise cannot be met as written.

## Findings

- [ticket] clutch/retro.py:205 `due_trigger` passes `measurements(window)` to `select_trigger`, and `Retro.__call__` (lines 431-434) now picks its trigger from that before it awaits `production_evidence`. The `override` spike count is only added inside `production_evidence` (`evidence["spikes"]["override"] += bool(invoices[check.key].bypassed)`, retro.py:247). It needs each checks invoice read through `checkout.git._run(..., "show", ...)`, and the journal does not record `bypassed`. `override` is a default-enabled `SpikeKind` (config.py:24, 244). So a window whose only due signal is an override spike now returns `None` from `Retro.__call__`, and drain and `clutch engine retro` never run that retro. This breaks the Boundary contract's 'trigger kinds ... are unchanged'. The ticket also requires `due_trigger` to read only `measurements(window)` with no I/O, and that `production_evidence` never runs before a trigger is selected on an unforced call. No in-fence implementation can satisfy all three. (do instead: A human changes the ticket to pick one of these: (a) make the journal record check bypasses, for example a `bypassed` field on the checks effect completion body written by the Check stage (a path outside this fence), and have `measurements` count `override` from it, adding that path to the fence; (b) explicitly accept dropping the `override` trigger, or moving it to post-evidence selection, and update the compatibility line and the docs; or (c) allow `due_trigger` to fall back to `production_evidence` only when `override` is the sole kind that could reach the threshold, and state that exception in Scope in and Definition of rejected.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "aae1ef08c50c746556745a9f811ca3f69689cbfd",
  "stem": "retro-due-one-owner",
  "reviewed_sha": "aae1ef08c50c746556745a9f811ca3f69689cbfd",
  "summary": "The diff does what the ticket says, but the ticket's pure no-I/O `due_trigger` built only on `measurements(window)` cannot keep the `override` spike trigger, which `production_evidence` alone counts from invoices read with `git show`, so the ticket's 'trigger kinds unchanged' promise cannot be met as written.",
  "findings": [
    {
      "code": "ticket",
      "path": "clutch/retro.py",
      "line": 205,
      "message": "`due_trigger` passes `measurements(window)` to `select_trigger`, and `Retro.__call__` (lines 431-434) now picks its trigger from that before it awaits `production_evidence`. The `override` spike count is only added inside `production_evidence` (`evidence[\"spikes\"][\"override\"] += bool(invoices[check.key].bypassed)`, retro.py:247). It needs each checks invoice read through `checkout.git._run(..., \"show\", ...)`, and the journal does not record `bypassed`. `override` is a default-enabled `SpikeKind` (config.py:24, 244). So a window whose only due signal is an override spike now returns `None` from `Retro.__call__`, and drain and `clutch engine retro` never run that retro. This breaks the Boundary contract's 'trigger kinds ... are unchanged'. The ticket also requires `due_trigger` to read only `measurements(window)` with no I/O, and that `production_evidence` never runs before a trigger is selected on an unforced call. No in-fence implementation can satisfy all three.",
      "paved_road": "A human changes the ticket to pick one of these: (a) make the journal record check bypasses, for example a `bypassed` field on the checks effect completion body written by the Check stage (a path outside this fence), and have `measurements` count `override` from it, adding that path to the fence; (b) explicitly accept dropping the `override` trigger, or moving it to post-evidence selection, and update the compatibility line and the docs; or (c) allow `due_trigger` to fall back to `production_evidence` only when `override` is the sole kind that could reach the threshold, and state that exception in Scope in and Definition of rejected.",
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
