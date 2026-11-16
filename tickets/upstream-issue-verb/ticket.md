---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
- none

## Context
- tickets/upstream-issue-verb/evidence/README.md
- docs/upstream-issue-plan.md#Not the Suggestion Box
- clutch/__main__.py::_parser
- clutch/__main__.py::main
- clutch/observe.py::help_payload
- clutch/redact.py::Redactor
- clutch/config.py::load_config
- clutch/runner.py::Refusal
- clutch/hostfiles.py::CORE_TEMPLATE
- clutch/docs/host-running.md
- docs/how-clutch-works.md#2.1
- docs/how-clutch-works.md#12.
- tests/unit/test_docs_verb.py::test_docs_without_config_or_lock
- tests/unit/test_host_running.py
- tests/unit/test_readme.py::test_clutch_verbs_exist
- tests/integration/test_hostfiles.py::test_core_golden_uses_branch_template
- tests/integration/test_hostfiles.py::test_core_activation_first_adoption
- tests/integration/test_fixture_host.py::test_fixture_profile_loads
- tests/integration/test_cli.py::CONFIG

## Goal / Why
A host session that finds a bug in clutch itself has no way to report it. The `CORE_TEMPLATE` Diagnosis rule in `clutch/hostfiles.py` says a fix that belongs in clutch "is never copied or patched into host files. Report it for the owner to carry to clutch, then stop." It names no channel, so the session can only describe the problem in chat and hope the operator relays it. `docs/upstream-issue-plan.md` (roadmap row 34, release 0.2.0) adds that channel for critical bugs only: a `clutch issue` verb that prints a prefilled GitHub new-issue link, which a person opens, reviews, and submits. The verb submits nothing, holds no token, needs no `gh`, and mutates nothing remote, so the "never run a remote-mutating verb unless the user says push" rule is untouched. The three channels stay apart: the Suggestion Box carries a host's own work, `report_inbox` carries the host application's bug reports, and only a critical clutch bug goes upstream. The critical classes are the closed set the owner settled in `docs/roadmap.md` section 6 decision 10: `state-loss`, `secret-leak`, `bad-merge`, `engine-stuck`, and `wrong-refusal`.

An agent ran the plan's hand test, and its capture is committed as this ticket's evidence under `tickets/upstream-issue-verb/evidence/` (summary in `README.md`). Where the capture differs from the plan, the capture wins:
1. Length limit (`fact1-url-length.md`). GitHub returns a 500 page once the URL plus request headers pass about 6.5 KB, and returns a 414 only at 8,192 bytes. A signed-in browser's cookies, and the signed-out login detour (about 1.4 to 1.5 times the link), come out of that budget. So the verb refuses a link longer than 3,000 bytes (`len(url) > 3000`). `urllib.parse.urlencode` (a space becomes `+`) encodes Markdown at about 1.12 times its length, against 1.43 for `quote`, so the query is built with `urlencode`.
2. Parameters (`fact2-prefill-params.md`). `title` and `body` pass through GitHub's redirects intact, and GitHub documents them as prefilling the form. `labels` needs label permission, and GitHub documents a 404 for a whole link that uses a parameter the person lacks permission for. So the verb sends only `title` and `body`. The `[critical:<class>]` title prefix does the sorting.
3. Metadata (`fact3-project-url-metadata.md`). The distribution is `clutchwork`. The plan's `metadata("clutch")` and `version("clutch")` raise `PackageNotFoundError` in both editable and wheel installs. The repository URL comes from the read that `clutch/observe.py::help_payload` already does, moved into a function both callers use, so a fork's install files to the fork. The version comes from `version("clutchwork")`.
4. Access (`fact4-repo-facts.md`). protus75/clutchwork is private with issues enabled, so the plan's Privacy premise ("The issue tracker is public") is false today. The verb's design does not change for this. Its docs say the link opens the form only for a GitHub account with access to the repository named in the installed package's Repository URL. Whether to make that repository public is the owner's decision, outside this ticket.

When this ticket is done:
- `clutch issue --class <class> "<title>" --body FILE` prints one line: `<Repository URL>/issues/new?` followed by the `urlencode`d `title` (`[critical:<class>] <title>`) and `body` (the file's text plus a footer naming the clutchwork version, the Python version, and the OS). Configured provider secrets are scrubbed from both before encoding. When the config does not load, nothing is scrubbed, and one stderr line says so.
- It refuses (exit 2, with a paved road) a missing or unknown class, an unreadable or empty body file, and a link over 3,000 bytes. It runs before config loads, takes no lock, writes nothing, and works while serve runs.
- Every host's managed block tells sessions to name a clutch defect to the user in one line, never to file it to the host's Suggestion Box, and to use `clutch issue` only for a critical class, with the user's agreement.
- The run guide, `docs/how-clutch-works.md`, and `README.md` describe the verb, the channels, the classes, and the access limit.

Rule home: the changed rule is for every host's sessions, so its home is `CORE_TEMPLATE` in `clutch/hostfiles.py`. It reaches this repo's `CLAUDE.md` and `AGENTS.md` and `hosts/fixture/CLAUDE.md` through `clutch core`. No rule outside a managed block changes. The bullet opens with "Outside clutch's own repo" because this repo is its own first host. Here a clutch defect is an ordinary ticket or Suggestion Box message, and an upstream issue filed against itself would be wrong. The plan left that conflict unaddressed (`.claude/roadmap-docs-digest.json`, upstream entry).

Byte budget: at HEAD `CORE_TEMPLATE` is 7,817 bytes, after `conduct-files-parity` freed 38. The new bullet is 292 bytes longer than the one it replaces, which brings the template to 8,109 of the 8,192-byte cap in `tests/integration/test_hostfiles.py::test_core_template_order_and_budget`. That leaves 83 bytes spare, so `graphics-kind`'s planned 9 bytes still fit.

## Scope in / Scope out
Scope in:
- New `clutch/issue.py`:
  - `CLASSES = ("state-loss", "secret-leak", "bad-merge", "engine-stuck", "wrong-refusal")`, the code's one home for the class set, and `MAX_LINK_BYTES = 3000`.
  - `version` is imported at module level (`from importlib.metadata import version`), so a unit test replaces `clutch.issue.version`.
  - `link(issue_class: str | None, title: str, body: str, scrub: Callable[[str], str]) -> str` runs these steps in order:
    1. When `issue_class` is not in `CLASSES` (including `None`), raise `runner.Refusal`. Its message names `--class` and lists the five classes. Its road is exactly `only critical bugs are filed upstream; name a non-critical clutch problem to the user in chat instead`.
    2. When `body.strip()` is empty, raise `runner.Refusal`. Its message says the `--body` file is empty, and its road is `write the clutch file, the defect, and minimal evidence into the --body file`.
    3. Build the title text `f"[critical:{issue_class}] {title}"`. Build the body text as `body.rstrip()` followed by `"\n\n---\nclutchwork " + version("clutchwork") + ", Python " + platform.python_version() + ", " + platform.system() + "\nFiled with clutch issue"`.
    4. Pass both texts through `scrub` before encoding. The URL is `observe.repository_url() + "/issues/new?" + urlencode({"title": <scrubbed title>, "body": <scrubbed body>})`, with no other query parameter.
    5. When `len(url) > MAX_LINK_BYTES`, raise `runner.Refusal` with message `link is <n> bytes, over the 3000-byte limit` and road `shorten the body; quote only the lines that show the defect`.
    6. Return the URL.
- `clutch/observe.py`: add `repository_url() -> str`, which returns the URL part of the `Repository, ` entry in `metadata("clutchwork").get_all("Project-URL")`. This is the expression `help_payload` uses today, moved. `help_payload` calls it. Nothing else in the file changes. This is the only `Project-URL` read in the `clutch` package.
- `clutch/__main__.py`:
  - `_parser`: an `issue` subparser with help `print a prefilled GitHub new-issue link for a critical clutch bug`. It takes `--class` (`dest="issue_class"`, default `None`), a positional `title`, and `--body` (`type=Path`, `required=True`). `--class` has no `choices`, because argparse's own invalid-choice error carries no paved road. Its help text lists the five classes, joined from `clutch.issue.CLASSES`.
  - `main`: an `issue` branch placed before `config = load_config(args.config, cwd=repo)`, beside `docs`, `init-config`, `install`, `new` and `doctor`. It does these steps in order:
    1. Read `repo / args.body` as UTF-8 text. On `OSError` or `UnicodeDecodeError`, raise `runner.Refusal` with message `cannot read --body file <path>: <error>` and road `pass the path of a UTF-8 Markdown file`.
    2. Build `Redactor.from_config(load_config(args.config, cwd=repo), env)`. On `ConfigError`, print one stderr line `issue: config did not load, so no secrets were scrubbed: <error>` and use `Redactor({})`.
    3. Print `issue.link(args.issue_class, args.title, body, redactor.scrub)` as the only stdout line, and return 0.
    Refusals go through `main`'s existing handler (exit 2, `clutch issue: <message> -- <road>`), and nothing is added to that handler. The branch takes no lock, builds no checkout, and writes no file, journal event, or git state.
- `clutch/hostfiles.py`, `CORE_TEMPLATE`: in the Diagnosis section, replace exactly this bullet:
  `- HARD: A fix that belongs in clutch (a prompt spec, gate, ticket format, host guide, or this block) is never copied or patched into host files. Report it for the owner to carry to clutch, then stop. Why: a host copy competes with clutch's rule, reaches no other host, and goes stale on upgrade.`
  with exactly this bullet:
  ``- HARD: Outside clutch's own repo, a fix that belongs in clutch (a prompt spec, gate, ticket format, host guide, or this block) is never copied or patched into host files nor filed to the Suggestion Box; name it to the user in one line. Only a bug in a `clutch issue` critical class goes upstream: draft a body file (clutch file, defect, minimal evidence, no host-private code or data), and with the user's agreement run `clutch issue` and give them the link to review and submit; then stop. Why: a host copy competes with clutch's rule, reaches no other host, and goes stale on upgrade.``
  No other byte of the template changes. The pinned phrase `is never copied or patched into host files` stays verbatim.
- Refresh the managed blocks from the edited template with the `core` verb, as `conduct-files-parity` did. Run `uv run clutch core` at the repo root, which rewrites `CLAUDE.md` and `AGENTS.md`. Then run `uv run clutch core` again with `hosts/fixture` as the working directory, which rewrites `hosts/fixture/CLAUDE.md`. Never hand-edit a managed block.
- `tests/integration/test_hostfiles.py`: regenerate `GOLDEN` with the module's own `if __name__ == "__main__":` block (`uv run python -m tests.integration.test_hostfiles`). No other line of the file changes.
- `clutch/docs/host-running.md`, two edits:
  1. Add a verb-table row for `issue` (Works while serve runs: Yes) directly after the `suggest` row. It says the verb prints a prefilled GitHub new-issue link for a critical clutch bug and submits nothing.
  2. Add a new section `## Reporting a critical clutch bug` at the end of the file. It holds:
     - A three-row channel table. Suggestion Box (`clutch suggest`) carries the host's own work and ends as a ticket in the host. Host bug reports (`report_inbox`) carry the host application's bug reports and end as a `bug_report` box message, then a host bug ticket. Upstream issue (`clutch issue`) carries a critical clutch bug the person confirms and ends as a GitHub issue on the clutch repository. `tests/unit/test_host_running.py` reads every line that starts with `` | ` `` as a verb row, so no new line in this file other than the `issue` verb row may start that way. Begin each first cell with plain words.
     - The five classes as a bulleted list, with the meanings from the plan's "Critical classes" table. A clutch problem that fits none of them is named to the user in chat and goes nowhere else. A session never files a clutch defect to the host's Suggestion Box.
     - What the body holds: the clutch file and line, the gate or spec text or the refusal message, and the minimum host detail needed to reproduce. What it leaves out: host-private code or data, ticket files, run records, `doctor` output, and host paths. The verb appends the version footer, and it scrubs configured provider secrets only when the config loads.
     - The review-then-submit step. With the user's agreement, a chat session runs `clutch issue --class <class> "<title>" --body <file>`. The person opens the printed link, reviews and edits the prefilled form, and submits it. clutch submits nothing. Ticket agents, triage, retro, Author, and harvest never prepare an upstream issue.
     - Access. The link opens the form only for a GitHub account with access to the repository named in the installed package's Repository URL. Any other account gets GitHub's 404 page.
- `docs/how-clutch-works.md`, two edits:
  - Section 2.1: one verb-table row `` `issue --class <class> <title> --body FILE` ``, Lock `no`, directly after the `suggest <summary>` row. It describes the printed link (`title` and `body` only, the version footer, the Repository URL from package metadata, and secrets scrubbed when config loads). It names the refusals (unknown or missing class, unreadable or empty body, a link over 3,000 bytes). It says the verb takes no lock, writes nothing, opens no browser, and submits nothing.
  - Section 12: one bullet appended to the section's bullet list. It says a clutch defect found in a host is named to the user in chat and never filed to the host's Suggestion Box. It says only a bug in one of `clutch issue`'s critical classes goes upstream, as the link that verb prints for a person to review and submit, and it points to the run guide's "Reporting a critical clutch bug" section.
  No other part of the file changes.
- `README.md`: one line in the `## Commands` block, directly after the `uv run clutch suggest` line: `uv run clutch issue    # link to report a critical clutch bug upstream`.
- New tests:
  - `tests/unit/test_issue_link.py` uses fakes and touches disk only under `tmp_path`. It replaces `clutch.observe.metadata` and `clutch.issue.version`, so it never reads the installed metadata.
  - `tests/integration/test_issue_verb.py` uses the real installed metadata and the real config loader. It may import `CONFIG` from `tests/integration/test_cli.py`, which stays unchanged.

Scope out:
- Submitting an issue, `gh`, the GitHub API, a token, opening a browser, a `--json` mode, a `labels` parameter, and any config key, flag, or env var for the limit or the classes.
- The VS Code extension and `clutch/help.py`: `issue` is not an extension surface. `dev.py`.
- `docs/upstream-issue-plan.md` (its Privacy section and its `"clutch"` metadata name are stale; the evidence records the facts), `docs/roadmap.md`, and `CLUTCH_PLAN.md`.
- `docs/how-clutch-works.md` sections 8.5 and 9.3. The section 9.3 "carry to clutch" decline stays a decision record in the host, as the plan says.
- The `uv add --dev clutch` install line in `README.md` and `clutch/docs/host-contract.md`: ticket `install-docs-name-clutchwork` owns it.
- Making protus75/clutchwork public, or pointing the Repository URL elsewhere: the owner's decision.
- `clutch/redact.py` and its writer-site checklist: the issue body is text a person writes, not a captured stream.
- `tests/integration/test_cli.py`, `tests/unit/test_host_running.py`, `tests/unit/test_readme.py`, and `tests/unit/test_hostfiles.py`: none is edited, and no test is added to them.

## Scope fence
- clutch/issue.py
- clutch/__main__.py
- clutch/observe.py
- clutch/hostfiles.py
- CLAUDE.md
- AGENTS.md
- hosts/fixture/CLAUDE.md
- clutch/docs/host-running.md
- docs/how-clutch-works.md
- README.md
- tests/unit/test_issue_link.py
- tests/integration/test_issue_verb.py
- tests/integration/test_hostfiles.py

## Acceptance criteria
1. `tests/unit/test_issue_link.py::test_link_prefills_only_title_and_body` sets up two fakes. `clutch.observe.metadata` becomes a recorder whose result's `get_all("Project-URL")` returns `["Homepage, https://example.com", "Repository, https://github.com/fork/clutchwork"]`. `clutch.issue.version` becomes a recorder returning `9.9.9`. The test then asserts that ``link("state-loss", "journal lost", "Steps:\n1. run `clutch drain`\n\n", lambda text: text)`` returns exactly ``"https://github.com/fork/clutchwork/issues/new?" + urlencode({"title": "[critical:state-loss] journal lost", "body": "Steps:\n1. run `clutch drain`\n\n---\nclutchwork 9.9.9, Python " + platform.python_version() + ", " + platform.system() + "\nFiled with clutch issue"})``. It also asserts that `parse_qs` of the URL's query has exactly the keys `title` and `body`, and that both recorders were called with `"clutchwork"`. Ruled out: a `labels` or any other parameter; `quote` encoding (`%20` for a space); a hard-coded repository URL (the fork's URL must appear); the Homepage entry; `metadata("clutch")` or `version("clutch")`; and a missing title prefix or footer.
2. `tests/unit/test_issue_link.py::test_classes_are_closed` asserts `CLASSES == ("state-loss", "secret-leak", "bad-merge", "engine-stuck", "wrong-refusal")`. It also asserts that `link("minor-annoyance", ...)` and `link(None, ...)` each raise `runner.Refusal` whose text contains all five class names and `only critical bugs are filed upstream; name a non-critical clutch problem to the user in chat instead`. Ruled out: a sixth or missing class, and a link built for a non-critical or missing class.
3. `tests/unit/test_issue_link.py::test_empty_body_refuses` asserts that a body of `""` and a body of `" \n\t"` each raise `runner.Refusal` whose text contains `empty`. Ruled out: a link whose body is only the footer.
4. `tests/unit/test_issue_link.py::test_link_length_limit` uses the fakes from criterion 1. A body of `a` characters sized so the link is exactly 3,000 bytes returns the link. One more `a` raises `runner.Refusal` whose text contains `3001`, `3000`, and `shorten the body; quote only the lines that show the defect`. Ruled out: any other limit, `>=` in place of `>`, and a limit on the body length instead of the whole link.
5. `tests/unit/test_issue_link.py::test_secrets_scrubbed_before_encoding` passes `Redactor({"TOKEN": "s3cr3t value"}).scrub`, with `s3cr3t value` in both the title and the body. It asserts that the decoded `title` and `body` each contain `[REDACTED:TOKEN]`, and that the URL does not contain `s3cr3t`. Ruled out: scrubbing the encoded URL, where `s3cr3t+value` would survive, and scrubbing only the body.
6. `tests/unit/test_issue_link.py::test_main_prints_link_without_lock_or_writes` writes `body.md` (containing `s3cr3t`) under `tmp_path`. It sets `cli.load_config` to a recorder returning `SimpleNamespace(providers=[SimpleNamespace(auth="TOKEN")])`, replaces `cli.Lockfile` and `cli.LocalFileSystem` with mocks that raise `AssertionError`, and uses the fakes from criterion 1. It asserts that `cli.main(["issue", "--class", "bad-merge", "merged a red gate", "--body", "body.md"], cwd=tmp_path, env={"TOKEN": "s3cr3t"})` returns 0 and that stdout is exactly one line, which starts `https://github.com/fork/clutchwork/issues/new?`. That line's decoded `body` contains `[REDACTED:TOKEN]` and not `s3cr3t`, stderr is empty, and `load_config` was called with `cwd=tmp_path`. Ruled out: a lock, a file write, a printed secret, and any extra stdout.
7. `tests/unit/test_issue_link.py::test_main_unscrubbed_when_config_fails` repeats criterion 6, except that `cli.load_config` raises `ConfigError(tmp_path / "config.yaml", None, "config file not found; create config.yaml at the checkout root or pass --config <path>")`. It asserts that `main` returns 0 and prints the link, whose decoded `body` contains `s3cr3t`. It also asserts that stderr is exactly one line containing both `no secrets were scrubbed` and `config file not found`. Ruled out: refusing when config is absent, and skipping the scrub without saying so.
8. `tests/unit/test_issue_link.py::test_main_refusals` runs `cli.main` with the fakes from criterion 1 and `cli.load_config` raising `ConfigError`. In each of these cases `main` returns 2, stdout is empty, and stderr has a line starting `clutch issue:`:
   - a `--body` path that does not exist, where stderr names that path;
   - a body file holding the bytes `b"\xff\xfe"`;
   - `--class minor-annoyance`;
   - `--class` omitted;
   - an empty body file;
   - a body file whose link would exceed 3,000 bytes.
   The test also asserts that `["issue", "--class", "state-loss", "t"]`, which has no `--body`, raises `SystemExit` with code 2. Ruled out: a traceback for an unreadable body, and a link printed for a missing class.
9. `tests/unit/test_issue_link.py::test_help_lists_classes` asserts that `cli._parser().parse_args(["issue", "--help"])` raises `SystemExit` with code 0. With all whitespace removed from the captured stdout (argparse may wrap at a hyphen), it contains each of the five class names. Ruled out: help that omits the classes.
10. `tests/integration/test_issue_verb.py::test_link_from_installed_metadata` writes `body.md` in a `tmp_path` that has no `config.yaml`. It asserts that `main(["issue", "--class", "engine-stuck", "drain idles", "--body", "body.md"], cwd=tmp_path, env={})` returns 0. The printed link starts with the URL part of the `Repository, ` entry of `importlib.metadata.metadata("clutchwork").get_all("Project-URL")`, followed by `/issues/new?title=%5Bcritical%3Aengine-stuck%5D+drain+idles&body=`. The decoded `body` ends with `"clutchwork " + importlib.metadata.version("clutchwork") + ", Python " + platform.python_version() + ", " + platform.system() + "\nFiled with clutch issue"`. Stderr contains `no secrets were scrubbed`. Ruled out: `PackageNotFoundError` from the name `clutch`, and a URL or version that differs from the installed metadata.
11. `tests/integration/test_issue_verb.py::test_link_scrubs_configured_secret` writes `config.yaml` to `tmp_path` as `CONFIG`, with `kind: cli` replaced by `kind: cli\n    auth: CLUTCH_ISSUE_KEY`, and a `body.md` containing `sk-issue-secret`. It runs `main` as in criterion 10 with `env={"CLUTCH_ISSUE_KEY": "sk-issue-secret"}`. It asserts that `main` returns 0, stdout does not contain `sk-issue-secret`, the decoded `body` contains `[REDACTED:CLUTCH_ISSUE_KEY]`, and stderr is empty. Ruled out: a scrub that ignores the loaded config, and an unscrubbed link when config loads.
12. The unit check passes. That is `clutch covgate` over `tests/unit`, the `unit` entry of `config.yaml` `review.mechanical`. Measured from `tests/unit/test_issue_link.py` among the rest of `tests/unit`, `clutch/issue.py` is at or above `test-gate.toml`'s `default = 90` and `clutch/__main__.py` is at or above its floor of 13.
13. The first `uv run python -c` command in `## Verification` exits 0. It checks that `CORE_TEMPLATE` contains the new bullet from `## Scope in / Scope out` byte for byte and no longer contains `Report it for the owner to carry to clutch`. Ruled out: the old tail kept, and the plan's unscoped wording without "Outside clutch's own repo".
14. `./dev.py test tests/integration/test_hostfiles.py tests/integration/test_fixture_host.py` exits 0.
    - `test_core_golden_uses_branch_template` fails if `GOLDEN` was not regenerated.
    - `test_core_activation_first_adoption` fails if the `CLAUDE.md` or `AGENTS.md` managed block is stale or hand-edited.
    - `test_core_template_order_and_budget` fails if the template exceeds 8,192 bytes.
    - `test_core_template_is_host_neutral` fails if the pinned phrase changed.
    - `test_fixture_profile_loads` fails if `hosts/fixture/CLAUDE.md` was not refreshed.
15. The `core_drift` gate passes at Check: the committed `CLAUDE.md` and `AGENTS.md` classify `current` against the branch's `CORE_TEMPLATE`.
16. The second `uv run python -c` command in `## Verification` exits 0. It checks four things:
    - `clutch/docs/host-running.md` has a `## Reporting a critical clutch bug` section that names all five classes, `clutch suggest`, `report_inbox`, `clutch issue`, `Repository URL`, and `404`.
    - The `docs/how-clutch-works.md` section 2.1 verb table has a row starting `` | `issue --class ``.
    - Section 12 of `docs/how-clutch-works.md` names `clutch issue`.
    - `README.md` contains `uv run clutch issue`.
    `./dev.py test tests/unit/test_host_running.py tests/unit/test_readme.py` exits 0. That proves the `issue` row exists and that no class or channel line in the new section is read as a verb row.
17. The third `uv run python -c` command in `## Verification` exits 0. It checks that exactly one file under `clutch/` mentions `Project-URL`, that `clutch/issue.py` mentions neither `Project-URL` nor `metadata(`, and that `clutch/observe.py` defines `def repository_url(`. Ruled out: a second Repository-URL reader.
18. `./dev.py test` exits 0.

## Verification
```
./dev.py test tests/unit/test_issue_link.py tests/unit/test_host_running.py tests/unit/test_readme.py
./dev.py test tests/integration/test_issue_verb.py tests/integration/test_hostfiles.py tests/integration/test_fixture_host.py
uv run python -c "from clutch.hostfiles import CORE_TEMPLATE as t; new = b'- HARD: Outside clutch^s own repo, a fix that belongs in clutch (a prompt spec, gate, ticket format, host guide, or this block) is never copied or patched into host files nor filed to the Suggestion Box; name it to the user in one line. Only a bug in a ~clutch issue~ critical class goes upstream: draft a body file (clutch file, defect, minimal evidence, no host-private code or data), and with the user^s agreement run ~clutch issue~ and give them the link to review and submit; then stop. Why: a host copy competes with clutch^s rule, reaches no other host, and goes stale on upgrade.'.replace(b'~', bytes([96])).replace(b'^', bytes([39])); assert new in t; assert b'Report it for the owner to carry to clutch' not in t"
uv run python -c "import pathlib; h = pathlib.Path('clutch/docs/host-running.md').read_text(); s = h.split('## Reporting a critical clutch bug', 1)[1]; assert all(w in s for w in ('state-loss', 'secret-leak', 'bad-merge', 'engine-stuck', 'wrong-refusal', 'clutch suggest', 'report_inbox', 'clutch issue', 'Repository URL', '404')); w = pathlib.Path('docs/how-clutch-works.md').read_text(); v = w.split('### 2.1 Verbs', 1)[1].split('### 2.2', 1)[0]; assert '| ' + chr(96) + 'issue --class' in v; assert 'clutch issue' in w.split('## 12. Host projects', 1)[1].split('## 13.', 1)[0]; assert 'uv run clutch issue' in pathlib.Path('README.md').read_text()"
uv run python -c "import pathlib; hits = [p for p in pathlib.Path('clutch').rglob('*.py') if 'Project-URL' in p.read_text()]; assert hits == [pathlib.Path('clutch/observe.py')], hits; i = pathlib.Path('clutch/issue.py').read_text(); assert 'Project-URL' not in i and 'metadata(' not in i; assert 'def repository_url(' in pathlib.Path('clutch/observe.py').read_text()"
./dev.py test
```

## Definition of rejected
The branch is rejected if any of these happens:
- The link carries any query parameter other than `title` and `body`.
- The verb opens a browser, starts a process, makes a network call, submits an issue, reads a token, or calls `gh`.
- The verb takes a lock or writes any file, journal event, or git state.
- The repository URL is hard-coded, or `Project-URL` is read anywhere but `clutch/observe.py::repository_url`.
- A metadata call names the distribution `clutch`.
- It adds a config key, flag, or env var for the limit or the classes, a `--json` mode, a `dev.py` subcommand, an extension command, or a `clutch/help.py` entry.
- `CORE_TEMPLATE` changes by anything other than the one bullet replacement, or a managed block is hand-edited or is not byte-equal to `hostfiles.render` of the branch's template.
- A test is added to `tests/integration/test_cli.py`, or any existing test other than `GOLDEN` in `tests/integration/test_hostfiles.py` is edited.

## Time budget
- expected: 60m
- stuck: 150m
