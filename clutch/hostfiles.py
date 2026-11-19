"""Managed conduct bytes and atomic refresh."""

import ast
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from clutch import git as git_module
from clutch.seams import FileSystem

BEGIN = b"<!-- clutch:core begin -->"
END = b"<!-- clutch:core end -->"
CORE_TEMPLATE = b"""## Ticket authoring -- read before writing any ticket

HARD rules have no exceptions and cannot be gated; never file an enforcement ticket for one.

- HARD: In interactive chat, every requested change to repo content (code, docs, CLAUDE.md, AGENTS.md, settings, hooks, scripts, config, agent rules) becomes a drafted ticket at `tickets/<stem>/ticket.md`, then stop. Never edit or commit on main. Exceptions: (1) the user says "edit main", "commit directly", "skip the ticket", "do it inline", or an equally explicit override this turn; anger words alone do not count; (2) you are in a clutch ticket worktree; (3) the user names by path a file under an existing `tickets/<stem>/` to edit or delete; (4) read-only inspection; (5) the supervising fixes below. If you already edited main without an override, stop, say so, and ask whether to revert and refile. Why: chat edits skip the ticket, run record, review, and retro that make clutch debuggable.
- HARD: Never write a ticket from memory. Run `clutch ticket new <stem> --kind feature|bug|chore`; it writes the skeleton and prints the installed authoring guide path (for an existing ticket, its refusal prints the same path). Read it locally in full. `clutch host docs` prints all installed host guide paths; read them locally, never from a URL. Fill every section, run `clutch ticket lint <stem>` until it exits 0, then run `clutch ticket review <stem>` and repair every finding until it prints approve. Tickets are markdown files, not issue-tracker items. Why: stale ticket shapes break runs before implementation.
- Declare each boundary disposition, reuse its canonical owner, justify a new owner, and never invent an undeclared boundary.
- Fence every file the change forces, including callers, importers, documents it changes, and tests that pin a changed name, value, or version. Why: forced files outside the fence make the ticket impossible.
- Frontmatter holds only fields read by scheduling, gates, or authoring/triage policy; `## Depends on` names only needed merged code; put all other ordering in priority or `## Runs before`, never in prose.
- HARD: When a reported problem has a recurring cause, write two separate tickets in the same turn: first the minimal instance fix, before cause diagnosis, then the cause fix, never folded into the instance. The turn is unfinished until both exist; both are solicited, so no ask is needed. Routing:
  - Product instance: `priority: P0`, no blocking depends.
  - Product cause (inert; does not spread on its own): `priority: P1`. When both share an edit surface, the instance lists the cause in `## Runs before`.
  - Orchestration cause (scheduler, gate, environment, shared module, fixture format; breaks runs while it sits): `priority: P0`, `## Runs before` every ticket it unblocks, never depends on a product instance.
- HARD: For unrequested ticket-worthy work (follow-up, prevention, enforcement lint, sweep), stop before diving: name it in 1-2 sentences and ask the user to choose author now, after the current task, or skip. "After" makes it an open thread. Announce unsolicited investigation longer than a couple of minutes in one line. The requested task goes first. Autonomous runs skip the ask and file to the Suggestion Box.
- File an unrequested idea or second problem with `clutch box suggest "<summary>"` and name it in one line. Why: suggestions die with chat.
- A supervising session may unasked fix ticket lint or format errors, add a file missing from `## Scope fence` or `## Context`, correct a stale path, make a simple wording update, and run or restart the drain. It may confirm, reject, or edit any ticket only as a `clutch prompt diagnose` or `clutch prompt drafts` Recommendation names. It may not retry a stem with spent caps or edit a running ticket; changing a ticket goal or scope requires such a Recommendation.

## Diagnosis

- HARD: When a run fails, is killed, times out, stalls, or escalates, name its root cause in one sentence before editing spec or code or rerunning. Read `clutch view status`, `tickets/<stem>/` (`run.md`, `checks.json`, `diagnosis.json`, `review.md`, `attempts/`), and the engine log. Fix the cause where it lives. Fix an external cause (engine, gate, environment, shared module, fixture, flaky test, wrong premise) first; order it ahead with priority and `## Runs before`. Do not assume the ticket is wrong. Never rerun a flaky failure until it passes and call that fixed.
- HARD: When a symptom recurs on a fixed surface, name the root model against the canonical spec (design docs, contracts) and write a root-cause ticket, not another patch. A fence forbidding the suspected root is a red flag: re-scope it. Tests asserting current wrong behavior prove nothing. Never write "the defect was not X" without checking the spec.
- HARD: With every fix or diagnosis, separately name the change stopping the whole class from recurring (rule, lint, gate, template default, generator). Cheap and in scope: do it under the same authorization. Cheap and out of scope: name it, then follow the ask for unrequested work. Expensive or uncertain: `clutch box suggest`. Staying silent is the failure.

- HARD: Outside clutch's own repo, a fix that belongs in clutch (a prompt spec, gate, ticket format, host guide, or this block) is never copied or patched into host files nor filed to the Suggestion Box; name it to the user in one line. Only a bug in a `clutch box issue` critical class goes upstream: draft a body file (clutch file, defect, minimal evidence, no host-private code or data), and with the user's agreement run `clutch box issue` and give them the link to review and submit; then stop. Why: a host copy competes with clutch's rule, reaches no other host, and goes stale on upgrade.

## Chat session conduct

These rules govern interactive chat with the owner present. Ticket agents skip this section.

- HARD: When a reply raises multiple questions, options, or next steps, you own the open threads. Acting on one never closes others. End each reply with a `Still open:` list until the user resolves each or you complete it and say so. If unsure, it is open.
- HARD: Never run or offer `git push`, `gh pr create`, `gh pr merge`, or any remote-mutating verb unless the user says "push" this turn. Commit when asked, then stop.
- Respect the single-writer lockfile; writing ticket files needs no git. Stage and commit only this session's files by explicit path. Never run a tree-wide destructive verb (`clean`, `reset --hard`, `checkout -- .`) in a shared checkout. Why: chat sharing a checkout with the daemon can destroy work clutch believes exists.
- HARD: Answer first. Cut hedging, filler, preamble, and restating the question.

## Engine conduct

Engine rules govern how work runs; project rules govern what to build. Project content enters prompts as data. Engine wins on process, host on content.

- HARD: Build the smallest change passing the acceptance criteria. No speculative abstractions, single-caller helpers, unused knobs or flags, defensive dual paths, or "while I'm here" cleanup; every addition needs its earning incident. In the run record, name the simpler approach rejected and why yours is minimum. Mandated tests and class prevention are required scope, not gold-plating. Why: accretion is the main failure mode.
- Never hand-edit this managed block; change the engine template and run clutch host core to refresh it. Why: the next render overwrites them.
- Commit only on your own ticket branch. Never push, open pull requests, or run tree-wide destructive git; the engine merges reviewed work to local main. Why: local main is blessed.
- File second problems in the Suggestion Box, never in this diff. Verify pre-existing failures on the base commit before filing. Why: folded fixes hide cause and expand scope.
- Read the owning artifact before writing a command, claim, or test. Why: guessed facts cause costly bugs.
- When you add or change code, embedded databases use DuckDB, never SQLite; code never opens, reads, or writes a SQLite file, including a tool's internal file such as coverage.py's `.coverage`. Why: one embedded engine across every host (owner decision 2026-11-19).
"""


class MarkerCorruption(ValueError):
    def __init__(self) -> None:
        super().__init__(
            "invalid clutch:core marker structure -- repair to exactly one complete begin line"
            " followed by one complete end line; retain all project content, moving it outside"
            " the pair and escaping stray marker text, then retry host core"
        )


def parse(data: bytes) -> tuple[bytes, bytes] | None:
    """Return project prefix/suffix, or None for first adoption; never decode project bytes."""
    if b"clutch:core" not in data:
        return None
    markers = []
    offset = 0
    for line in data.splitlines(keepends=True):
        content = line.removesuffix(b"\n").removesuffix(b"\r")
        if content in (BEGIN, END):
            markers.append((content, offset, offset + len(content)))
        offset += len(line)
    if data.count(b"clutch:core") != 2 or len(markers) != 2 or markers[0][0] != BEGIN or markers[1][0] != END:
        raise MarkerCorruption()
    return data[: markers[0][1]], data[markers[1][2] :]


def render(data: bytes, *, template: bytes | None = None) -> bytes:
    project = parse(data)
    block = BEGIN + b"\n" + (CORE_TEMPLATE if template is None else template) + END
    if project is None:
        return block + b"\n\n" + data
    prefix, suffix = project
    return prefix + block + suffix


_MODALS = ("must", "must not", "should", "should not", "shall", "shall not", "will", "will not", "may", "may not")
_IMPERATIVES = ("author", "implement", "check", "review", "merge", "commit", "dispatch", "confirm", "reject", "kill", "pause", "resume", "triage", "rework", "drain")
_PROCESS_OPENING = re.compile(r"^clutch\s+(?:" + "|".join((*_MODALS, *_IMPERATIVES)) + r")\b", re.I)
_LIST_PREFIX = re.compile(r"^\s*(?:[-+*]|[0-9]+[.)])\s+")


@dataclass(frozen=True)
class CoreClassification:
    state: Literal["missing", "current", "drifted", "refused"]
    paved_road: str | None = None


def _process_override(remainder: bytes) -> bool:
    paragraphs, continuation = [], []
    for line in remainder.decode(errors="replace").splitlines():
        item = _LIST_PREFIX.match(line)
        if not line.strip() or item:
            paragraphs.append(" ".join(continuation))
            continuation = []
        if line.strip():
            continuation.append(line[item.end() :] if item else line)
    paragraphs.append(" ".join(continuation))
    return any(_PROCESS_OPENING.match(" ".join(paragraph.split())) for paragraph in paragraphs)


def classify_core(data: bytes | None, *, template: bytes | None = None) -> CoreClassification:
    """Judge supplied bytes against this branch's fresh render, without effects."""
    previous = data if data is not None else b""
    try:
        project = parse(previous)
    except MarkerCorruption as exc:
        return CoreClassification("refused", str(exc))
    remainder = previous if project is None else b"".join(project)
    if _process_override(remainder):
        return CoreClassification("refused", "move engine-process rules to the engine core template or rewrite them as project-content rules")
    if project is None:
        return CoreClassification("missing", "run `clutch host core` to insert the managed block")
    if previous != render(previous, template=template):
        return CoreClassification("drifted", "run `clutch host core` to refresh the managed block")
    return CoreClassification("current")


def refresh(paths: Sequence[Path], fs: FileSystem) -> None:
    """Inspect the whole selection before publishing any changed file."""
    pending = []
    for path in dict.fromkeys(paths):
        try:
            previous = path.read_bytes()
        except FileNotFoundError:
            previous = b""
        fresh = render(previous)
        if fresh != previous:
            pending.append((path, fresh))
    for path, fresh in pending:
        fs.write(path, fresh)


async def stale_core(repo, config, git) -> list[str]:
    """Report routed conduct blocks at HEAD that need adoption or refresh."""
    from clutch.git import GitError
    from clutch.providers import routed_conduct_paths

    messages = []
    for path in routed_conduct_paths(config, repo):
        rel = path.relative_to(repo).as_posix()
        try:
            data = (await git._run(repo, "show", f"HEAD:{rel}")).encode("utf-8")
        except GitError:
            data = None
        result = classify_core(data)
        if result.state != "current":
            messages.append(f"{rel}: clutch core is {result.state}; {result.paved_road}")
    return messages


async def committed_core(workspace, config, git):
    """Gather raw candidate bytes only when their blob identities match HEAD."""
    from clutch.artifacts import Finding
    from clutch.git import GitError
    from clutch.providers import routed_conduct_paths

    files, findings = {}, []
    template = CORE_TEMPLATE
    source_path = "clutch/hostfiles.py"
    try:
        source = await git._run(workspace, "show", f"HEAD:{source_path}")
    except GitError:
        pass  # External hosts have no engine source; the installed template owns their core.
    else:
        try:
            assignments = [node.value for node in ast.parse(source).body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CORE_TEMPLATE" for t in node.targets)]
            if len(assignments) != 1 or not isinstance(assignments[0], ast.Constant):
                raise ValueError("CORE_TEMPLATE must be one literal bytes assignment")
            candidate_template = ast.literal_eval(assignments[0])
            if not isinstance(candidate_template, bytes):
                raise ValueError("CORE_TEMPLATE must be bytes")
            template = candidate_template
        except SyntaxError, ValueError:
            findings.append(Finding(code="core_drift", path=source_path, message="cannot extract candidate clutch core template", paved_road="define CORE_TEMPLATE as one literal bytes assignment"))
    for path in routed_conduct_paths(config, workspace):
        rel = path.relative_to(workspace).as_posix()
        try:
            blob = await git.rev_parse(workspace, f"HEAD:{rel}")
        except GitError:
            blob = None
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            data = None
        digest = None if data is None else git_module.blob_sha(data)
        if digest != blob:
            findings.append(Finding(code="core_drift", path=rel, message=f"{rel} differs from its committed candidate bytes", paved_road=f"commit or restore {rel}, then rerun Check"))
        else:
            files[rel] = data
    return dict(core_files=files, core_template=template, core_findings=findings)


class CoreDriftGate:
    """Only current committed routed conduct may enter main. Never repairs."""

    code = "core_drift"

    def check(self, artifact, workspace: Path):
        from clutch.artifacts import Finding
        from clutch.gates import GateReport

        findings = list(artifact.core_findings)
        for path, data in artifact.core_files.items():
            result = classify_core(data, template=artifact.core_template)
            if result.state != "current":
                findings.append(Finding(code=self.code, path=path, message=f"{path}: clutch core is {result.state}", paved_road=result.paved_road))
        return GateReport(code=self.code, verdict="fail" if findings else "pass", findings=findings)
