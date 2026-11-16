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
| `prompt` | Yes | Render an operator prompt for a ticket, named box IDs, all committed drafts, or the drain loop without writing state. |
| `core` | Yes | Refresh managed conduct files. |
| `probe` | Yes | Probe declared providers and models. |
| `install` | Yes | Install named provider CLIs into the host project as pnpm dev dependencies; with no names, report each adapter's package, location, and version. |
| `init-config` | Yes | Print a suggested `config.yaml` from the provider CLIs found and the models they serve; `--write` creates `config.yaml` when none exists. |
| `update-config` | Yes | List the model names each declared provider serves and say which configured names are current, replaced, or not served; writes nothing. |
| `docs` | Yes | Print the installed host guide paths and their purposes. |
| `migrate-config` | Yes | Validate and migrate an older config. |
| `pause` | Yes | Ask the running engine to pause admission. |
| `resume` | Yes | Ask the running engine to release its current hold. |
| `kill` | Yes | Ask the running engine to stop at a safe point. |
| `stop` | Yes | Finish active work and exit. |
| `review` | Yes | Only the named ticket's pending edits are committed through intake before reviewing the committed ticket. |
| `suggest` | Yes | File an idea into the Suggestion Box. |
| `triage` | No | Make one pass over named pending box IDs, or all pending messages. |
| `release` | No | Bump the version with `--minor` or `--patch`, commit `pyproject.toml` and `uv.lock`, and tag `v<version>`; publishes nothing. |
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

Stop serve before `triage`, `dismiss`, `release`, `run`, `drain`, or another `serve`: each takes the writer lock outright and refuses while it is held. `doctor` also needs the lock available to pass its probe. There is one writer per host; the kernel releases its lock when the holder exits. Never delete `clutch.lock`—wait for or stop the holder instead.
