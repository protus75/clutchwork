Author the clutch ticket `${stem}` at ${ticket} from its request: the roadmap row whose stem is ${stem} when the roadmap has one, else the request given with this prompt. Decisions given with this prompt or recorded in the roadmap override the plans. Other agents may author other tickets in this checkout, and a drain may be running.

Limits:
- Write only under tickets/<your stems>/ and a scratch directory of your own outside the checkout. Never edit code, docs, specs, config, conduct files, or another ticket.
- Run no git verb that writes. Never run `clutch drain`, `clutch run`, `clutch serve`, `clutch confirm`, `clutch reject`, `clutch triage`, `clutch dismiss`, `clutch stop`, or `clutch kill`.
- The review verb commits your ticket through intake; that is the only commit you cause.
- A running drain's intake commits any edited ticket it sees. Edit a copy in your scratch directory and replace the ticket file in one write. Before each write, once every stem in its Depends on has merged, run `clutch status` and stop if the stem is in flight.
- Second problems go to `clutch suggest`, never into the ticket. A cause fix is always filed, never authored.
- If review fails with a provider error, drought, or rate limit (not a verdict), wait about two minutes and retry, up to 3 times.

Procedure:
1. Read the request's owning design and every code and doc location it cites, at HEAD. Search the git log and tickets/ for merged work covering it. If fully covered, create nothing and report skipped with evidence. If partly covered, author only the rest and list what you dropped and why.
2. Run `clutch new ${stem} --kind <kind>` using the row's kind, else the kind the request implies. For a bug, first save real observed output to a file and pass it with --evidence <file>. If new refuses because the ticket exists, stop and report failed with its message. Read the ticket authoring guide whose path it prints (`clutch docs` also names it) in full; it owns every section's content. Then read the skeleton and one recently merged ticket for shape.
3. Fill every section as the guide says. Author the smallest change satisfying the request, and nothing it does not ask for. Fence closure is where tickets fail: apply the guide's ## Scope fence rules to every name, value, verb, path, state, and set member added or changed. Grep tests, docs, source, extension and client code, in-code registries and closed sets included. Read every confirmed, unmerged ticket that fences a file yours fences; in ## Context or the criteria state what either merge order changes so neither breaks. Write test commands as the host's conduct file says. Set Depends on and Runs before as the guide says. Give a realistic time budget. If the request cannot fit one run, split it into at most 3 tickets: keep ${stem} as one and name the others ${stem}-<part>.
4. Run `clutch lint ${stem}` until it exits 0.
5. Make the guide's pre-review checks.
6. Run `clutch review ${stem}`. Repair every finding, re-lint, and re-review until it prints approve. After 6 rounds without approve, stop and report review_stuck with the last findings verbatim.

Report status: approved, skipped, review_stuck, or failed. Per ticket report its stem, kind, priority, review rounds, final fence, Depends on, Runs before, and expected and stuck minutes; what you dropped and why; suggestions filed by id; and anything whoever launched you must know.
