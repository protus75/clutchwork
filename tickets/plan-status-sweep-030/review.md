# Review: snag

The cited claims check out against the code, but the driver plan's summary rewrite now only says what the operator used to do by hand and drops the statement that the driver handles held tickets.

## Findings

- [logic] docs/roadmap-driver-plan.md:3 Scope item 6 asks to place the operator's by-hand work before the supervisor step (rows 89 and 96). The rewrite instead replaced the whole sentence 'When a ticket is held for a person, the driver does what the operator does today by hand: ...' with 'Before the supervisor step (rows 89 and 96), the operator handled held tickets by ...'. The plan summary now describes only the past manual process and no longer says that the driver, through `failure_terminal`/`supervise_step`, does this for held tickets. That removes the driver's held-ticket role from the summary of a plan whose subject is running the roadmap unattended. (do instead: Keep the driver as the subject and put the manual process in the past, e.g. 'When a ticket is held for a person, the driver's supervisor step (rows 89 and 96) reads the diagnosis, edits the ticket within the supervising rules, has the edit reviewed, and keeps the ticket, a bounded number of times; before it the operator did this by hand.')

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "c0e02bac2a9db7b165faa892bd91969633e3ddd1",
  "stem": "plan-status-sweep-030",
  "reviewed_sha": "c0e02bac2a9db7b165faa892bd91969633e3ddd1",
  "summary": "The cited claims check out against the code, but the driver plan's summary rewrite now only says what the operator used to do by hand and drops the statement that the driver handles held tickets.",
  "findings": [
    {
      "code": "logic",
      "path": "docs/roadmap-driver-plan.md",
      "line": 3,
      "message": "Scope item 6 asks to place the operator's by-hand work before the supervisor step (rows 89 and 96). The rewrite instead replaced the whole sentence 'When a ticket is held for a person, the driver does what the operator does today by hand: ...' with 'Before the supervisor step (rows 89 and 96), the operator handled held tickets by ...'. The plan summary now describes only the past manual process and no longer says that the driver, through `failure_terminal`/`supervise_step`, does this for held tickets. That removes the driver's held-ticket role from the summary of a plan whose subject is running the roadmap unattended.",
      "paved_road": "Keep the driver as the subject and put the manual process in the past, e.g. 'When a ticket is held for a person, the driver's supervisor step (rows 89 and 96) reads the diagnosis, edits the ticket within the supervising rules, has the edit reviewed, and keeps the ticket, a bounded number of times; before it the operator did this by hand.'",
      "kind": null,
      "unit": null
    }
  ],
  "spec_version": "1.6",
  "provider": "claude",
  "model": "claude-opus-5-5",
  "verdict": "snag"
}
```
