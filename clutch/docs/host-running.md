# Running ClutchWork on a host

From the host checkout root, with clutch [installed](host-contract.md#install) and `config.yaml` set up as in the [host contract](host-contract.md), run:

```sh
uv run clutch doctor
uv run clutch serve
```

Use the same prefix for the other verbs below; for example, `clutch install` reports provider CLIs. The host checkout remains the working directory; `--config PATH` before the verb selects a different config. `serve` is the normal mode: it runs until `kill`, `stop`, or Ctrl-C. `drain` is a finite run to quiescence. Closing its terminal, SIGTERM, or Ctrl-C ends it as `kill` does. Serve stops on SIGHUP as it does on Ctrl-C: an unjournaled stop that the next start reconciles. A running serve picks up config edits and new ticket files live. Drafts written by Author wait for `confirm`.

| Verb | Works while serve runs? | What it does |
|---|---|---|
| `watch` | Yes | Show the live text view; `--once` prints one view. |
| `snapshot` | Yes | Print the extension snapshot as JSON. |
| `status` | Yes | Show the journal projection. |
| `stats` | Yes | Show the read-only health and efficiency projection. |
| `lint` | Yes | Validate tickets without writing. |
| `retro` | Yes | Run a retro report now, or queue one on the running engine. |
| `doctor` | No | Inspect setup; its lock probe reports a held lock as a failure. |
| `prompt` | Yes | Render an operator prompt for a ticket, a new ticket stem (`author`), named box IDs, all committed drafts, the drain loop, or the plan-ticket-drain kickoff without writing state. |
| `core` | Yes | Refresh managed conduct files. |
| `probe` | Yes | Probe declared providers and models. |
| `install` | Yes | Install named provider CLIs into the host project as pnpm dev dependencies; with no names, report each adapter's package, location, and version. |
| `init-config` | Yes | Print a suggested `config.yaml` from the provider CLIs found and the models they serve; `--write` creates `config.yaml` when none exists. |
| `update-config` | Yes | List the model names each declared provider serves and say which configured names are current, replaced, or not served; reports names as unverified when the listing is empty with a problem; writes nothing. |
| `help` | Yes | Print a command's help and examples; `clutch --help <command>` does the same. |
| `docs` | Yes | Print the installed host guide paths and their purposes. |
| `migrate-config` | Yes | Validate and migrate an older config. |
| `pause` | Yes | Ask the running engine to pause admission. |
| `resume` | Yes | Ask the running engine to release its current hold. |
| `kill` | Yes | Ask the running engine to stop at a safe point. |
| `stop` | Yes | Finish active work and exit. |
| `review` | Yes | Only the named ticket's pending edits are committed through intake before reviewing the committed ticket. |
| `suggest` | Yes | File an idea into the Suggestion Box. |
| `issue` | Yes | Print a prefilled GitHub new-issue link for a critical clutch bug; submits nothing. |
| `roadmap` | No | Author ready rows with `roadmap author [--ahead N]` and maintain their links. `roadmap merged` checks named stems, a release's rows, or a count of tickets merged since a tag, exits 0 when they hold and 1 otherwise, writes nothing, and works while serve runs. `roadmap status` prints, per release, the rows merged, authored, ready, and blocked and the last gate result, then the next rows to author and the waiting rows. It writes nothing and works while serve runs. When `docs/roadmap.md` exists, `drain` and `serve` run `roadmap author --ahead 2`, the release gate (releasing and, with `release.publish: true`, publishing when it passes), and a `notify` digest at start and after every settle. `roadmap gate <release>` runs the release's gate block from `docs/roadmap.md`, journals the result, exits 0 when every command passes and 1 otherwise, and works while serve runs. `roadmap accept <release>` reviews release promises, appends gap rows in one commit, exits 0 only with no partial or unmet promise, takes no writer lock, and works while serve runs. |
| `triage` | No | Make one pass over named pending box IDs, or all pending messages. |
| `publish` | No | Build the release tagged at HEAD and upload only with `release.publish: true`; never bumps. |
| `release` | No | Bump the version with `--minor` or `--patch`, write a new `CHANGELOG.md` section, commit it with `pyproject.toml` and `uv.lock`, and tag `v<version>`; publishes nothing. |
| `dismiss` | No | Dismiss named box IDs without a model call. |
| `covmap` | Yes | Runs `review.coverage_map.argv` and writes `<state_dir>/coverage-map.json`; exits 0 on success or 2 on refusal. |
| `covgate` | Yes | Run a unit command and check its coverage report. |
| `new` | Yes | Create and lint a ticket skeleton. |
| `order` | Yes | Validate and edit a ticket's priority or runs-before ordering. |
| `run` | No | Intake the named ticket and run it through the pipeline; other pending tickets are left untouched. |
| `confirm` | Yes | Intake the named ticket, then apply or publish a keep verdict after interactive confirmation; other pending tickets are left untouched. |
| `reject` | Yes | Intake the named ticket, then apply or publish a reject verdict after interactive confirmation; other pending tickets are left untouched. |
| `drain` | No | Run eligible tickets to quiescence. `--detach` runs in its own session, surviving terminal or editor closing, and appends output to `<state_dir>/drain.out`. |
| `serve` | No | Run the continuous daemon. |

Stop serve before `roadmap author`, `triage`, `dismiss`, `release`, `publish`, `run`, `drain`, or another `serve`: each takes the writer lock outright and refuses while it is held. `doctor` also needs the lock available to pass its probe. There is one writer per host; the kernel releases its lock when the holder exits. Never delete `clutch.lock`—wait for or stop the holder instead.

## Reporting a critical clutch bug

| Channel | Carries | Ends as |
|---|---|---|
| Suggestion Box (`clutch suggest`) | The host's own work | A host ticket |
| Host bug reports (`report_inbox`) | The host application's bug reports | A `bug_report` box message, then a host bug ticket |
| Upstream issue (`clutch issue`) | A critical clutch bug confirmed by the person | A GitHub issue on the clutch repository |

Critical classes:

- `state-loss`: clutch loses or corrupts committed work, tickets, the journal, or git state.
- `secret-leak`: a configured secret reaches a log, journal, prompt, commit, or a process that should not have it.
- `bad-merge`: clutch merges work that failed a hard gate or review, or changed files outside the fence.
- `engine-stuck`: serve or drain cannot run any ticket on a setup `doctor` passes, and no documented verb releases it.
- `wrong-refusal`: clutch refuses valid config, ticket, or intake with a paved road that cannot be followed.

Name a clutch problem outside these classes to the user in chat; it goes nowhere else. A session never files a clutch defect to the host's Suggestion Box.

The body contains the clutch file and line, gate or spec text or refusal message, and minimum host detail needed to reproduce. Leave out host-private code or data, ticket files, run records, `doctor` output, and host paths. The verb appends a version footer and scrubs configured provider secrets only when config loads.

With the user's agreement, a chat session runs `clutch issue --class <class> "<title>" --body <file>`. The person opens the printed link, reviews and edits the prefilled form, and submits it. clutch submits nothing. Ticket agents, triage, retro, Author, and harvest never prepare an upstream issue.

The link opens the form only for a GitHub account with access to the repository named in the installed package's Repository URL. Any other account gets GitHub's 404 page.
