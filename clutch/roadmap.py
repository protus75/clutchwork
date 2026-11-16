"""Pure parsing and selection of roadmap ticket rows."""

import re
from dataclasses import dataclass, field
from typing import get_args

from clutch.box import BOX_DIR, Box, RereportJournal, RoadmapRow, Verdict
from clutch.runner import SPECS_DIR, Refusal
from clutch.specs import load_spec
from clutch.status import SETTLED, last_states
from clutch.tickets import Frontmatter

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


def choose(rows: list[Row], *, states: dict[str, str], files: set[str]) -> Choice:
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
    unfinished = [r._table for r in links + open_rows + ready + [w.row for w in waits] if states.get(r.stem) != "rejected"]
    if unfinished:
        first = min(unfinished)
        ready = [row for row in ready if row._table == first]
    ready.sort(key=lambda r: (r._table, r.priority, r.line))
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
    choice = choose(rows, states=last_states(checkout.journal.read()), files=files)
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
