## Outcome

ok

## Surprises / judgment calls

The dashboard’s shared ticket view restores pinned focus during rendering, so project switches clear its pin as well as the dashboard focus; this is the minimum change needed to prevent stale ticket details.

## Dead ends

A focus-reset mutation initially passed because the shared ticket view independently cleared an unpinned selection; the test now pins a ticket present in both projects and rejects the wrong behavior.

## Second problems filed

- box-001184-10fc7f9f: docs/antigravity-plan.md still describes the MCP default repository as the current working directory; that file is outside the ticket’s scope fence.

## Resolved engine/model

- provider: codex
- model: gpt-6.1-terra
- spec: implement 2.29

## Predicted vs actual

Ticket budget: 15 minutes expected, 30 minutes stuck; actual time not measured.

