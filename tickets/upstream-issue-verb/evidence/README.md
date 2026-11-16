# Upstream issue plan: step 0 hand-test evidence

Plan: `docs/upstream-issue-plan.md`, section "Prerequisite: hand test" (ticket breakdown row 0).
Run by an agent on 2026-11-16 UTC (local 2026-11-15) at HEAD `31327358`, in place of a person, per the owner's decision that no human runs hand tests. Commits landed during the run up to `a7b7329a` were ticket files only.
Everything was read-only. Plain HTTP GETs, `gh api` reads, and a local wheel build and install under the scratchpad. No login, no issue created, nothing remote mutated, and nothing in the repo edited except this directory.

| File | Fact |
|---|---|
| `fact1-url-length.md` | Link length limit: sweeps, the 500/414 edges, the header-sum effect, the login detour, and the chosen limit |
| `fact2-prefill-params.md` | Whether `title`, `body` and `labels` prefill |
| `fact3-project-url-metadata.md` | `Project-URL` from editable, wheel and PyPI installs, plus a side finding |
| `fact4-repo-facts.md` | protus75/clutchwork visibility, issues and templates |
| `raw/` | Probe scripts (`probe.py`, `probe_headers.py`, `probe_edge.py`), every JSONL result row, header captures, and the GitHub docs excerpt |

## Fact 1: link length limit

- The target repo is private, so an anonymous `issues/new` returns 404. The edge was measured on public `octocat/Hello-World` (issues on, no templates). The private repo's URL and a non-redirecting public page hit the same ceiling, so the limit belongs to github.com, not to the repo.
- With curl's minimal headers, a URL up to **6,500 bytes** works every time: 302 to login, with `return_to` equal to the request byte for byte and the login form's hidden `return_to` intact. From about **6,510-6,590 bytes** GitHub returns **500** "Internal server error" (the edge is noisy by about 50 bytes). From 8,020 to 8,191 bytes the HTTP/2 connection resets (HTTP/1.1 gives a 502). **414** first appears at **8,192 bytes**. GitHub's docs promise a 414, but a prefilled link breaks with a 500 about 1.7 KB earlier.
- The ceiling applies to the URL **plus request headers**. With a browser-like header set and a junk cookie, the request fails once URL + cookie reaches about 6,450-6,500 bytes, whatever the split (URL 200 + cookie 6,200 passes, 200 + 6,300 fails; 3,000 + 3,400 passes, 3,000 + 3,500 fails; 6,400 + 0 passes, 6,500 + 0 fails). A signed-in person's GitHub cookies come out of the link's budget. Their size could not be observed without logging in.
- Truncation: when a signed-out person follows the link, GitHub re-encodes it into `login?return_to=` (about 1.39x for prose, up to 1.53x for an all-escape body). The login page 500s from a 6.1-6.9 KB login URL. Once the redirect would reach about 8 KB, GitHub **drops `return_to`** and redirects to a bare `/login`, and the prefill is silently lost. That was the only truncation seen. Below the ceiling nothing was ever truncated.
- `urllib.parse.urlencode` (space -> `+`, which GitHub's docs use) encodes Markdown at about 1.12x, against 1.43x for `quote`.

**Refusal limit: 3,000 bytes for the whole encoded link (`len(url)`).** That is about 46% of the measured 6.5 KB ceiling. It leaves about 400 bytes or more for a signed-in browser (estimated 0.6 KB of browser headers plus up to about 2.5 KB of GitHub cookies) and for the signed-out login detour (link x 1.53 plus headers). With `urlencode` it still carries about 2,400 characters of Markdown body after the base URL, title and footer.

## Fact 2: prefill parameters

- `title`, `body` and `labels` survive the login redirect byte for byte, including brackets, a colon, a newline, backticks and non-ASCII text. They also survive in the login form's hidden `return_to` and in the private repo's 404 "Sign in" link.
- The rendered, filled form needs a signed-in browser and was **not observed**. GitHub's docs ("Creating an issue from a URL query") document `title` and `body` prefill. Those docs plus the intact `return_to` are the evidence under the no-human-hand-test decision.
- The repo has no `.github/` and no issue templates, so the link lands on the blank form, not the chooser.
- **Do not send `labels`.** The docs say the `labels` parameter needs label permission, and that a link using a parameter the person lacks permission for "will return a 404 Not Found error page". A non-triager host operator would get a 404 for the whole link. The `[critical:<class>]` title prefix already sorts the tracker.

## Fact 3: Project-URL metadata

- `importlib.metadata.metadata("clutchwork").get_all("Project-URL")` returns `['Repository, https://github.com/protus75/clutchwork']` in this repo's editable venv and in a non-editable wheel install (built with `uv build --wheel` into the scratchpad, installed into a throwaway Python 3.14 venv; the repo was unchanged). PyPI's published `clutchwork` 0.2.4 carries the same `project_urls`.
- `metadata("clutch")` and `version("clutch")`, as the plan writes them, raise `PackageNotFoundError` in both installs. Use `"clutchwork"`, and reuse the reader in `clutch/observe.py::help_payload`.
- Side finding, not filed: `README.md:14` and `clutch/docs/host-contract.md:10` tell hosts to run `uv add --dev clutch`. On PyPI, `clutch` is an unrelated "Python Web Framework for GAE" (0.1a2), and `uv pip compile` resolves `clutch` to `clutch==0.1a2`. A host following the install docs never gets clutchwork.

## Fact 4: repo facts

- `gh api repos/protus75/clutchwork` (authenticated as the owner): `has_issues: true`, `open_issues_count: 0`, **`private: true`, `visibility: private`**, no `.github/`, `issue_template: null`, license "Other" (proprietary).
- An anonymous visitor gets 404 for the repo, its issues and `issues/new`. Only accounts with repo access can open a printed link. A host operator who is not a collaborator gets a 404 page. This contradicts the plan's Privacy premise ("The issue tracker is public"), even though the public PyPI release points its Repository URL at this repo. Making the repo public, or pointing the URL elsewhere, is an owner decision that blocks the verb being useful to other hosts.

## What the `upstream-issue-verb` ticket should carry from this

1. Refuse when `len(url) > 3000`, naming the actual and maximum lengths. Build the query with `urllib.parse.urlencode({"title": ..., "body": ...})`.
2. Send only `title` and `body`. Never send `labels`.
3. Read `metadata("clutchwork")` and `version("clutchwork")`, reusing `clutch/observe.py::help_payload`'s Repository read.
4. Before authoring, the owner must decide the private-repo question (fact 4). The plan's Privacy section must be corrected either way.
