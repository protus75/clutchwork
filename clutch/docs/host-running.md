<!-- clutch:meta
schema: clutch.meta/1.0
kind: guide
purpose: Operator guide to running ClutchWork on a host: which verbs work while serve runs, writer-lock rules, and the channels and classes for reporting clutch problems upstream
relates: [clutch/docs/host-contract.md]
owner: clutch/docs/host-contract.md
verified: 628fcc0e
hash: 0c88f8c416ca8135139e118a274f9751a9b8ca5bea0358ea3c2aaad473fc095f
-->
# Running ClutchWork on a host

From the host checkout root, with clutch [installed](host-contract.md#install) and `config.yaml` set up as in the [host contract](host-contract.md), run:

```sh
uv run clutch host doctor
uv run clutch engine serve
```

Use the same prefix for the other verbs below; for example, `clutch provider install` reports provider CLIs. The host checkout remains the working directory; `--config PATH` before the verb selects a different config. `engine serve` is the normal mode: it runs until `engine kill`, `engine stop`, or Ctrl-C. `engine drain` is a finite run to quiescence. Closing its terminal, SIGTERM, or Ctrl-C ends it as `engine kill` does. Serve stops on SIGHUP as it does on Ctrl-C: an unjournaled stop that the next start reconciles. A running serve picks up config edits and new ticket files live. Drafts, including a new hand-written ticket authored `state: draft`, wait for `ticket confirm`.

| Verb | Works while serve runs? | What it does |
|---|---|---|
| `view watch` | Yes | Show the live text view; `--once` prints one view. |
| `mcp serve` | Yes | Run the stdio MCP server with read tools including project index search, ticket, Suggestion Box, detached engine-control tools, app-only UI verdict tools, and MCP Prompts. It serves the MCP App resource ui://clutch/dashboard.html and tools clutch_open_dashboard, clutch_app_snapshot, and clutch_app_stats. Supported mutations submit to the running engine's inbox when its lock is held. `--check` verifies the dashboard and tools without serving. |
| `view snapshot` | Yes | Print the extension snapshot as JSON; `snapshot_merged_limit` caps merged rows at 100 by default, and `--all-merged` includes all. |
| `view status` | Yes | Show the journal projection and any evidence size warning. Also reports overdue retro and calibration reminders without running them. |
| `view stats` | Yes | Show the read-only health and efficiency projection. |
| `view events` | Yes | Stream actionable engine changes after a silent baseline; `--once` returns JSON, `--cursor` resumes, and `--timeout` sets the wait in seconds. |
| `ticket lint` | Yes | Validate tickets and graphics judge independence without writing. |
| `engine retro` | Yes | Run a retro report only when invoked, now or queued on the running engine; status and doctor report overdue thresholds. |
| `engine calibrate` | Yes | Run only when invoked; status and doctor report overdue calibration. Journal and print, per provider and model, the median estimate and the median and 90th-percentile actual Implement minutes of the last `calibration.every` completed Implement calls. |
| `host antigravity` | Yes | Install or refresh the global Antigravity plugin (or `--plugin-dir PATH`), or write workspace skills with `--workspace`. `--verify` checks the installed plugin. |
| `host doctor` | No | Inspect setup, including parallel provider concurrency, graphics judge independence and panel provider concurrency; its lock probe reports a held lock as a failure and excess evidence size as a warning. Warns when the installed Antigravity plugin MCP configuration drifts or its executable cannot resolve. Also reports overdue retro and calibration reminders without running them. |
| `prompt` | Yes | List prompts with `prompt list` and render host prompts with `prompt host <name> [stem]`; render an operator prompt for a ticket, a new ticket stem (`author`), named box IDs, all committed drafts, the drain loop, the plan-ticket-drain or plan-ticket-serve kickoff, or roadmap creation and maintenance without writing state; both plan kickoffs require explicit Sonnet selection for Claude subagents; follow the roadmap prompt with `clutch roadmap status` and `clutch prompt plan-ticket-drain`. |
| `host core` | Yes | Refresh managed conduct files. |
| `provider probe` | Yes | Probe declared providers and models. |
| `provider install` | Yes | Install named provider CLIs into the host project as pnpm dev dependencies; with no names, report each adapter's package, location, and version. |
| `config init` | Yes | Print a suggested `config.yaml` from the provider CLIs found and the models they serve; `--write` creates `config.yaml` when none exists. |
| `config update` | Yes | List the model names each declared provider serves and say which configured names are current, replaced, or not served; reports names as unverified when the listing is empty with a problem; writes nothing. |
| `help` | Yes | Print a command's help and examples; `clutch --help <command>` does the same. |
| `host docs` | Yes | Print the installed host guide paths and their purposes. |
| `config migrate` | Yes | Validate and migrate an older config. |
| `engine pause` | Yes | Ask the running engine to pause admission. |
| `engine resume` | Yes | Ask the running engine to release its current hold. |
| `engine kill` | Yes | Ask the running engine to stop at a safe point. |
| `engine stop` | Yes | Finish active work and exit. |
| `ticket review` | Yes | Only the named ticket's pending edits are committed through intake before reviewing the committed ticket. |
| `box suggest` | Yes | File an idea into the Suggestion Box. |
| `box issue` | Yes | Print a prefilled GitHub new-issue link for a critical clutch bug or a process gap; submits nothing. |
| `context suggest` | Yes | Suggest files and sections for a ticket from the index; `--require` exits 1 when none are suggested. |
| `index build` | No | Build or refresh the project index under the writer lock. |
| `index query` | Yes | Search indexed repository chunks read-only without a lock. |
| `meta refresh` | Yes | Insert or refresh configured file metadata under the commit lock. |
| `meta check` | Yes | Report metadata findings without writing. |
| `meta fill` | No | Fill metadata using a read-only model under the writer lock. |
| `roadmap` | No | Author ready rows with `roadmap author [--ahead N]` and maintain their links. `roadmap merged` checks named stems, a release's rows, or a count of tickets merged since a tag, exits 0 when they hold and 1 otherwise, writes nothing, and works while serve runs. With `--parallel`, `roadmap merged` counts only merges whose run overlapped another run and fails when any such ticket spent its conflict-rerun limit. `roadmap status` prints, per release, the rows merged, authored, ready, and blocked and the last gate result, then the next rows to author and the waiting rows. It writes nothing and works while serve runs. `roadmap gate <release>` runs the release's gate block from `docs/roadmap.md`, journals the result, exits 0 when every command passes and 1 otherwise, and works while serve runs. `roadmap accept <release>` reviews release promises, appends gap rows in one commit, exits 0 only with no partial or unmet promise, takes no writer lock, and works while serve runs. |
| `box triage` | Yes | Make one pass over named pending box IDs, or all pending messages. |
| `release ship` | No | Gate the current release, bump and tag it, optionally publish, then run packages; takes the writer lock. |
| `release publish` | No | Run configured `release.pre_build` commands before building the release tagged at HEAD and upload only with `release.publish: true`; never bumps. |
| `release bump` | No | Bump the version with `--minor` or `--patch`, write a new `CHANGELOG.md` section, check, regenerate and commit the Antigravity plugin bundle when present together with `pyproject.toml` and `uv.lock`, and tag `v<version>`; publishes nothing. |
| `box dismiss` | No | Dismiss named box IDs without a model call. |
| `evidence show` | Yes | Print call envelopes and stored normalized event lines. |
| `evidence schema` | Yes | Print the JSON Schema for start, end or event records. |
| `evidence renormalize` | Yes | Rebuild current normalized views from stored raw stdout, preserving older normalizer ids; count skipped calls. |
| `evidence prune` | No | Take the writer lock and prune oldest eligible blobs to the target, printing sizes before and after. |
| `evidence coverage` | Yes | Print known-event percentages and unknown native types by provider and CLI version, and unknown-major-version skip counts. |
| `evidence captures` | Yes | List ticket captures or print one by attempt and name. |
| `training export` | Yes | With `--require-records`, exit 2 after export if any requested kind has no records. With `--kinds` choose implement, preference, review, diagnosis, ticket, conflict, or triage; `--since DATE` filters by call date. Triage labels reflect operator overrides of the verdict. Ticket records include an `authored_by` filter; human tickets without a linked author call are omitted. Exports labelled training records from evidence and merged commits; implement records include a tool-call trajectory unless `--no-trajectory` is set, and `file_purposes` for changed paths found in the index. |
| `training eval` | Yes | Replay held-out review records through the selected route and print agreement to stdout only; exit 2 if no held-out review record was scored; no journal, evidence records or engine log. |
| `coverage map` | Yes | Runs `review.coverage_map.argv` and writes `<state_dir>/coverage-map.json`; exits 0 on success or 2 on refusal. |
| `coverage gate` | Yes | Run a unit command and check its coverage report. |
| `ticket new` | Yes | Create and lint a ticket skeleton. |
| `ticket order` | Yes | Validate and edit a ticket's priority or runs-before ordering. |
| `engine run` | No | Intake the named ticket and run it through the pipeline; other pending tickets are left untouched. |
| `ticket confirm` | Yes | Intake the named ticket, then apply or publish a keep verdict after interactive confirmation; other pending tickets are left untouched. Submission is not applied completion; serve applies ticket verdicts during active Check or model work. |
| `ticket reject` | Yes | Intake the named ticket, then apply or publish a reject verdict with an optional `--reason` after interactive confirmation; other pending tickets are left untouched. Submission is not applied completion; serve applies ticket verdicts during active Check or model work. |
| `engine drain` | No | Run eligible tickets to quiescence. `--detach` runs in its own session, surviving terminal or editor closing, and appends output to `<state_dir>/drain.out`. |
| `engine serve` | No | Run the continuous daemon. `--detach` runs in its own session, surviving terminal or editor closing, appends output to `<state_dir>/serve.out`, and briefly checks startup or reports an immediate refusal. |

Stop serve before `evidence prune`, `index build`, `roadmap author`, `box dismiss`, `release bump`, `release publish`, `release ship`, `engine run`, `engine drain`, or another `engine serve`: each takes the writer lock outright and refuses while it is held. `host doctor` also needs the lock available to pass its probe. There is one writer per host; the kernel releases its lock when the holder exits. Never delete `clutch.lock`—wait for or stop the holder instead.

## Reporting a clutch problem upstream

| Channel | Carries | Ends as |
|---|---|---|
| Suggestion Box (`clutch box suggest`) | The host's own work | A host ticket |
| Host bug reports (`report_inbox`) | The host application's bug reports | A `bug_report` box message, then a host bug ticket |
| Upstream issue (`clutch box issue`) | A critical clutch bug or a process gap, confirmed by the person | A GitHub issue on the clutch repository |

Critical classes:

- `state-loss`: clutch loses or corrupts committed work, tickets, the journal, or git state.
- `secret-leak`: a configured secret reaches a log, journal, prompt, commit, or a process that should not have it.
- `bad-merge`: clutch merges work that failed a hard gate or review, or changed files outside the fence.
- `engine-stuck`: serve or drain cannot run any ticket on a setup `host doctor` passes, and no documented verb releases it.
- `wrong-refusal`: clutch refuses valid config, ticket, or intake with a paved road that cannot be followed.

- `process-gap`: a clutch prompt spec, gate, or process flaw that cost a real run an Implement attempt, a review cycle, or an escalation. The body names the clutch file at fault and the run evidence (attempt count and review findings showing the gap), leaving out the host-private material listed below. A bare idea with no run that paid for it is named to the user in chat and goes nowhere else.

Name any other clutch problem to the user in chat; it goes nowhere else. A session never files a clutch defect to the host's Suggestion Box.

The body contains the clutch file and line, gate or spec text or refusal message, and minimum host detail needed to reproduce. Leave out host-private code or data, ticket files, run records, `host doctor` output, and host paths. The verb appends a version footer and scrubs configured provider secrets only when config loads.

With the user's agreement, a chat session runs `clutch box issue --class <class> "<title>" --body <file>`. The person opens the printed link, reviews and edits the prefilled form, and submits it. clutch submits nothing. Ticket agents, triage, retro, Author, and harvest never prepare an upstream issue.

The link opens the form only for a GitHub account with access to the repository named in the installed package's Repository URL. Any other account gets GitHub's 404 page.
