<!-- clutch:meta
schema: clutch.meta/1.0
kind: plan
purpose: Private remote Clutch viewer for desktop browsers and Android tablets over Tailscale, with staged delivery and acceptance checks
relates: [clutch/observe.py, clutch/graph.py, vscode-clutchwork/extension.js, docs/how-clutch-works.md]
owner: engine
verified: e77de812
hash: 1344052b5b8051bb4d36abe2d950e81253672f98fa2f637570d6a4dfce1d4f50
-->
# Private remote Clutch view

## Status and decisions

Proposed 2026-11-22. This document plans future behavior; it does not describe a shipped web service.

The owner wants a remote version of the extension view, accessible on a private network, including an Android tablet connected through Tailscale. Build a responsive web app first. A native Android app is optional later and would consume the same service.

Working scope for the first release: one repository per service process and read-only viewing. Remote controls remain a separate proposed phase, pending the owner's decision. Public internet hosting is outside this plan.

## Intended experience

1. Start the viewer on the machine containing the repository and Clutch state.
2. Expose its loopback listener privately through Tailscale Serve.
3. Connect the Android tablet to the same tailnet and open the service's HTTPS URL in its browser.
4. Browse the ticket graph, selected ticket details, recent activity, Suggestion Box messages, and available run records.
5. Optionally install the web app to the tablet's home screen.

The repository machine must be awake and reachable. VS Code need not be running. The viewer operates whether the engine is active or stopped.

Tailscale supports Android clients, and Serve makes a local service available within a tailnet. Serve provides the private HTTPS entry point; access must be restricted to the intended users/devices using tailnet policy. No router port forwarding or public endpoint is required. References: [Tailscale device access, including Android](https://tailscale.com/docs/use-cases/personal-or-at-home-use/access-nas-media-file-servers), [Tailscale Serve](https://tailscale.com/docs/features/tailscale-serve), and [Serve examples and access controls](https://tailscale.com/docs/reference/examples/serve).

## Existing foundation

- `clutch/observe.py::snapshot` builds the extension snapshot, including ticket rows, display details, activity, Suggestion Box data, help, counts, and engine state.
- `clutch/graph.py` owns graph layout. Clients receive lane decisions and draw them.
- `vscode-clutchwork/extension.js` obtains the snapshot through `clutch view snapshot` and distributes it to extension views. It also provides VS Code-specific file opening, menus, watchers, and command execution.
- `vscode-clutchwork/media/graph.js`, `view.js`, `detail.js`, and `box.js` contain browser rendering code. The view scripts currently depend on VS Code messaging and styling.
- Stats are fetched separately by the extension; they are not automatically supplied by the main snapshot.

The existing snapshot also contains machine-local paths, commands, and watcher information. It is not an HTTP response contract as-is.

## Architecture and ownership

```text
Repository + journal + existing Clutch projections
                    |
           Python viewer service
          loopback HTTP listener
                    |
         Tailscale Serve: HTTPS
         tailnet access policy
                    |
        Desktop or Android browser
```

The service serves the application and its API from one origin. It invokes the existing Python observation capabilities rather than launching VS Code or introducing a second state store. Files and journal remain authoritative; HTTP responses and any in-memory snapshots are rebuildable projections.

| Boundary | Disposition | Owner and contract |
|---|---|---|
| State and display projection | Reuse | `clutch/observe.py`; preserve ticket ordering, status, help, and existing admission decisions. Add any newly needed domain display fields here. |
| Graph layout | Reuse | `clutch/graph.py`; remains pure, with no network, clock, color, or pixel decisions. |
| Remote HTTP API and service lifecycle | Create | A new Python viewer module in `clutch/`, with its exact path chosen when authoring implementation. This independently accessed network boundary is earned by the browser client. It owns request validation, response shape, artifact identifiers, errors, and shutdown, not ticket policy. |
| Client rendering | Extend | Existing extension rendering assets where practical; share drawing code between browser and VS Code, with explicit host adapters for transport, links, and theme. Migrate every affected consumer together. |
| Artifact access | Create | The viewer API maps known record identifiers to permitted artifacts using Clutch's filesystem seam. Browser input never supplies an arbitrary filesystem path. |
| Remote transport and access | Reuse | Tailscale owns private connectivity, HTTPS termination, and tailnet access policy. Clutch owns its loopback listener and validates HTTP requests. |

Keep browser JavaScript thin: rendering, navigation, selection, and transport. Ordering, eligibility, row selection rules, graph layout, and domain time displays stay in Python. Responsive layout is client presentation.

## Phase 1: read-only service

Deliver the service and an explicit browser response contract before adding controls.

- Add a command under the existing `view` group. Its final name is chosen with CLI help and documentation in the implementation change; do not reuse `engine serve`, which owns engine orchestration.
- Run one repository per process, with explicit start, shutdown, bind-conflict, configuration-error, and unavailable-state behavior. Follow existing process and injectable seam conventions.
- Bind to loopback. The service does not need the engine writer lock; its observation/cache access must use existing concurrency behavior safely alongside drain or serve.
- Return an allowlisted projection of existing snapshot data. Exclude local command argv, watcher roots, configuration locations, and absolute machine paths. Include only fields with a browser consumer.
- Provide application assets, snapshot refresh, and known artifact retrieval. Specify route names, response fields, errors, and size limits in the implementation contract and tests.
- Permit only known ticket/run/check/review/diagnosis and Suggestion Box records needed by the interface. Reject traversal, symlink escape, unknown identifiers, and access to configuration, secrets, or arbitrary checkout files.
- Render record contents as text or safely rendered Markdown. Repository content must not execute scripts in the viewer.
- Start with polling while the page is visible and a manual refresh action. Coalesce overlapping refreshes so concurrent clients do not start duplicate snapshot builds. Keep this state in memory; add no database or event bus.
- Include snapshot generation time and distinguish a failed refresh from a successful empty state. Account for records disappearing between listing and opening.
- Accept only read operations. Serve through the intended origin, reject unexpected Host values, and do not allow arbitrary cross-origin API reads.

Acceptance: the same repository state produces matching rows, ordering, statuses, and lanes in the extension and remote projection; permitted artifacts open; disallowed requests fail; drain continues undisturbed; refresh failures do not look like current data.

## Phase 2: desktop and Android interface

- Desktop: ticket graph/list alongside selected details, with activity and Suggestion Box views.
- Tablet: usable portrait and landscape layouts; tapping selects a row and opens details with a clear return path. Essential information never requires hover or a context menu.
- Show engine state, counts, help, last successful refresh, loading, empty, disconnected, and stale states.
- Allow opening the permitted records from details and activity. Translate help links to browser-readable documentation rather than editor file commands.
- Retain the last successful snapshot in memory during a connection failure and label it stale. Recover automatically after reconnection without losing selection when that selection still exists.
- Share the graph renderer and applicable detail rendering with the extension. Replace host-specific assumptions explicitly; avoid a general frontend framework or plugin system unless implementation demonstrates a need.
- Keep VS Code behavior working after any shared asset extraction.

Acceptance: desktop and a physical Android tablet can navigate graph, details, activity, messages, help, and records using mouse or touch. All domain ordering and graph decisions still originate in Python.

## Phase 3: Tailscale access and home-screen installation

- Document setup on both the repository machine and Android tablet, including the service's Clutch start verb and Tailscale's supported Serve setup.
- Use Tailscale Serve for the loopback service's private HTTPS URL. Document restricting access to the owner and verifying that an unauthorized device cannot reach the viewer. Do not enable Funnel, which provides public access.
- Keep private network access distinct from per-person application login: the initial deployment trusts the authorized tailnet audience and local host. Application accounts are outside the first release.
- Add the web manifest, icons, and browser metadata needed for home-screen installation on a supported Android browser. Verify actual install behavior; add a service worker only if required by that behavior.
- Keep sensitive API responses out of persistent offline caches. Any application-shell cache must not retain ticket bodies or run records.
- Document restart and shutdown behavior, including that engine stop does not stop the viewer and viewer shutdown does not stop the engine.

Acceptance: the owner can open and install the viewer on the tablet over Tailscale while away from the repository machine's LAN. Disabling the tablet's tailnet connection removes remote reachability; unauthorized access fails; reconnecting restores the view.

## Proposed later phase: remote controls

This phase requires an explicit scope decision after read-only viewing works.

Candidate actions are ticket confirm/reject and engine start/stop/kill. Each action needs a closed API operation that delegates to the existing canonical command/admission behavior, rechecks current eligibility and locks at submission, and returns the actual accepted or refused result. Client-supplied commands and argv are never executable input.

Before enabling writes, define request authentication/authorization, same-origin and CSRF protection, operator identity in the existing run/journal model where supported, duplicate-submission behavior, and confirmation for disruptive controls. Verify stale views cannot bypass admission or reset spent caps. Retain existing journal semantics rather than creating a parallel action ledger.

Native Android, notifications, streaming updates, multiple repositories, public hosting, editing tickets, and remote editor/agent sessions are outside the initial deliverable. Revisit each only with a concrete need.

## Verification and documentation

Use `./dev.py test` for automated verification. Add focused test modules rather than growing the repository's hot integration files.

- Fake-driven tests cover projection parity, request validation, artifact confinement, escaping, failure responses, snapshot refresh coalescing, and shutdown.
- Real network/filesystem tests, if required, use the repository's approved real-I/O test path and allowlist. Integration tests never consume this checkout's live tickets or journal.
- Check that the browser projection removes local-only fields, cannot read arbitrary paths, and cannot mutate tickets or invoke controls in the read-only release.
- Verify observation can coexist with engine activity and respects existing cache synchronization.
- Check shared rendering in both VS Code and the browser after extraction.
- Perform the physical Android/Tailscale acceptance checks separately; in-memory tests cannot establish remote reachability or installation behavior.
- Update command help, applicable host guides, the command tables in `docs/how-clutch-works.md` and `clutch/docs/host-running.md`, and relevant READMEs when the command ships. Browser help must reuse the existing help owner rather than copy policy text.

No standing tests should pin this plan's wording. Implementation tests pin the delivered contracts.

## Delivery sequence and completion

Sequence: Phase 1 service and contract, Phase 2 responsive viewer, then Phase 3 private deployment and Android installation. Each phase needs its own bounded implementation work, with dependencies only where it consumes preceding merged code. This plan does not add roadmap rows or authorize implementation by itself.

The first release is complete when the owner can privately inspect the repository from the Android tablet, with matching engine facts, readable records, clear stale-state handling, and no VS Code dependency, while the engine continues running normally.

The private-network choice is settled. The remaining product decision is whether remote controls should join the first release; this plan defaults to read-only until that is decided.
