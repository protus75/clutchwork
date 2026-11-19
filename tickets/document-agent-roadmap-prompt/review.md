# Review: snag

The prompt, facet, dispatch, tests and doc tables match the ticket, but the README line telling users about the prompt sits in the section that only covers developing Clutch's own repo, so operators on installed hosts won't find it there.

## Findings

- [acceptance] README.md:115 The new line "Use `clutch prompt roadmap` to print the procedure for creating or maintaining `docs/roadmap.md`..." was appended under `## Developing clutch`, which README line 106 says "is for working on clutch's own repository". The ticket's goal is a prompt for operators on Clutch itself *or an independently installed host*, and Scope in asks README to document invocation, output and handoff for that operator. In this spot, host operators are told the verb applies only to Clutch's own checkout. The line also uses bare `clutch` where every other command in the README uses `uv run clutch`. (do instead: Move the sentence into the host-operator part of README.md, for example next to the planning example under `## Observe and decide` ("Help me plan this feature..."). Write it as `uv run clutch prompt roadmap`, hand off through `uv run clutch roadmap status` and `uv run clutch prompt plan-ticket-drain`, and remove it from `## Developing clutch`.)

## Record

```json
{
  "artifact_schema_version": 1,
  "produced_by_spec_version": 1,
  "produced_at_sha": "99812d81bcd231e61b9d62a1ee5bbf8dcb6624e9",
  "stem": "document-agent-roadmap-prompt",
  "reviewed_sha": "99812d81bcd231e61b9d62a1ee5bbf8dcb6624e9",
  "summary": "The prompt, facet, dispatch, tests and doc tables match the ticket, but the README line telling users about the prompt sits in the section that only covers developing Clutch's own repo, so operators on installed hosts won't find it there.",
  "findings": [
    {
      "code": "acceptance",
      "path": "README.md",
      "line": 115,
      "message": "The new line \"Use `clutch prompt roadmap` to print the procedure for creating or maintaining `docs/roadmap.md`...\" was appended under `## Developing clutch`, which README line 106 says \"is for working on clutch's own repository\". The ticket's goal is a prompt for operators on Clutch itself *or an independently installed host*, and Scope in asks README to document invocation, output and handoff for that operator. In this spot, host operators are told the verb applies only to Clutch's own checkout. The line also uses bare `clutch` where every other command in the README uses `uv run clutch`.",
      "paved_road": "Move the sentence into the host-operator part of README.md, for example next to the planning example under `## Observe and decide` (\"Help me plan this feature...\"). Write it as `uv run clutch prompt roadmap`, hand off through `uv run clutch roadmap status` and `uv run clutch prompt plan-ticket-drain`, and remove it from `## Developing clutch`.",
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
