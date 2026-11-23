"""Pure parsing and selection of roadmap ticket rows."""

import re
import shlex
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import get_args

from clutch.author import ticket_state
from clutch.box import BOX_DIR, Box, RereportJournal, RoadmapRow, Verdict, parse_record, record_path
from clutch.git import GitError
from clutch.journal import EventType
from clutch.providers import child_env
from clutch.runner import SPECS_DIR, Refusal
from clutch.seams import ExecutableNotFound
from clutch.specs import load_spec
from clutch.status import SETTLED, last_states
from clutch.tickets import INTAKE_SIGNAL, Frontmatter, stem_findings, ticket_path

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


def append_row(text: str, release: str, line: str) -> str:
    rows = [row for row in parse(text) if release_name(row.release) == release]
    if not rows:
        raise Refusal(f"no release {release}", "name a release heading of docs/roadmap.md section 8")
    table = min(row._table for row in rows)
    last = max(row.line for row in rows if row._table == table)
    lines = text.splitlines(keepends=True)
    ending = lines[last][len(lines[last].rstrip("\r\n")) :]
    while last + 1 < len(lines) and lines[last + 1].startswith("|"):
        last += 1
    lines.insert(last + 1, line + ending)
    return "".join(lines)


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
    matches = []
    for path in files:
        nested = re.fullmatch(r"docs/([^/]+)/plan\.md", path)
        if (re.fullmatch(r"docs/[^/]+-plan\.md", path) and name in path[5:-3].split("-")) or (nested and (name == nested.group(1) or name in nested.group(1).split("-"))):
            matches.append(path)
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


def unfinished_dependency(dependencies, rows, strikes, states):
    done = {row.stem for row in rows if row.struck or row in strikes}
    by_stem = {row.stem for row in rows}
    return next((stem for stem in dependencies if (stem not in done if stem in by_stem else states.get(stem) not in SETTLED)), None)


def _is_release_audit(row: Row) -> bool:
    return re.sub(r"-r\d+$", "", row.stem) == "release-audit-" + release_name(row.release).replace(".", "")


def choose(rows: list[Row], *, states: dict[str, str], files: set[str], current: str | None = None, drafts: frozenset[str] = frozenset(), held: dict[str, str] | None = None) -> Choice:
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
        elif row.linked or str(ticket_path(row.stem)) in files:
            if not row.linked:
                links.append(row)
            if state == "rejected":
                waits.append(Wait(row, f"{row.stem} is rejected", "give the row a new stem"))
            elif row.stem in drafts and not state:
                waits.append(Wait(row, f"{row.stem} is still a draft", "confirm the draft with `clutch ticket confirm`"))
            else:
                open_rows.append(row)
        elif state:
            waits.append(Wait(row, f"{row.stem} is already in the journal", "give the row a new stem"))
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
        if unfinished_dependency(dependencies, rows, strikes, states) is not None:
            continue
        siblings = (
            [other for other in rows if other != row and release_name(other.release) == release_name(row.release) and not other.struck and other not in strikes] if _is_release_audit(row) else []
        )
        if siblings:
            waits.append(Wait(row, f"release {release_name(row.release)} has {len(siblings)} open rows", "merge or strike the other rows of the release"))
            continue
        if row.kind not in kinds or row.priority not in priorities:
            waits.append(Wait(row, f"invalid kind or priority: {row.kind}, {row.priority}", "use a ticket kind and priority"))
        elif plan_path(row.owner, files) is None:
            waits.append(Wait(row, f"no unique plan for {row.owner}", "start Owner with roadmap or a matching name from exactly one docs/*-plan.md or docs/<name>/plan.md"))
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
            elif held and release_name(row.release) in held:
                release = release_name(row.release)
                waits.append(Wait(row, f"start gate of {release} fails: {held[release]}", "make the release's start block pass"))
            else:
                ready.append(row)
    unfinished = [rank(r) for r in links + open_rows + ready + [w.row for w in waits] if states.get(r.stem) != "rejected"]
    if unfinished:
        first = min(unfinished)
        ready = [row for row in ready if rank(row) == first]
    ready.sort(key=lambda r: (rank(r), r.priority, r.line))
    return Choice(tuple(strikes), tuple(links), len(open_rows), tuple(ready), tuple(waits))


def row_messages(box, row):
    base = re.sub(r"-r\d+$", "", row.stem)
    origin = re.compile(r"roadmap/" + re.escape(base) + r"(?:-r\d+)?$")
    return [message for message in box.messages() if message.message_class == "roadmap_row" and origin.fullmatch(message.origin)]


def refile_count(messages):
    return sum(bool(re.search(r" \[re-file \d+\]$", message.summary)) for message in messages)


def decline_reason(repo, message):
    try:
        _, body = parse_record((repo / record_path(message.resolution.link)).read_text())
    except FileNotFoundError:
        return ""
    return body.partition("Evidence: ")[2].strip()


def rejection_reason(events, stem):
    terminal = diagnosis = operator = None
    for event in events:
        if event.ticket != stem:
            continue
        if event.type == EventType.SIGNAL and event.body.get("signal") == "reject_verdict" and event.body.get("verdict") == "kill" and event.body.get("actor") == "operator":
            operator = event
        elif event.type == EventType.STATE_TRANSITION and event.body.get("routed") == "reject_queue":
            terminal = event
        elif event.type == EventType.SIGNAL and event.body.get("signal") == "diagnosis":
            diagnosis = event
    parts = (
        ([operator.body.get("reason")] if operator else [])
        + ([terminal.body.get("reason")] if terminal else [])
        + (terminal.body.get("rework_findings", []) if terminal else [])
        + (diagnosis.body.get("lessons", []) if diagnosis else [])
    )
    return " ".join(part for part in parts if part) or "rejected"


def fresh_stem(stem, taken):
    base = re.sub(r"-r\d+$", "", stem)
    number = 1
    while f"{base}-r{number}" in taken:
        number += 1
    return f"{base}-r{number}"


def refile_row(text, row, stem):
    lines = text.splitlines(keepends=True)
    for other in parse(text):
        if other.number != row.number:
            line = lines[other.line]
            ending = line[len(line.rstrip("\r\n")) :]
            cells = _cells(line)
            cells[5] = cells[5].replace(f"`{row.stem}`", f"`{stem}`")
            lines[other.line] = "|" + "|".join(cells) + "|" + ending
    line = lines[row.line]
    ending = line[len(line.rstrip("\r\n")) :]
    cells = _cells(line)
    cells[1] = f" `{stem}` "
    cells[7] = " " + re.sub(r"^\*\*Authored\*\* \(.*?\)\.\s*", "", cells[7].strip()) + " "
    lines[row.line] = "|" + "|".join(cells) + "|" + ending
    return "".join(lines)


async def _write_row(checkout, row, edit, action, message, lines):
    async with checkout.git.main_write():
        path = checkout.repo / ROADMAP
        text = path.read_text()
        fresh = next((r for r in parse(text) if r.number == row.number), None)
        if fresh is None or fresh.stem != row.stem or fresh.content != row.content:
            lines.append(f"roadmap: row {row.number} {row.stem} changed on disk; skipped {action}")
            return None
        text = edit(text, fresh)
        checkout.fs.write(path, text.encode())
        await checkout.git.commit(checkout.repo, message, only=[ROADMAP])
        return text


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
    events = checkout.journal.read()
    states = last_states(events)
    named = {event.ticket for event in events if event.ticket}
    taken = named | {row.stem for row in rows} | {match.group(1) for path in files if (match := re.match(r"tickets/([^/]+)/", path))}
    held = await start_holds(checkout, rows, states)
    choice = choose(rows, states=states, files=files, current=current_release(repo), held=held)
    lines = []
    for action, selected, edit in (("strike", choice.strike, strike), ("link", choice.link, link)):
        for row in selected:
            if action == "link" and states.get(row.stem) == "rejected":
                continue
            updated = await _write_row(checkout, row, edit, action, f"clutch(roadmap): {action} {row.stem}", lines)
            if updated is None:
                continue
            text = updated
            lines.append(f"roadmap: {'struck' if action == 'strike' else 'linked'} row {row.number} {row.stem}")
    opened = choice.open
    box = Box(checkout.config.state_dir / BOX_DIR, checkout.fs, rereport=RereportJournal(checkout.journal))
    filed = []

    ready_numbers = []
    for row in choice.ready:
        if row.stem in named and not states.get(row.stem):
            stem = fresh_stem(row.stem, taken)
            updated = await _write_row(checkout, row, lambda text, fresh: refile_row(text, fresh, stem), "refile", f"clutch(roadmap): refile {row.stem} as {stem}", lines)
            if updated is None:
                continue
            text = updated
            taken.add(stem)
        ready_numbers.append(row.number)
    rows = parse(text)
    candidates = [next(r for r in rows if r.number == number) for number in ready_numbers]
    for row in candidates:
        if opened + len(filed) >= ahead:
            break
        messages = row_messages(box, row)
        count = refile_count(messages)
        reason = None
        latest = messages[-1] if messages else None
        if reason is None and latest and latest.resolution is not None and latest.resolution.kind == "declined":
            reason = decline_reason(repo, latest)
        if reason is not None and count >= checkout.config.caps.supervise:
            lines.append(f"roadmap: row {row.number} {row.stem} re-files spent: {reason or 'declined'}")
            continue
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
        summary = f"Roadmap row {row.number} `{row.stem}`: {row.content}"
        if reason is not None:
            if latest is not None:
                summary = latest.summary
            summary += (f" {reason}" if reason else "") + f" [re-file {count + 1}]"
        elif latest and refile_count([latest]):
            summary = latest.summary
        id, _ = box.enqueue(message_class="roadmap_row", origin=f"roadmap/{row.stem}", summary=summary, roadmap_row=payload)
        message = box.get(id)
        if message.resolution is not None and message.resolution.kind == "declined":
            lines.append(f"roadmap: row {row.number} {row.stem} declined -> {message.resolution.link}")
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
            updated = await _write_row(checkout, row, link, "link", f"clutch(roadmap): author {row.stem}", lines)
            if updated is None:
                continue
            text = updated
            lines.append(f"roadmap: authored row {row.number} {row.stem}")
            opened += 1
        elif message.resolution is not None and message.resolution.kind == "declined":
            lines.append(f"roadmap: row {row.number} {row.stem} declined -> {message.resolution.link}")
        else:
            lines.append(f"roadmap: row {row.number} {row.stem} pending -- run clutch roadmap author again")
    lines.extend(
        f"roadmap: row {wait.row.number} {wait.row.stem} waits: {rejection_reason(events, wait.row.stem) if states.get(wait.row.stem) == 'rejected' else wait.reason} -- {wait.road}"
        for wait in choice.waits
    )
    lines.append(f"roadmap: {opened} of {ahead} rows open")
    return lines


def release_name(heading: str) -> str:
    return re.split(r"[ ,]", heading, maxsplit=1)[0]


def draft_stems(repo, rows):
    drafts = set()
    for row in rows:
        path = repo / ticket_path(row.stem)
        try:
            text = path.read_text()
        except FileNotFoundError:
            continue
        if ticket_state(text) == "draft":
            drafts.add(row.stem)
    return frozenset(drafts)


async def status(checkout) -> list[str]:
    path = checkout.repo / ROADMAP
    if not path.is_file():
        raise Refusal(f"missing {ROADMAP}", "restore docs/roadmap.md")
    rows = parse(path.read_text())
    files = set((await checkout.git._run(checkout.repo, "ls-files", "--cached", "--others", "--exclude-standard", "-z")).split("\0"))
    events = checkout.journal.read()
    states = last_states(events)
    held = await start_holds(checkout, rows, states)
    choice = choose(rows, states=states, files=files, current=current_release(checkout.repo), drafts=draft_stems(checkout.repo, rows), held=held)
    box = Box(checkout.config.state_dir / BOX_DIR, checkout.fs)
    messages_by_row = {row: row_messages(box, row) for row in rows}
    declined = {row for row, messages in messages_by_row.items() if messages and messages[-1].resolution is not None and messages[-1].resolution.kind == "declined"}
    releases = {}
    for row in rows:
        counts = releases.setdefault(release_name(row.release), [0, 0, 0, 0])
        if row.struck or row in choice.strike:
            counts[0] += 1
        elif (row.linked or str(ticket_path(row.stem)) in files) and states.get(row.stem) != "rejected":
            counts[1] += 1
        elif row in choice.ready and row not in declined:
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
    lines.append("next: " + (", ".join(row.stem for row in choice.ready if row not in declined) or "none"))
    lines.extend(
        f"waits: row {wait.row.number} {wait.row.stem}: {rejection_reason(events, wait.row.stem) if states.get(wait.row.stem) == 'rejected' else wait.reason} -- {wait.road}" for wait in choice.waits
    )
    for row in rows:
        messages = messages_by_row[row]
        if row.struck or not messages or any(wait.row == row for wait in choice.waits):
            continue
        latest = messages[-1]
        spent = refile_count(messages) >= checkout.config.caps.supervise
        if spent and states.get(row.stem) == "rejected":
            reason = rejection_reason(events, row.stem)
        elif row in declined:
            reason = decline_reason(checkout.repo, latest) or "declined"
        else:
            continue
        label = "re-files spent" if spent else "declined"
        lines.append(f"waits: row {row.number} {row.stem}: {label} -- {reason}")
    return lines


def gates(text: str, fence: str = "gate") -> dict[str, tuple[tuple[str, ...], ...]]:
    result = {}
    release = None
    commands = None
    road = f"add a ```{fence} block under the release's heading in docs/roadmap.md section 8"
    for line in text.splitlines():
        if commands is not None:
            if line.strip() == "```":
                if not commands:
                    raise Refusal(f"empty {fence} for {release}", f"add at least one argv command to the {fence} block")
                result[release] = tuple(commands)
                commands = None
            elif line.strip():
                try:
                    argv = shlex.split(line, posix=True)
                except ValueError as exc:
                    raise Refusal(f"invalid {fence} command for {release}: {exc}", "fix the command's quoting so shlex.split can parse it") from None
                if not argv or not argv[0].strip():
                    raise Refusal(f"{fence} command for {release} has no executable", f"start each {fence} command with a non-empty executable")
                commands.append(tuple(argv))
        elif line.startswith("### "):
            release = release_name(line[4:].strip())
        elif line.strip() == f"```{fence}":
            if release is None:
                raise Refusal(f"{fence} has no release heading", road)
            if release in result:
                raise Refusal(f"duplicate {fence} for {release}", f"keep exactly one {fence} block per release in docs/roadmap.md section 8")
            commands = []
    if commands is not None:
        raise Refusal(f"unclosed {fence} for {release}", f"close the {fence} block with a ``` line")
    return result


async def run_start(checkout, release) -> tuple[bool, list[str]]:
    path = checkout.repo / ROADMAP
    if not path.is_file():
        raise Refusal(f"missing {ROADMAP}", "restore docs/roadmap.md")
    commands = gates(path.read_text(), "start").get(release, ())
    lines = []
    for argv in commands:
        command = shlex.join(argv)
        try:
            rc, _, _ = await checkout.exec_.run(list(argv), cwd=checkout.repo, env=child_env(checkout.env, checkout.config), timeout=checkout.config.drain.max_ticket_minutes * 60.0)
        except TimeoutError, ExecutableNotFound:
            rc = 1
        if rc:
            return False, [command]
        lines.append(command)
    return True, lines


async def start_holds(checkout, rows, states):
    held = {}
    releases = dict.fromkeys(release_name(row.release) for row in rows if not row.struck and states.get(row.stem) not in SETTLED)
    for release in releases:
        passed, lines = await run_start(checkout, release)
        if not passed:
            held[release] = lines[-1]
    return held


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


def parallel_stems(events) -> set[str]:
    running = set()
    parallel = set()
    for event in events:
        if event.type != EventType.STATE_TRANSITION or event.ticket is None or "to" not in event.body:
            continue
        if event.body["to"] == "running":
            others = running - {event.ticket}
            if others:
                parallel.update(others | {event.ticket})
            running.add(event.ticket)
        else:
            running.discard(event.ticket)
    return parallel


async def merged(checkout, stems, *, release=None, priorities=(), since=None, at_least=None, source=None, unattended=False, parallel=False) -> tuple[bool, list[str]]:
    if not stems and release is None and at_least is None:
        raise Refusal("no condition", "add a stem, --release, or --since and --at-least")
    if priorities and release is None:
        raise Refusal("--priority needs --release", "add --release or drop --priority")
    if (since is None) != (at_least is None):
        raise Refusal("--since and --at-least must be paired", "add the missing flag or drop the other")
    if (source is not None or unattended or parallel) and at_least is None:
        raise Refusal(
            "count filter needs --at-least", "add --since and --at-least or drop --source, --unattended and --parallel" if parallel else "add --since and --at-least or drop --source and --unattended"
        )
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
        drafts = draft_stems(checkout.repo, rows)
        choice = choose(rows, states=states, files=frozenset(), drafts=drafts)

        def report(row, label):
            if not row.struck and row not in choice.strike:
                state = states.get(row.stem)
                reason = (f"is {state}" if state else "is a draft" if row.stem in drafts else "is not in the journal") if state not in SETTLED else "has a split ticket that has not settled"
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
            raise Refusal(f"missing tag {since}", "a phase's tag is made at its start by `clutch release bump --minor`") from None
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
        overlapping = parallel_stems(events) if parallel else set()
        count = sum(1 for stem in found if (source is None or sources.get(stem) == source) and (not unattended or stem not in verdicts) and (not parallel or stem in overlapping))
        if count < at_least:
            lines.append(f"roadmap merged: {count} of {at_least} tickets merged since {since} match")
        if parallel:
            spent = {event.ticket for event in events if event.type == EventType.STATE_TRANSITION and event.ticket in overlapping and event.body.get("reason") == "merge_conflict_rerun_spent"}
            lines.extend(f"roadmap merged: {stem} hit merge_conflict_rerun_spent" for stem in sorted(spent))
    return (False, lines) if lines else (True, ["roadmap merged: ok"])
