"""Pure parsing and selection of roadmap ticket rows."""

import re
import shlex
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import get_args

from clutch import release as release_module
from clutch.box import BOX_DIR, Box, RereportJournal, RoadmapRow, Verdict
from clutch.git import GitError
from clutch.journal import EventType
from clutch.providers import child_env
from clutch.runner import SPECS_DIR, Refusal
from clutch.seams import ExecutableNotFound
from clutch.specs import load_spec
from clutch.status import SETTLED, last_states
from clutch.tickets import INTAKE_SIGNAL, Frontmatter, stem_findings

ROADMAP = "docs/roadmap.md"
COLUMNS = ("#", "Stem", "Owner", "Kind", "P", "Depends on", "Runs before", "Content")
TOKEN = re.compile(r"`([^`]+)`")


@dataclass(frozen=True)
class Row:
    number: int
    release: str
    stem: str
    owner: str
    kind: str
    priority: str
    depends: str
    runs_before: tuple[str, ...]
    content: str
    linked: bool
    struck: bool
    line: int
    _table: int = field(default=0, repr=False, compare=False)


@dataclass(frozen=True)
class Wait:
    row: Row
    reason: str
    road: str


@dataclass(frozen=True)
class Choice:
    strike: tuple[Row, ...]
    link: tuple[Row, ...]
    open: int
    ready: tuple[Row, ...]
    waits: tuple[Wait, ...]


def _cells(line: str) -> list[str]:
    cells = line.rstrip("\r\n")[1:-1].split("|")
    return cells[:7] + ["|".join(cells[7:])]


def parse(text: str) -> list[Row]:
    lines = text.splitlines()
    release = ""
    table = 0
    rows = []
    numbers: set[int] = set()
    stems: set[str] = set()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("### "):
            release = line[4:].strip()
        if line.startswith("|") and tuple(cell.strip() for cell in _cells(line)) == COLUMNS:
            table += 1
            i += 2
            while i < len(lines) and lines[i].startswith("|"):
                raw = _cells(lines[i])
                if len(raw) == 8:
                    cells = [cell.replace("~~", "").strip() for cell in raw]
                    match = TOKEN.search(cells[1])
                    if cells[0].isdigit() and match:
                        number, stem = int(cells[0]), match.group(1)
                        for value, seen, label in ((number, numbers, "number"), (stem, stems, "stem")):
                            if value in seen:
                                raise Refusal(f"duplicate {label}: {value}", f"make {label} unique")
                            seen.add(value)
                        linked = bool(re.search(r"tickets/" + re.escape(stem) + r"/(?:`|\))", lines[i]))
                        struck = any(c.strip().startswith("~~") and c.strip().endswith("~~") for c in raw)
                        rows.append(Row(number, release, stem, cells[2], cells[3], cells[4], cells[5], tuple(TOKEN.findall(cells[6])), cells[7], linked, struck, i, table))
                i += 1
            continue
        i += 1
    if not table:
        raise Refusal("no master table", "restore header: " + " | ".join(COLUMNS))
    return rows


def depends_on(row: Row, rows: list[Row]) -> tuple[str, ...]:
    result = []
    by_number = {r.number: r.stem for r in rows}
    for part in row.depends.split(",") if row.depends else ():
        part = part.strip()
        token = re.fullmatch(r"`([^`]+)`", part)
        single = re.fullmatch(r"row (\d+)", part)
        span = re.fullmatch(r"rows (\d+)-(\d+)", part)
        if token:
            result.append(token.group(1))
        elif single or span:
            start = int((single or span).group(1))
            end = int(span.group(2)) if span else start
            if end < start:
                raise ValueError(f"invalid dependency: {part}")
            for number in range(start, end + 1):
                if number not in by_number:
                    raise ValueError(f"unknown row {number} in {part}")
                result.append(by_number[number])
        else:
            raise ValueError(f"invalid dependency: {part}")
    return tuple(result)


def _edit(text: str, row: Row, *, merged: bool) -> str:
    lines = text.splitlines(keepends=True)
    line = lines[row.line]
    ending = line[len(line.rstrip("\r\n")) :]
    cells = _cells(line)
    if merged:
        cells[1] = " " + "~~" + cells[1].strip() + "~~" + " "
    content = cells[7].strip()
    prefix = "**Authored** ("
    if content.startswith(prefix):
        if merged:
            content = "**Merged** (" + content[len(prefix) :]
        else:
            end = content.index(").", len(prefix))
            content = content[:end] + f", `tickets/{row.stem}/`" + content[end:]
    else:
        label = "Merged" if merged else "Authored"
        content = f"**{label}** (`tickets/{row.stem}/`). " + content
    cells[7] = " " + content + " "
    lines[row.line] = "|" + "|".join(cells) + "|" + ending
    return "".join(lines)


def link(text: str, row: Row) -> str:
    return text if row.linked else _edit(text, row, merged=False)


def strike(text: str, row: Row) -> str:
    return text if row.struck else _edit(text, row, merged=True)


def plan_path(owner: str, files: set[str]) -> str | None:
    words = owner.lower().split()
    if not words:
        return None
    name = words[0]
    if name == "roadmap":
        return ROADMAP
    matches = [path for path in files if re.fullmatch(r"docs/[^/]+-plan\.md", path) and name in path[5:-3].split("-")]
    return matches[0] if len(matches) == 1 else None


def current_release(repo: Path) -> str | None:
    try:
        with (repo / "pyproject.toml").open("rb") as stream:
            version = tomllib.load(stream).get("project", {}).get("version")
    except OSError, tomllib.TOMLDecodeError, AttributeError:
        return None
    if not isinstance(version, str):
        return None
    parts = version.split(".")
    if len(parts) < 2 or not all(re.fullmatch(r"[0-9]+", part) for part in parts[:2]):
        return None
    return f"{parts[0]}.{parts[1]}.0"


def choose(rows: list[Row], *, states: dict[str, str], files: set[str], current: str | None = None) -> Choice:
    tables = [row._table for row in rows if release_name(row.release) == current] if current is not None else []
    c = min(tables) if tables else None

    def rank(row):
        return (0 if c is None or release_name(row.release) == current else 1 if row._table < c else 2, row._table)

    strikes, links, ready, waits = [], [], [], []
    open_rows = []
    for row in rows:
        if row.struck:
            continue
        prefix = re.match(r"\*\*Authored\*\* \((.*?)\)\.", row.content)
        splits = re.findall(r"tickets/([^/]+)/", prefix.group(1)) if prefix else []
        state = states.get(row.stem)
        if state in SETTLED and all(states.get(stem) in SETTLED for stem in splits):
            strikes.append(row)
        elif row.linked:
            if state != "rejected":
                open_rows.append(row)
        elif f"tickets/{row.stem}/ticket.md" in files:
            links.append(row)
            if state != "rejected":
                open_rows.append(row)
        elif state:
            waits.append(Wait(row, f"{row.stem} is already in the journal", "give the row a new stem"))
    done = {row.stem for row in rows if row.struck or row in strikes}
    by_stem = {row.stem: row for row in rows}
    handled = set(strikes + links + open_rows + [w.row for w in waits])
    kinds = get_args(Frontmatter.model_fields["kind"].annotation)
    priorities = get_args(Frontmatter.model_fields["priority"].annotation)
    for row in rows:
        if row.struck or row in handled or row.linked:
            continue
        try:
            dependencies = depends_on(row, rows)
        except ValueError as exc:
            waits.append(Wait(row, str(exc), "correct the Depends on cell"))
            continue
        if any(stem not in done if stem in by_stem else states.get(stem) not in SETTLED for stem in dependencies):
            continue
        if row.kind not in kinds or row.priority not in priorities:
            waits.append(Wait(row, f"invalid kind or priority: {row.kind}, {row.priority}", "use a ticket kind and priority"))
        elif plan_path(row.owner, files) is None:
            waits.append(Wait(row, f"no unique plan for {row.owner}", "start Owner with roadmap or a word from exactly one docs/*-plan.md name"))
        else:
            directory = f"tickets/{row.stem}/evidence/"
            named = [token for token in TOKEN.findall(row.content) if token.startswith(directory)]
            missing = [path for path in named if path not in files]
            has_evidence = any(path.startswith(directory) for path in files)
            if missing:
                waits.append(Wait(row, "missing evidence: " + ", ".join(missing), "run the capture and save it at " + ", ".join(missing)))
            elif not named and not has_evidence and re.search(r"hand test|agent capture", row.content, re.I):
                waits.append(Wait(row, "capture evidence missing", f"run the capture and save it under {directory}"))
            elif not named and not has_evidence and row.kind == "bug":
                waits.append(Wait(row, "observed failure evidence missing", f"save the observed failure under {directory}"))
            else:
                ready.append(row)
    unfinished = [rank(r) for r in links + open_rows + ready + [w.row for w in waits] if states.get(r.stem) != "rejected"]
    if unfinished:
        first = min(unfinished)
        ready = [row for row in ready if rank(row) == first]
    ready.sort(key=lambda r: (rank(r), r.priority, r.line))
    return Choice(tuple(strikes), tuple(links), len(open_rows), tuple(ready), tuple(waits))


async def author_ahead(checkout, ahead, author_messages) -> list[str]:
    repo = checkout.repo
    if await checkout.git.status_porcelain(repo, "--", ROADMAP):
        raise Refusal(f"uncommitted {ROADMAP}", f"commit or restore {ROADMAP}, then run `clutch roadmap author` again")
    path = repo / ROADMAP
    if not path.is_file():
        raise Refusal(f"missing {ROADMAP}", "restore the master ticket table in docs/roadmap.md")
    text = path.read_text()
    rows = parse(text)
    files = set((await checkout.git._run(repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")).split("\0"))
    choice = choose(rows, states=last_states(checkout.journal.read()), files=files, current=current_release(repo))
    lines = []
    for action, selected, edit in (("strike", choice.strike, strike), ("link", choice.link, link)):
        for row in selected:
            text = edit(text, row)
            checkout.fs.write(path, text.encode())
            await checkout.git.commit(repo, f"clutch(roadmap): {action} {row.stem}", only=[ROADMAP])
            lines.append(f"roadmap: {'struck' if action == 'strike' else 'linked'} row {row.number} {row.stem}")
    opened = choice.open
    box = Box(checkout.config.state_dir / BOX_DIR, checkout.fs, rereport=RereportJournal(checkout.journal))
    filed = []

    def declined(row, message):
        return f"roadmap: row {row.number} {row.stem} declined -> {message.resolution.link} -- reword the row's Content in docs/roadmap.md to file it again"

    for row in choice.ready:
        if opened + len(filed) >= ahead:
            break
        payload = RoadmapRow(
            number=row.number,
            release=row.release,
            stem=row.stem,
            owner=row.owner,
            kind=row.kind,
            priority=row.priority,
            depends=list(depends_on(row, rows)),
            runs_before=list(row.runs_before),
            content=row.content,
            plan=plan_path(row.owner, files),
        )
        id, _ = box.enqueue(message_class="roadmap_row", origin=f"roadmap/{row.stem}", summary=f"Roadmap row {row.number} `{row.stem}`: {row.content}", roadmap_row=payload)
        message = box.get(id)
        if message.resolution is not None and message.resolution.kind == "declined":
            lines.append(declined(row, message))
            continue
        if message.status == "pending" and message.verdict is None:
            version = load_spec((SPECS_DIR / "triage.md").read_text()).meta.version
            box.record_verdict(id, Verdict(verdict="author", produced_by_spec_version=version, rationale=f"Roadmap row {row.number} is planned work in docs/roadmap.md"))
        filed.append((row, id))
    if filed:
        await author_messages([id for _, id in filed])
    for row, id in filed:
        message = box.get(id)
        if message.resolution is not None and message.resolution.kind == "ticket":
            text = link(text, row)
            checkout.fs.write(path, text.encode())
            await checkout.git.commit(repo, f"clutch(roadmap): author {row.stem}", only=[ROADMAP])
            lines.append(f"roadmap: authored row {row.number} {row.stem}")
            opened += 1
        elif message.resolution is not None and message.resolution.kind == "declined":
            lines.append(declined(row, message))
        else:
            lines.append(f"roadmap: row {row.number} {row.stem} pending -- run clutch roadmap author again")
    lines.extend(f"roadmap: row {wait.row.number} {wait.row.stem} waits: {wait.reason} -- {wait.road}" for wait in choice.waits)
    lines.append(f"roadmap: {opened} of {ahead} rows open")
    return lines


def release_name(heading: str) -> str:
    return re.split(r"[ ,]", heading, maxsplit=1)[0]


async def status(checkout) -> list[str]:
    path = checkout.repo / ROADMAP
    if not path.is_file():
        raise Refusal(f"missing {ROADMAP}", "restore docs/roadmap.md")
    rows = parse(path.read_text())
    files = set((await checkout.git._run(checkout.repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")).split("\0"))
    events = checkout.journal.read()
    states = last_states(events)
    choice = choose(rows, states=states, files=files, current=current_release(checkout.repo))
    releases = {}
    for row in rows:
        counts = releases.setdefault(release_name(row.release), [0, 0, 0, 0])
        if row.struck or row in choice.strike:
            counts[0] += 1
        elif (row.linked or f"tickets/{row.stem}/ticket.md" in files) and states.get(row.stem) != "rejected":
            counts[1] += 1
        elif row in choice.ready:
            counts[2] += 1
        else:
            counts[3] += 1
    gates_by_release = {}
    for event in events:
        if event.type == EventType.SIGNAL and event.body.get("signal") == "roadmap_gate":
            gates_by_release[event.body["release"]] = event
    lines = []
    for release, (merged_count, authored, ready, blocked) in releases.items():
        event = gates_by_release.get(release)
        gate = "not run"
        if event is not None:
            gate = f"passed {event.ts}" if event.body["passed"] else f"failed {event.ts}: {event.body['failed']}"
        lines.append(f"release {release}: {merged_count} merged, {authored} authored, {ready} ready, {blocked} blocked; gate {gate}")
    lines.append("next: " + (", ".join(row.stem for row in choice.ready) or "none"))
    lines.extend(f"waits: row {wait.row.number} {wait.row.stem}: {wait.reason} -- {wait.road}" for wait in choice.waits)
    return lines


def gates(text: str) -> dict[str, tuple[tuple[str, ...], ...]]:
    result = {}
    release = None
    commands = None
    road = "add a ```gate block under the release's heading in docs/roadmap.md section 8"
    for line in text.splitlines():
        if commands is not None:
            if line.strip() == "```":
                if not commands:
                    raise Refusal(f"empty gate for {release}", "add at least one argv command to the gate block")
                result[release] = tuple(commands)
                commands = None
            elif line.strip():
                try:
                    argv = shlex.split(line, posix=True)
                except ValueError as exc:
                    raise Refusal(f"invalid gate command for {release}: {exc}", "fix the command's quoting so shlex.split can parse it") from None
                if not argv or not argv[0].strip():
                    raise Refusal(f"gate command for {release} has no executable", "start each gate command with a non-empty executable")
                commands.append(tuple(argv))
        elif line.startswith("### "):
            release = release_name(line[4:].strip())
        elif line.strip() == "```gate":
            if release is None:
                raise Refusal("gate has no release heading", road)
            if release in result:
                raise Refusal(f"duplicate gate for {release}", "keep exactly one gate block per release in docs/roadmap.md section 8")
            commands = []
    if commands is not None:
        raise Refusal(f"unclosed gate for {release}", "close the gate block with a ``` line")
    return result


async def run_gate(checkout, release) -> tuple[bool, list[str]]:
    path = checkout.repo / ROADMAP
    if not path.is_file():
        raise Refusal(f"missing {ROADMAP}", "restore docs/roadmap.md")
    blocks = gates(path.read_text())
    if release not in blocks:
        raise Refusal(f"no gate for {release}", "add a ```gate block under the release's heading in docs/roadmap.md section 8")
    lines = []
    failed = None
    for argv in blocks[release]:
        command = shlex.join(argv)
        why = None
        detail = ""
        try:
            rc, out, err = await checkout.exec_.run(list(argv), cwd=checkout.repo, env=child_env(checkout.env, checkout.config), timeout=checkout.config.drain.max_ticket_minutes * 60.0)
            if rc:
                why = f"exit {rc}"
                tail = [line for line in err.splitlines() if line.strip()] or [line for line in out.splitlines() if line.strip()]
                if tail:
                    detail = f" -- {tail[-1]}"
        except TimeoutError:
            why = "timeout"
        except ExecutableNotFound:
            why = "not found"
        if why is not None:
            lines.append(f"gate {release}: failed ({why}): {command}{detail}")
            failed = command
            break
        lines.append(f"gate {release}: ok: {command}")
    passed = failed is None
    lines.append(f"gate {release}: {'passed' if passed else 'failed'}")
    checkout.journal.append(EventType.SIGNAL, {"signal": "roadmap_gate", "release": release, "passed": passed, "failed": failed})
    return passed, lines


async def merged(checkout, stems, *, release=None, priorities=(), since=None, at_least=None, source=None, unattended=False) -> tuple[bool, list[str]]:
    if not stems and release is None and at_least is None:
        raise Refusal("no condition", "add a stem, --release, or --since and --at-least")
    if priorities and release is None:
        raise Refusal("--priority needs --release", "add --release or drop --priority")
    if (since is None) != (at_least is None):
        raise Refusal("--since and --at-least must be paired", "add the missing flag or drop the other")
    if (source is not None or unattended) and at_least is None:
        raise Refusal("count filter needs --at-least", "add --since and --at-least or drop --source and --unattended")
    if at_least is not None and at_least < 1:
        raise Refusal("--at-least must be positive", "set --at-least to at least 1")
    for stem in stems:
        if findings := stem_findings(stem):
            raise Refusal(findings[0].message, findings[0].paved_road)
    events = checkout.journal.read()
    states = last_states(events)
    lines = []
    if stems or release is not None:
        path = checkout.repo / ROADMAP
        if not path.is_file():
            raise Refusal(f"missing {ROADMAP}", "restore docs/roadmap.md")
        rows = parse(path.read_text())
        choice = choose(rows, states=states, files=frozenset())

        def report(row, label):
            if not row.struck and row not in choice.strike:
                state = states.get(row.stem)
                reason = (f"is {state}" if state else "is not in the journal") if state not in SETTLED else "has a split ticket that has not settled"
                lines.append(f"roadmap merged: {label}row {row.number} {row.stem} {reason}")

        for stem in stems:
            row = next((row for row in rows if row.stem == stem), None)
            if row is None:
                raise Refusal(f"no row for {stem}", "name a row's stem from docs/roadmap.md section 8")
            report(row, "")
        if release is not None:
            selected = [row for row in rows if release_name(row.release) == release]
            if not selected:
                raise Refusal(f"no release {release}", "name a release heading of docs/roadmap.md section 8")
            for row in selected:
                if not priorities or row.priority in priorities:
                    report(row, f"release {release} ")
    if since is not None:
        tag = f"refs/tags/{since}"
        try:
            await checkout.git.rev_parse(checkout.repo, tag)
        except GitError:
            raise Refusal(f"missing tag {since}", "a phase's tag is made at its start by `clutch release --minor`") from None
        log = await checkout.git._run(checkout.repo, "log", "--first-parent", "--format=%(trailers:key=clutch-ticket,valueonly)", f"{tag}..HEAD")
        found = {line.strip() for line in log.splitlines() if line.strip()}
        sources = {}
        verdicts = set()
        for event in events:
            if event.type != EventType.SIGNAL:
                continue
            signal = event.body.get("signal")
            if signal == INTAKE_SIGNAL:
                sources[event.ticket] = event.body.get("source")
            if signal == "draft_confirmed" or (signal == "reject_verdict" and event.body.get("actor") == "operator"):
                verdicts.add(event.ticket)
        count = sum(1 for stem in found if (source is None or sources.get(stem) == source) and (not unattended or stem not in verdicts))
        if count < at_least:
            lines.append(f"roadmap merged: {count} of {at_least} tickets merged since {since} match")
    return (False, lines) if lines else (True, ["roadmap merged: ok"])


async def ship(checkout) -> list[str]:
    current = current_release(checkout.repo)
    if current is None:
        return []
    passed, lines = await run_gate(checkout, current)
    if not passed:
        return lines
    if checkout.config.release.publish:
        await release_module.publishable(checkout.repo, checkout.git, checkout.env, checkout.config)
    version, sha = await release_module.release(checkout.repo, checkout.git, checkout.exec_, child_env(checkout.env, checkout.config), "minor")
    release_module.journal_release(checkout.journal, version, sha)
    lines.append(f"release: tagged v{version} at {sha}")
    if checkout.config.release.publish:
        version, _, _ = await release_module.publish(checkout.repo, checkout.git, checkout.exec_, checkout.fs, checkout.env, checkout.config)
        lines.append(f"publish: uploaded {version} to PyPI")
    return lines
