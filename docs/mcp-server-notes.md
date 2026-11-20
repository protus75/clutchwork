# MCP server: design notes

Status: exploratory notes from a chat on 2026-11-19. Nothing is decided, ticketed, or built. Not on the roadmap.

## Question

Should clutch be an MCP server, or stay a CLI tool?

## Position

Keep the CLI as the core. Add a thin MCP adapter on top only if agents need to drive clutch interactively.

## Why the CLI stays the foundation

- Clutch is a long-running daemon with a journal, lockfile, and worktrees. That is process-owner state. An MCP server is normally a request/response tool host tied to a client session, which is the wrong lifecycle for a drain that must survive editor reloads (see `drain-survives-editor-reload`).
- The rules already assume the CLI shape: every task is a `clutch` verb, external binaries go through argv-list wrappers, and guides name verbs. Claude, codex, humans, CI, and the VS Code extension all call the CLI today with no extra protocol.
- Tickets and gates are file-based, and files plus the journal are the source of truth, so any front end can read them.

## Where MCP would earn its place

- Typed, structured results for chat sessions (`ticket new`, `ticket lint`, `ticket review`, `view status`, `box suggest`) instead of parsed text.
- Discoverability: agents get tool schemas instead of reading help text.
- Remote or monitoring use, where a read-only status server fits (see the `remote-monitoring-drain-session` ticket draft).

## Shape, if built

- Every verb stays in the CLI as the single implementation. The MCP server is a thin adapter (same argv wrappers or the same functions) and adds no logic. This matches the "thin wrapper, clutch owns the logic" rule for the extension.
- Start read-only (status, ticket view, lint). Add mutating verbs only later.
- Never expose daemon lifecycle (start or stop drain).
- It must not become a second authority (no dual-path code).

## Effect on host projects

- Gains: no clutch on the host's PATH or venv; typed tools for the agent.
- Unchanged: the host still needs the managed rules block from `clutch host core`, and agents still read the authoring guides locally.
- Cost: each host needs an MCP config entry (`.mcp.json` or the codex equivalent), which is one more setup step and one more thing to drift.

## One server for several hosts

- Stdio MCP servers are spawned per client session, so a single shared server means an HTTP transport: a long-lived local service with its own lifecycle, port, and auth.
- It would route by a `host` argument on each tool, run the verb against that host's directory, and hold no state of its own.
- Each host keeps its own journal, lockfile, and worktrees. Drains in different hosts do not conflict; two writers in one host still do.
- Risk: one HTTP endpoint that can run mutating verbs across all repos widens the trust surface (clutch is "fenced by gates, not jailed"). Read-only status, ticket view, and lint across hosts is a safe fit; mutating verbs would need auth and a host allowlist.
- This is the strongest argument for MCP. Ticket authoring and the drain stay CLI verbs run in each host.

## Open questions

- Whether to draft a ticket for a read-only MCP adapter.
- Whether clutch already has a multi-host registry. If not, that is the prerequisite for any shared server. Not yet checked in the code.
