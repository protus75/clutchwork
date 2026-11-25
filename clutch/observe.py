"""Read-only host observations for the CLI and extension."""

import asyncio
import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from importlib.metadata import metadata
from pathlib import Path
from types import SimpleNamespace
from typing import Literal, get_args
from urllib.parse import unquote

from clutch import ask
from clutch.box import BOX_DIR
from clutch.config import load_config
from clutch.drain import PREMISE, authored_at, awaiting_operator, order_tickets, parked_blob
from clutch.enginelog import ENGINE_LOG_FILE, engine_log_path
from clutch.graph import layout
from clutch.help import COMMANDS, help_map, help_pick
from clutch.journalcache import open_journal_cache
from clutch.lockfile import ENGINE_VERBS
from clutch.providers import ADAPTERS
from clutch.rework import settled_dependencies
from clutch.specs import load_spec
from clutch.status import (
    CLOSED,
    SETTLED,
    Admission,
    AdmissionFacts,
    confirm_admission,
    dismiss_admission,
    latest_transitions,
    lint_admission,
    order_admission,
    reject_admission,
    review_admission,
    run_admission,
    triage_admission,
)
from clutch.tickets import (
    CHECKS_FILE,
    DIAGNOSIS_FILE,
    REVIEW_FILE,
    RUN_FILE,
    TICKET_FILE,
    Frontmatter,
    TicketInvalid,
    _graph,
    _intake_plan_stem,
    _porcelain,
    artifact_path,
    in_fence,
    intake_pending,
    order,
    parse_ticket,
    read_tolerant,
    ticket_path,
    validate_ticket,
)

WATCH_STATE_GLOB = f"{{journal/*.jsonl,queue.json,{ENGINE_LOG_FILE},box/*.json}}"

STEP_NAMES = {
    "meta": "Meta",
    "acceptance": "Acceptance",
    "requisition_review": "Requisition",
    "implement": "Implement",
    "check": "Check",
    "merge": "Merge",
    "review": "Review",
    "review_visual": "Visual review",
    "resolve": "Resolve",
    "diagnose": "Diagnose",
    "rework": "Rework",
    "retro": "Retro",
    "triage": "Triage",
    "author": "Author",
}

PHASE_NAMES = {"preflight": "Preflight", "retro_check": "Retro check"}

STEP_KINDS: dict[str, str] = {
    **{f"{step}_{suffix}": step for step in (*STEP_NAMES, *PHASE_NAMES, "stage") for suffix in ("start", "ok", "failed")},
    **{event: event for event in ("engine_start", "engine_stop", "engine_lost")},
}


STATUS_KEYS = (
    "invalid",
    "new",
    "draft",
    "held_change",
    "held_operator",
    "waits_on",
    "not_eligible",
    "interrupted",
    "retry_pending",
    "after",
    "ready",
    "upgrade_hold",
    "running",
    "merged",
    "already_satisfied",
)


def repository_url() -> str:
    return next(value.split(", ", 1)[1] for value in metadata("clutchwork").get_all("Project-URL") if value.startswith("Repository, "))


def help_payload():
    help = help_map(Path.read_text, repository_url())
    return help, help_pick(help)


@dataclass(frozen=True)
class Context:
    root: Path
    state: Path
    config: Path
    exec: object
    git: object
    env: object


def process_output(ctx, *args):
    _, out, _ = asyncio.run(ctx.exec.run(args, cwd=ctx.root, env=ctx.env, timeout=30))
    return out


def git_output(ctx, *args):
    return asyncio.run(ctx.git._run(ctx.root, *args))


def local(ts: str) -> datetime:
    return datetime.fromisoformat(ts).astimezone()


def clock(ts: str) -> str:
    return local(ts).strftime("%-I:%M %p")


def ago(ts: str) -> str:
    seconds = int((datetime.now().astimezone() - local(ts)).total_seconds())
    return f"{seconds // 60}m{seconds % 60:02d}s"


def relative(ts: str, now: datetime) -> str:
    minutes = int((now - local(ts)).total_seconds() / 60 + 0.5)
    if minutes < 60:
        return f"{minutes} min ago"
    if minutes < 2880:
        return f"{int(minutes / 60 + 0.5)} hr ago"
    return f"{int(minutes / 1440 + 0.5)} days ago"


def processes(ctx) -> list[tuple[int, int, str]]:
    out = process_output(ctx, "ps", "-eo", "pid=,ppid=,args=")
    rows = []
    for line in out.splitlines():
        pid, ppid, *args = line.split(None, 2)
        rows.append((int(pid), int(ppid), args[0] if args else ""))
    return rows


def started(ctx, pid: int) -> datetime:
    text = process_output(ctx, "ps", "-o", "lstart=", "-p", str(pid)).strip()
    return datetime.strptime(text, "%a %b %d %H:%M:%S %Y").astimezone()


def lock_holder(state: Path, name: str = "clutch.lock") -> datetime | None:
    """When the live lock holder (drain, serve, run, review, ...) started; None when no live process holds the lock.

    A killed drain leaves its lockfile behind, so a pid that no longer exists holds nothing.
    """
    try:
        lock = json.loads((state / name).read_text())
    except OSError, ValueError:
        return None
    if not lock.get("pid") or not lock.get("started_at"):
        return None
    try:
        os.kill(lock["pid"], 0)
    except ProcessLookupError:
        return None
    except PermissionError:
        pass
    return datetime.fromisoformat(lock["started_at"])


def lock_verb(holder: dict, name: str) -> str:
    if holder.get("verb"):
        return holder["verb"]
    if name == "clutch.lock":
        return "clutch"
    try:
        argv = Path(f"/proc/{holder['pid']}/cmdline").read_bytes().decode().split("\0")
        index = argv.index("clutch") + 1
        if argv[index : index + 1] == ["--config"]:
            index += 2
        return argv[index] or "clutch"
    except OSError, ValueError, IndexError, KeyError, UnicodeError:
        return "clutch"


def lock_display(state: Path, name: str) -> tuple[str, str]:
    if lock_holder(state, name) is None:
        return "", ""
    try:
        holder = json.loads((state / name).read_text())
        verb = lock_verb(holder, name)
        return f"{verb} since {clock(holder['started_at'])} (pid {holder['pid']})", verb
    except OSError, ValueError, KeyError:
        return "", ""


def running_stems(state: Path, last_state: dict[str, dict]) -> list[str]:
    """Stems journaled `running` by the live lock holder.

    The journal's last `running` outlives a killed engine, and a later holder such as `review` does not reconcile it,
    so a `running` journaled before the holder started is stale.
    """
    since = lock_holder(state)
    if since is None:
        return []
    return [s for s, b in last_state.items() if b.get("to") == "running" and datetime.fromisoformat(b["ts"]) >= since]


def this_repo(ctx, pid: int, config: str | None) -> bool:
    """Whether a drain runs against this checkout: its --config is ours, or it has none and runs here."""
    try:
        cwd = Path(os.readlink(f"/proc/{pid}/cwd"))
    except OSError:
        return False
    return (cwd / config).resolve() == ctx.config if config else cwd.resolve() == ctx.root and ctx.config == ctx.root / "config.yaml"


def drain_processes(ctx, rows: list[tuple[int, int, str]]) -> list[int]:
    """This repo's engine drain processes, oldest first; a self-upgrade re-exec leaves its parent waiting on the child.

    Another host's drain also runs `python -m clutch --config <its config> engine drain` from this venv.
    """
    pids = []
    for pid, _, args in rows:
        match = re.match(r"\S*python3? -m clutch (?:--config (\S+) )?engine drain\b", args)
        if match and this_repo(ctx, pid, match.group(1)):
            pids.append(pid)
    return sorted(pids, key=lambda pid: started(ctx, pid))


def _open_calls(evidence: Path, stem: str):
    records = []
    for directory in (evidence / "calls").glob("*"):
        if not unquote(directory.name).startswith(f"llm/{stem}/") or (directory / "end.json").exists():
            continue
        try:
            record = json.loads((directory / "start.json").read_text())
            start = datetime.fromisoformat(record["clock"]["wall_start"])
        except OSError, ValueError, KeyError, TypeError:
            continue
        records.append((start, directory.name, record))
    return records


def _session(record):
    ids = record.get("native_ids") or {}
    value = ids.get("session_id") or ids.get("thread_id")
    return {"provider": record["provider"]["name"], "id": value} if value else None


def step_session(evidence: Path, stem: str, surface: str, attempt: int, run_seq: int):
    records = []
    for directory in (evidence / "calls").glob("*"):
        try:
            record = json.loads((directory / "start.json").read_text())
            if (record.get("stem"), record.get("surface"), record.get("attempt"), record.get("run_seq")) == (stem, surface, attempt, run_seq):
                records.append((datetime.fromisoformat(record["clock"]["wall_start"]), directory.name, record))
        except OSError, ValueError, KeyError, TypeError:
            continue
    return _session(max(records, key=lambda item: item[:2])[2]) if records else None


def live_call(evidence: Path, stem: str, surface: str, began: str) -> str:
    """The newest open model call for this stage, from its evidence record."""
    records = [(start, name, record) for start, name, record in _open_calls(evidence, stem) if record["surface"] == surface and (not began or start >= datetime.fromisoformat(began))]
    if not records:
        return ""
    record = max(records, key=lambda item: item[:2])[2]
    return f"{record['provider']['name']} {record['model']['requested']}"


def frontmatter(path: Path) -> dict[str, object]:
    try:
        return read_tolerant(path.read_text()).frontmatter
    except OSError:
        return {}


def capability(ctx, events: list[dict], stem: str, surface: str) -> str:
    """Show the effective ticket capability; requisition review uses its spec effort."""
    window = events
    for i, e in enumerate(events):
        body = e.get("body", {})
        if e.get("ticket") == stem and body.get("signal") == "reject_verdict" and body.get("verdict") == "keep" and body.get("actor") in ("operator", "supervisor"):
            window = events[i + 1 :]
    rung = next((e["body"]["rung"] for e in reversed(window) if e.get("type") == "cap_consumed" and e.get("ticket") == stem and e["body"].get("cap") == "retry" and "rung" in e["body"]), None)
    meta = frontmatter(ctx.root / ticket_path(stem))
    tier = rung["tier"] if rung else meta.get("agent_tier", "medium")
    effort = rung["effort"] if rung else meta.get("agent_effort", "medium")
    if surface == "resolve":
        spec = load_spec((Path(__file__).parent / "specs" / "resolve.md").read_text()).meta
        return f"{spec.tier}/{spec.effort}"
    if surface == "requisition_review":
        effort = load_spec((Path(__file__).parent / "specs" / "requisition_review.md").read_text()).meta.effort
    return f"{tier}/{effort}" + (" (escalated)" if rung else "")


def read_lines(path: Path, limit: int) -> list[dict]:
    rows = []
    for line in path.read_text(errors="replace").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except ValueError:
            pass
    return rows


def journal(state: Path) -> list[dict]:
    events: list[dict] = []
    for segment in sorted((state / "journal").glob("*.jsonl")):
        for line in segment.read_text(errors="replace").splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
    return events


def current_step(log: list[dict], stem: str, since: str) -> tuple[str, str, str | None]:
    """The step `stem` is on, inferred from its last engine-log stage event; when it began; its model surface."""
    floor = datetime.fromisoformat(since)
    stages = [e for e in log if e.get("stem") == stem and e.get("event") in ("stage_start", "stage_end") and datetime.fromisoformat(e["ts"]) >= floor]
    if not stages:
        return "Starting", "", None
    last = stages[-1]
    name = STEP_NAMES.get(last.get("surface"), last.get("surface", "?"))
    if last["event"] == "stage_start":
        return name, last["ts"], None if last.get("surface") in ("check", "merge") else last.get("surface")
    after = {"requisition_review": "Implement", "implement": "Check", "check": "Review", "review": "Merge", "diagnose": "Retry or hold"}.get(last.get("surface"))
    return (after or f"after {name}"), last["ts"], None


def depends(path: Path) -> list[str]:
    return list(read_tolerant(path.read_text()).depends)


def held(history, blobs, candidates) -> set[str]:
    """Content parks matching a committed ticket."""
    return {s for s in candidates if (blob := parked_blob(history, s)) is not None and blob == blobs.get(s)}


def operator_holds(ctx, history, candidates) -> set[str]:
    if not candidates:
        return set()
    caps_config = load_config(ctx.config, cwd=ctx.root).caps
    return {s for s in candidates if awaiting_operator(history, s, caps_config)}


def as_events(events: list[dict]) -> list[SimpleNamespace]:
    """Adapt journal dictionaries for event projections."""
    return [SimpleNamespace(type=e.get("type"), body=e.get("body", {}), ticket=e.get("ticket"), ts=e.get("ts"), key=e.get("key")) for e in events]


def last_bodies(history) -> dict[str, dict]:
    """Latest transition bodies with their timestamps."""
    return {stem: {**e.body, "ts": e.ts} for stem, e in latest_transitions(history).items()}


UPGRADE_HOLD = "held: engine upgrade pending; starts after serve restarts on new code"


def upgrade_pending(state, events):
    since = lock_holder(state)
    if since is None:
        return False
    for event in reversed(events):
        if event.get("type") == "signal":
            signal = event.get("body", {}).get("signal")
            if signal == "serve_handoff":
                return False
            if signal == "serve_upgrade_pending":
                return datetime.fromisoformat(event["ts"]) >= since
    return False


def idle_reason(stem, view):
    if stem in view.get("waiting", {}):
        return "waits for a free slot: overlaps " + ", ".join(view["waiting"][stem]), "slot_overlap"
    if view.get("hold") == "max_unmerged":
        return "waits for merges: max_unmerged finished tickets wait to merge", "merge_wait"
    return None


def queue(ctx, events: list[dict], last_state: dict[str, dict], running: set[str], held_stems: set[str], *, alive: bool = False) -> list[tuple[str, str, str]]:
    """Every confirmed ticket not yet settled, rejected, or running: (priority, stem, why it is waiting)."""
    done = CLOSED
    history = as_events(events)
    waiting_on_person = operator_holds(ctx, history, {e.ticket for e in history if e.ticket is not None})
    held_stems = held_stems | waiting_on_person
    # A dependency is met when it, or every leaf of the split that superseded it, settled: the drain's own test.
    settled = settled_dependencies(history)
    rows = []
    upgrade = upgrade_pending(ctx.state, events)
    for path in sorted((ctx.root / "tickets").glob("*/ticket.md")):
        stem, meta = path.parent.name, frontmatter(path)
        last = last_state.get(stem, {}).get("to")
        if meta.get("state") != "confirmed" or last in done or stem in running:
            continue
        open_deps = [d for d in depends(path) if d not in settled]
        if stem in waiting_on_person:
            spent = next((e["body"].get("mechanical") for e in reversed(events) if e.get("ticket") == stem and e.get("body", {}).get("signal") == "diagnosis"), None)
            why = f"NEEDS YOUR KEEP OR KILL ({spent})" if spent and "cap spent" in spent else "NEEDS YOUR KEEP OR KILL"
        elif stem in held_stems:
            why = "held until the ticket changes"
        elif last == "running":
            why = "interrupted: the engine stopped mid-run; reruns when it restarts"
        elif open_deps:
            why = "waits on " + ", ".join(open_deps)
        elif last is None:
            why = "ready, not run yet"
        else:
            why = f"retry pending (last: {last})"
        if upgrade and (why == "ready, not run yet" or why.startswith("retry pending (")):
            why = UPGRADE_HOLD
        rows.append((meta.get("priority", "P2"), stem, why))
    rows.sort()
    try:
        view = json.loads((ctx.state / "queue.json").read_text())
    except FileNotFoundError:
        return rows
    if alive:
        rows = [(priority, stem, idle_reason(stem, view)[0] if why == "ready, not run yet" and idle_reason(stem, view) else why) for priority, stem, why in rows]
    by_stem = {row[1]: row for row in rows}
    ordered = []
    for stem in view["order"]:
        if stem in by_stem and not (by_stem[stem][2].startswith("waits on ") or stem in held_stems):
            priority, _, why = by_stem.pop(stem)
            hints = view["runs_before"].get(stem, [])
            if hints:
                why += "; runs before: " + ", ".join(hints)
            ordered.append((priority, stem, why))
    return ordered + [row for row in rows if row[1] in by_stem]


def recent_steps(state: Path, log: list[dict], limit: int) -> list[dict]:
    """Merge stage and engine lifetime events, newest first."""
    rows = []
    lifecycle = [e for e in log if e.get("event") in ("engine_start", "engine_stop")]
    for e in log:
        event = e.get("event")
        if event in ("stage_start", "stage_end"):
            verb = "start" if event == "stage_start" else f"end ({e.get('outcome', '?')})"
            surface = e.get("surface")
            prefix = surface if surface in STEP_NAMES else "stage"
            suffix = "start" if event == "stage_start" else "ok" if e.get("outcome") == "ok" else "failed"
            name = STEP_NAMES.get(surface, surface)
            if surface == "triage" and "run_seq" in e:
                name = f"{name} #{e['run_seq']}"
            rows.append({"ts": e["ts"], "stem": e.get("stem"), "surface": surface, "attempt": e.get("attempt"), "run_seq": e.get("run_seq"), "text": f"{name} {verb}", "kind": f"{prefix}_{suffix}"})
        elif event in ("phase_start", "phase_end"):
            name = PHASE_NAMES[e["phase"]]
            outcome = e.get("outcome", "?")
            verb = "start" if event == "phase_start" else f"end ({outcome.replace('_', ' ')})"
            suffix = "start" if event == "phase_start" else "failed" if outcome == "failed" else "ok"
            kind = f"{e['phase']}_{suffix}"
            rows.append({"ts": e["ts"], "stem": None, "text": f"{name} {verb}", "kind": kind})
        elif event == "engine_start":
            rows.append({"ts": e["ts"], "stem": None, "text": f"{e['verb']} started (pid {e['pid']})", "kind": "engine_start"})
        elif event == "engine_stop":
            rows.append({"ts": e["ts"], "stem": None, "text": f"{e['verb']} stopped ({e['outcome']})", "kind": "engine_stop"})
    if lifecycle:
        latest = max(enumerate(lifecycle), key=lambda pair: (pair[1]["ts"], pair[0]))[1]
        try:
            holder_pid = json.loads((state / "clutch.lock").read_text()).get("pid") if lock_holder(state) is not None else None
        except OSError, ValueError:
            holder_pid = None
        if latest["event"] == "engine_start" and holder_pid != latest["pid"]:
            rows.append({"ts": latest["ts"], "stem": None, "text": f"{latest['verb']} ended without a stop record (killed?)", "kind": "engine_lost"})
    return sorted(rows, key=lambda row: row["ts"], reverse=True)[:limit]


def text_snapshot(ctx) -> str:
    state = ctx.state
    events = journal(state)
    log = read_lines(engine_log_path(state), 4000) if (engine_log_path(state)).exists() else []
    rows = processes(ctx)
    drains = drain_processes(ctx, rows)
    lines = [f"clutch view watch  {datetime.now().astimezone().strftime('%-I:%M:%S %p')}", ""]
    if not drains:
        lines.append("Drain: not running")
        since = None
    else:
        since = started(ctx, drains[0])
        restarts = f", restarted {len(drains) - 1}x on new engine code" if len(drains) > 1 else ""
        lines.append(f"Drain: running since {since.strftime('%-I:%M %p')} (pid {drains[-1]}{restarts})")
    history = as_events(events)
    last_state = last_bodies(history)
    running = running_stems(state, last_state)
    lines.append("")
    if running:
        for stem in running:
            attempt = sum(1 for e in events if e.get("type") == "state_transition" and e.get("ticket") == stem and e["body"].get("to") not in ("running", None))
            step, began, surface = current_step(log, stem, last_state[stem]["ts"])
            when = f" for {ago(began)} (since {clock(began)})" if began else ""
            lines.append(f"Now: {stem}  attempt {attempt + 1}  step: {step}{when}")
            if surface:
                lines.append(f"     asked for tier/effort {capability(ctx, events, stem, surface)}")
                model = live_call(state / "evidence", stem, surface, began) if drains else ""
                lines.append(f"     model: {model or 'no model call running'}")
            else:
                lines.append("     no model call (mechanical step)")
    else:
        lines.append("Now: nothing running")
    if since is not None:
        done = [(s, b) for s, b in last_state.items() if b.get("to") != "running" and local(b["ts"]) >= since]
        lines.append("")
        lines.append("This drain:")
        for stem, body in sorted(done, key=lambda item: item[1]["ts"]):
            outcome = "merged" if body["to"] in SETTLED else f"stopped: {body['to']}"
            if body.get("routed") == "reject_queue":
                outcome += " (held for you)"
            lines.append(f"  {clock(body['ts'])}  {stem}  {outcome}")
        if not done:
            lines.append("  (nothing finished yet)")
    pending = queue(ctx, events, last_state, set(running), held(history, committed_ticket_shas(ctx), {e.ticket for e in history if e.ticket is not None}), alive=bool(drains))
    lines += ["", f"Queue ({len(pending)} to do):"]
    lines += [f"  {priority}  {stem}  {why}" for priority, stem, why in pending] or ["  (empty)"]
    recent = recent_steps(state, log, 8)
    if recent:
        lines += ["", "Recent steps:"]
        for row in recent:
            stem = f"{row['stem']}  " if row["stem"] is not None else ""
            lines.append(f"  {clock(row['ts'])}  {stem}{row['text']}")
    return "\n".join(lines)


# Recent Steps keeps more history than watch's 8 because its view scrolls.
STEPS = 40


def load_tickets(ctx, skip: set[str]) -> tuple[dict, dict]:
    """Full engine parse of unsettled tickets only."""
    parsed, invalid = {}, {}
    for path in sorted((ctx.root / "tickets").glob("*/ticket.md")):
        stem = path.parent.name
        if stem in skip:
            continue
        try:
            parsed[stem] = parse_ticket(stem, path.read_text(), ctx.root)
        except TicketInvalid as e:
            invalid[stem] = str(e).splitlines()[0] if str(e) else "invalid ticket"
    return parsed, invalid


def simulate(candidates: dict, done: set[str], authored: dict, *, strict: bool) -> list:
    """Pick tickets one at a time the way the drain does; strict stops when nothing is eligible."""
    order, done, remaining = [], set(done), dict(candidates)
    while remaining:
        if strict:
            eligible = [t for t in remaining.values() if set(t.depends) <= done]
        else:
            # Unblocked view: a dependency outside the blocked set (rejected, missing) no longer holds anything back.
            eligible = [t for t in remaining.values() if all(d in done or d not in remaining for d in t.depends)]
        if not eligible:
            if strict:
                break
            eligible = list(remaining.values())  # a depends cycle among blocked tickets: still list them
        pick = order_tickets(eligible, authored)[0]
        order.append(pick)
        done.add(pick.stem)
        del remaining[pick.stem]
    return order


def uncommitted_tickets(ctx) -> tuple[set[str], set[str]]:
    """(stems whose ticket.md differs from HEAD or is untracked, stems never committed): not yet on the ticket plane."""
    out = asyncio.run(ctx.git.status_porcelain(ctx.root, "--", "tickets"))
    dirty, new = set(), set()
    for line in out.splitlines():
        code, path = line[:2], line[3:]
        # `tickets/<stem>/ticket.md` changed, or the whole `tickets/<stem>/` dir is untracked.
        if path.endswith("/ticket.md") or (path.endswith("/") and len(Path(path).parts) == 2):
            dirty.add(Path(path).parts[1])
            if code == "??":
                new.add(Path(path).parts[1])
    return dirty, new


def committed_ticket_shas(ctx) -> dict[str, str]:
    """Each stem's committed ticket.md blob: the content a `requisition_verdict` approves by `ticket_sha`."""
    out = git_output(ctx, "ls-tree", "-r", "HEAD", "--", "tickets")
    shas = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        if path.endswith("/ticket.md"):
            shas[Path(path).parts[1]] = meta.split()[2]
    return shas


def commits(ctx) -> dict[str, dict]:
    out = git_output(ctx, "log", "--format=%H%x1f%h%x1f%an%x1f%aI%x1f%s%x1f%b%x1e", "main")
    rows = {}
    for record in out.split("\x1e"):
        record = record.lstrip("\n")
        if not record:
            continue
        sha, short, author, date, subject, body = record.split("\x1f", 5)
        message = (subject + ("\n\n" + body if body else "")).rstrip()
        rows[sha] = {"sha": sha, "short": short, "author": author, "date": date, "subject": subject, "message": message}
    return rows


@dataclass(frozen=True)
class MenuEntry:
    kind: Literal["ticket", "box"]
    admission: Callable[..., Admission]
    inputs: tuple[str, ...]
    needs_lock: bool = False
    extension_only: bool = False
    command: str = field(kw_only=True)


# Every emitted key lives here. Ask rules are extension-only; every other rule is a verb admission.
MENU = {
    "clutchReview": MenuEntry("ticket", review_admission, ("stem", "facts", "file_exists", "ticket", "intake_decision", "stray", "pending"), command="clutch.ticket.review"),
    "clutchLint": MenuEntry("ticket", lint_admission, ("stem", "facts", "file_exists"), command="clutch.ticket.lint"),
    "clutchRun": MenuEntry("ticket", run_admission, ("stem", "facts", "file_exists", "ticket", "intake_decision", "stray"), needs_lock=True, command="clutch.ticket.run"),
    "clutchConfirm": MenuEntry("ticket", confirm_admission, ("facts", "stem", "draft", "interrupted"), command="clutch.ticket.confirm"),
    "clutchReject": MenuEntry("ticket", reject_admission, ("facts", "stem", "draft", "interrupted"), command="clutch.ticket.reject"),
    "clutchCopySession": MenuEntry("ticket", lambda session: Admission("admit" if session else "noop"), ("session",), extension_only=True, command="clutch.ticket.copySession"),
    "clutchCopyStem": MenuEntry("ticket", lambda section: Admission("admit" if section == "merged" else "noop"), ("section",), extension_only=True, command="clutch.ticket.copyStem"),
    "clutchAskDiagnose": MenuEntry("ticket", lambda section: Admission("admit" if section != "merged" else "noop"), ("section",), extension_only=True, command="clutch.ticket.askDiagnose"),
    "clutchAskDrafts": MenuEntry("ticket", lambda row_draft: Admission("admit" if row_draft else "noop"), ("row_draft",), extension_only=True, command="clutch.ticket.askDrafts"),
    "clutchAskReview": MenuEntry("ticket", lambda section: Admission("admit" if section in ("queued", "blocked") else "noop"), ("section",), extension_only=True, command="clutch.ticket.askReview"),
    "clutchPriority": MenuEntry("ticket", order_admission, ("stem", "facts", "file_exists", "lock_holder", "ticket"), command="clutch.ticket.priority"),
    "clutchRunsBefore": MenuEntry("ticket", order_admission, ("stem", "facts", "file_exists", "lock_holder", "ticket"), command="clutch.ticket.runsBefore"),
    "clutchTriage": MenuEntry("box", triage_admission, ("id", "messages"), needs_lock=True, command="clutch.box.triage"),
    "clutchDismiss": MenuEntry("box", dismiss_admission, ("id", "messages"), needs_lock=True, command="clutch.box.dismiss"),
}


def row_menu(kind, inputs, alive):
    menu = {}
    for key, entry in MENU.items():
        if entry.kind != kind:
            continue
        values = inputs[key] if kind == "ticket" else inputs
        admission = entry.admission(**{name: values[name] for name in entry.inputs})
        menu[key] = "off" if admission.outcome != "admit" else "locked" if entry.needs_lock and alive else "on"
    return menu


def ticket_menu_inputs(ctx, facts, stems, holder, interrupted):
    """Read porcelain once and share graph reads across all row validations."""
    entries = _porcelain(asyncio.run(ctx.git.status_porcelain(ctx.root, "--untracked-files=all")))
    pending, evidence, stray = asyncio.run(intake_pending(ctx.root, ctx.git, entries))
    states = facts.states
    graphs = (_graph(ctx.root), _graph(ctx.root, "Runs before"))
    result = {}

    def validated(stem, text):
        try:
            return validate_ticket(stem, text, ctx.root, graphs=graphs)
        except TicketInvalid as exc:
            return exc.findings

    for stem in stems:
        path = ctx.root / ticket_path(stem)
        exists = path.is_file()
        text = path.read_text() if exists else ""
        plan = _intake_plan_stem(ctx.root, stem, pending[stem], evidence[stem], states.get(stem), graphs=graphs) if stem in pending else None
        decision = plan[2] if plan else None
        claimed = plan[1] if plan else text
        # Merged run and settled review/order outcomes do not depend on validation.
        disk = validated(stem, claimed) if exists and states.get(stem) != "merged" else None
        review_ticket = None
        ticket_pending = any(p.startswith(f"tickets/{stem}/") for _, p in entries)
        if exists and states.get(stem) not in CLOSED and not (ticket_pending and stray) and not isinstance(decision, list):
            main_text = claimed if plan else git_output(ctx, "show", f"main:{ticket_path(stem)}")
            review_ticket = disk if main_text == claimed else validated(stem, main_text)
        common = dict(
            stem=stem,
            facts=facts,
            file_exists=exists,
            intake_decision=decision,
            stray=stray,
            pending=ticket_pending,
            draft=False,
            row_draft=False,
            interrupted=interrupted,
            section="",
            session=False,
            lock_holder=holder,
        )
        order_ticket = validated(stem, text) if exists and text != claimed and states.get(stem) not in CLOSED else disk
        runs_before_ticket = validated(stem, order(text, priority=None, runs_before=[])) if exists and states.get(stem) not in CLOSED else order_ticket
        result[stem] = {
            key: dict(common, ticket=review_ticket if key == "clutchReview" else order_ticket if key == "clutchPriority" else runs_before_ticket if key == "clutchRunsBefore" else disk)
            for key, entry in MENU.items()
            if entry.kind == "ticket"
        }
    return result, set(pending), {s for s, new in pending.items() if new}


def extension_fields(root: Path) -> dict:
    return {
        "root": str(root.resolve()),
        "commands": {
            "review": ["ticket", "review"],
            "lint": ["ticket", "lint"],
            "run": ["engine", "run"],
            "triage": ["box", "triage"],
            "dismiss": ["box", "dismiss"],
            "serve": ["engine", "serve"],
            "stop": ["engine", "stop"],
            "order": ["ticket", "order"],
            "stats": ["view", "stats", "--tree"],
            "askDiagnose": ["prompt", "diagnose"],
            "askReview": ["prompt", "review"],
            "askDrafts": ["prompt", "drafts"],
            "askDrainLoop": ["prompt", "drain-loop"],
            "askBox": ["prompt", "box"],
        },
        "orderFlags": {"priority": "--priority", "runsBefore": "--runs-before"},
        "providerInstalls": [{"label": f"Update {name}", "detail": f"installs {ADAPTERS[name].PACKAGE}@latest", "argv": ["provider", "install", name]} for name in sorted(ADAPTERS)]
        + [{"label": "Update all providers", "detail": "installs all provider CLIs", "argv": ["provider", "install", *sorted(ADAPTERS)]}],
    }


def journal_facts(state: Path, history) -> AdmissionFacts:
    from clutch.reconcile import orphans

    with open_journal_cache(state) as cache:
        return AdmissionFacts(states=cache.last_states(), reject=frozenset(cache.reject_queue()), settled=settled_dependencies(history), orphans=frozenset(orphans(history)))


def _shared_fences(tickets):
    paths = {}
    for ticket in tickets:
        for path in {path.rstrip("/") for path in ticket.scope_fence if not in_fence(path, [f"tickets/{ticket.stem}"])}:
            paths.setdefault(path, set()).add(ticket.stem)
    shared = {}
    for path, stems in sorted(paths.items()):
        if len(stems) > 1:
            for stem in stems:
                shared.setdefault(stem, []).append(f"{path} (also: {', '.join(sorted(stems - {stem}))})")
    return {stem: "\n".join(lines) for stem, lines in shared.items()}


def prompt_pick(config, root, stems, box_ids):
    entries, problems = ask.catalog(config, root)
    return {
        "promptPick": [{"label": " ".join(entry["argv"][1:]), "detail": entry["description"], "argv": entry["argv"], "takes": entry["takes"]} for entry in entries]
        + [{"label": str(path), "detail": message} for path, message in problems],
        "promptArgs": {"stem": stems, "box": box_ids},
    }


def snapshot(ctx, *, merged_limit: int | None = None) -> dict:
    state = ctx.state
    help, help_pick_items = help_payload()
    now = datetime.now().astimezone()
    events = journal(state)
    log = read_lines(engine_log_path(state), 4000) if (engine_log_path(state)).exists() else []
    history = as_events(events)
    facts = journal_facts(state, history)
    last = last_bodies(history)
    tickets, invalid = load_tickets(ctx, {s for s, b in last.items() if b.get("to") in CLOSED})
    authored = authored_at(history)
    # The drain's own test: a dependency is met when it, or every leaf of the split that superseded it, settled.
    settled = set(facts.settled)
    blobs = committed_ticket_shas(ctx)
    reject_stems = operator_holds(ctx, history, facts.reject)
    held_stems = held(history, blobs, {s for s, st in facts.states.items() if st in (PREMISE, "gate_failed")}) | reject_stems

    def to(stem: str) -> str | None:
        return last.get(stem, {}).get("to")

    merged = sorted((s for s in last if to(s) in SETTLED), key=lambda s: last[s]["ts"], reverse=True)
    merged = merged[:merged_limit]
    alive = lock_holder(state) is not None
    interrupted = set(facts.orphans) if not alive else set()
    lock, verb = lock_display(state, "clutch.lock")
    commit_lock, _ = lock_display(state, "commit.lock")
    running = running_stems(state, last)
    open_ = {s: t for s, t in tickets.items() if to(s) not in CLOSED and s not in running and t.frontmatter.state not in ("rejected", "merged")}
    runnable = {s: t for s, t in open_.items() if t.frontmatter.state == "confirmed" and s not in held_stems}
    queued = simulate(runnable, settled | set(running), authored, strict=True)
    queued_stems = {t.stem for t in queued}
    blocked = simulate({s: t for s, t in open_.items() if s not in queued_stems}, settled | set(running) | queued_stems, authored, strict=False)
    blocked_stems = {t.stem for t in blocked}

    # The menu and displayed pending/new flags share intake's porcelain interpretation.
    menu_inputs, dirty, new = ticket_menu_inputs(ctx, facts, set(tickets) | set(invalid) | set(merged) | set(running), object() if alive else None, interrupted)
    verdicts: dict[str, dict[str, str]] = {}  # stem -> ticket_sha -> last verdict for that content
    for e in events:
        body = e.get("body", {})
        if e.get("type") == "signal" and body.get("signal") == "requisition_verdict" and e.get("ticket"):
            verdicts.setdefault(e["ticket"], {})[body.get("ticket_sha")] = body.get("verdict")

    def review(stem: str) -> str:
        """The buildability review for the ticket's current committed text; the drain reviews before a first run."""
        if stem in new or stem not in blobs:
            return "not reviewed: reviewed before its first run, once committed"
        verdict = verdicts.get(stem, {}).get(blobs[stem])
        if verdict == "approve":
            return "approved"
        if verdict:
            return f"{verdict} on this text: edit the ticket to address the findings"
        if verdicts.get(stem):
            return "approved an earlier version: re-reviewed before it runs"
        return "not reviewed: reviewed before its first run"

    def why_blocked(t) -> tuple[str, str]:
        if t.stem in new:
            return "new: draft stays draft until clutch ticket confirm; no state is confirmed by next intake", "new"
        if t.frontmatter.state != "confirmed":
            return t.frontmatter.state, "draft"
        if t.stem in held_stems and t.stem not in reject_stems:
            return f"held until the ticket changes (last: {to(t.stem)})", "held_change"
        if t.stem in reject_stems:
            spent = next((e["body"].get("mechanical") for e in reversed(events) if e.get("ticket") == t.stem and e.get("body", {}).get("signal") == "diagnosis"), None)
            return (f"held: {spent}" if spent else f"held (last: {to(t.stem)})"), "held_operator"
        waits = [d for d in t.depends if d not in settled]
        return ("waits on " + ", ".join(waits), "waits_on") if waits else ("not eligible", "not_eligible")

    upgrade = upgrade_pending(state, events)

    try:
        queue_view = json.loads((state / "queue.json").read_text()) if verb in ENGINE_VERBS else {}
    except FileNotFoundError:
        queue_view = {}

    def why_queued(t) -> tuple[str, str]:
        if to(t.stem) == "running":
            return "interrupted: the engine stopped mid-run; reruns when it restarts", "interrupted"
        if upgrade:
            return UPGRADE_HOLD, "upgrade_hold"
        if to(t.stem) is not None:
            return f"retry pending (last: {to(t.stem)})", "retry_pending"
        waits = [d for d in t.depends if d not in settled]
        return ("after " + ", ".join(waits), "after") if waits else (idle_reason(t.stem, queue_view) or ("ready", "ready"))

    def base(stem: str, section: str, status: str, status_key: str) -> dict:
        t, path = tickets.get(stem), ctx.root / ticket_path(stem)
        return {
            "stem": stem,
            "section": section,
            "status": status,
            "help": {"section": f"section.{section}", "status": f"status.{status_key}"},
            "priority": t.frontmatter.priority if t else frontmatter(path).get("priority", ""),
            "depends": list(t.depends) if t else depends(path) if path.exists() else [],
            "goal": t.sections.get("Goal / Why", "") if t else "",
            "runsBefore": list(t.runs_before) if t else [],
            "path": str(ticket_path(stem)),
            "held": stem in held_stems,
            # Only a committed draft appears in the drafts prompt.
            "draft": bool(t) and t.frontmatter.state == "draft" and stem not in new,
            # Pending ticket changes go through intake before a verdict is submitted.
            "committed": stem not in dirty,
            "review": review(stem) if section != "merged" else "",
        }

    # Invalid rows lead the blocked section: they usually depend on valid ones, and graph edges only point down.
    rows = [{**base(stem, "blocked", "invalid: " + why, "invalid"), "goal": ""} for stem, why in sorted(invalid.items()) if to(stem) not in CLOSED and stem not in running]
    rows += [base(t.stem, "blocked", *why_blocked(t)) for t in reversed(blocked)]
    rows += [base(t.stem, "queued", *why_queued(t)) for t in reversed(queued)]
    for stem in running:
        step, began, _ = current_step(log, stem, last[stem]["ts"])
        row = base(stem, "running", f"running: {step}" + (f" for {ago(began)}" if began else ""), "running")
        calls = [entry for entry in _open_calls(state / "evidence", stem) if _session(entry[2])]
        if calls:
            row["sessionId"] = _session(max(calls, key=lambda item: item[:2])[2])["id"]
        rows.append(row)
    log_rows = commits(ctx)
    for stem in merged:
        body = last[stem]
        row = base(stem, "merged", "merged" if body["to"] == "merged" else body["to"].replace("_", " "), body["to"])
        row["commit"] = log_rows.get(body.get("commit", ""))
        row["mergedAt"] = body["ts"]
        row["mergedAtAgo"] = relative(body["ts"], now)
        row["mergedAtDisplay"] = local(body["ts"]).strftime("%x, %X")
        if row["commit"]:
            row["commit"] = {**row["commit"], "dateAgo": relative(row["commit"]["date"], now), "dateDisplay": local(row["commit"]["date"]).strftime("%x, %X")}
        rows.append(row)
    shown = {r["stem"] for r in rows}
    unmerged = [r["stem"] for r in rows if r["section"] != "merged"]
    priorities = list(get_args(Frontmatter.model_fields["priority"].annotation))
    shared_fences = _shared_fences(tickets[r["stem"]] for r in rows if r["section"] != "merged" and r["stem"] in tickets)

    for r in rows:
        status_help = help[r["help"]["status"]]["text"]
        r["tooltip"] = r["commit"]["message"] + "\n\n" + status_help if r["section"] == "merged" and r["commit"] else status_help
        inputs = menu_inputs[r["stem"]]
        for values in inputs.values():
            values["session"] = "sessionId" in r
            values["section"] = r["section"]
            values["row_draft"] = r["draft"]
            values["draft"] = bool(tickets.get(r["stem"])) and tickets[r["stem"]].frontmatter.state == "draft"
        r["menu"] = row_menu("ticket", inputs, alive)
        r["next"] = [COMMANDS[MENU[key].command] for key, value in r["menu"].items() if value == "on"]
        r["priorityChoices"] = [{"label": p, "description": "current" if p == r["priority"] else ""} for p in priorities]
        r["priorityTag"] = r["priority"] if r["section"] in ("running", "queued") else ""
        if r["priorityTag"]:
            r["priorityHelp"] = "priority"
        if r["section"] != "merged":
            r["runsBeforeChoices"] = [{"label": stem, "picked": stem in r["runsBefore"]} for stem in unmerged if stem != r["stem"]]
        r["depends"] = [d for d in r["depends"] if d in shown]
        detail = [{"heading": None, "text": r["status"] + (f" · {r['priority']}" if r["priority"] else "")}]
        if r["review"]:
            detail.append({"heading": None, "text": f"review: {r['review']}"})
        if r["section"] == "merged":
            if c := r["commit"]:
                detail.append({"heading": "Commit", "text": c["subject"]})
                detail.append({"heading": None, "text": f"{c['short']} · {c['author']} · {c['dateAgo']} ({c['dateDisplay']})"})
            else:
                detail.append({"heading": None, "text": "no commit on main"})
            if r["mergedAt"]:
                detail.append({"heading": None, "text": f"settled {r['mergedAtAgo']} ({r['mergedAtDisplay']})"})
        else:
            detail.extend(
                [
                    {"heading": "Goal / Why", "text": r["goal"] or "(none)"},
                    {"heading": "Runs before", "text": ", ".join(r["runsBefore"]) or "(none)"},
                ]
            )
        if r["stem"] in shared_fences and r["section"] != "merged":
            detail.append({"heading": "Shared fence", "text": shared_fences[r["stem"]]})
        if r["depends"]:
            detail.append({"heading": "Depends on", "text": ", ".join(r["depends"])})
        r["detail"] = detail
    for row, graph in zip(rows, layout(rows)):
        row["graph"] = graph
    from clutch.box import Box
    from clutch.seams import LocalFileSystem
    from clutch.status import project

    box = Box(state / BOX_DIR, LocalFileSystem())
    messages = box.messages()
    labels = {id: (cls, label, summary) for id, cls, label, summary in project([], box=box).box}
    box_rows = []
    for m in reversed(messages):
        cls, label, summary = labels[m.id]
        fields = [["Summary", m.summary], ["Origin", m.origin]]
        if m.stage is not None:
            fields.append(["Stage", f"{m.stage}: {m.outcome}"])
        if m.reports:
            fields.append(["Re-reports", str(m.reports)])
        if m.verdict:
            fields.append(["Recorded verdict", f"{m.verdict.verdict}: {m.verdict.rationale}"])
        if m.resolution:
            fields.append(["Resolution", f"{m.resolution.kind} -> {m.resolution.link}"])
        for title, value in (("Fixed failure", m.fixed_failure), ("Overcorrection risk", m.overcorrection_risk), ("Retro report", m.retro_report_key)):
            if value:
                fields.append([title, value])
        if m.proposed_spec_paths:
            fields.append(["Proposed specs", "\n".join(m.proposed_spec_paths)])
        if m.test_issue:
            fields.append(["Test issue", m.test_issue])
        if m.proposed_paths:
            fields.append(["Proposed paths", "\n".join(m.proposed_paths)])
        path = box.path(m).resolve()
        link = None
        if m.resolution:
            link = str(ticket_path(m.resolution.link)) if m.resolution.kind == "ticket" else str(Path("tickets/decisions") / (m.resolution.link + ".md"))
        outcome = ("author" if m.resolution.kind == "ticket" else m.resolution.kind) if m.resolution else ("reopened" if m.reopen else "pending")
        box_rows.append(
            {
                "id": m.id,
                "seq": m.seq,
                "messageClass": cls,
                "help": {
                    "class": f"box.{cls}",
                    "outcome": f"boxOutcome.{outcome}",
                },
                "state": m.status,
                "menu": row_menu("box", {"id": m.id, "messages": messages}, alive),
                "status": f"{cls} · {label}",
                "summary": summary,
                "fields": fields,
                "path": str(path.relative_to(ctx.root.resolve())) if path.is_relative_to(ctx.root.resolve()) else None,
                "link": link,
            }
        )
    steps = recent_steps(state, log, STEPS)
    for step in steps:
        surface = step.pop("surface", None)
        attempt = step.pop("attempt", None)
        run_seq = step.pop("run_seq", None)
        if step.get("stem") is not None and surface is not None and attempt is not None and run_seq is not None:
            session = step_session(state / "evidence", step["stem"], surface, attempt, run_seq)
            if session:
                step["session"] = session
                step["contextValue"] = "session"
        if surface in ("author", "triage"):
            # Author keys its box message by attempt; triage by run_seq (its attempt is the pass number).
            seq = attempt if surface == "author" else run_seq
            message = next((row for row in box_rows if row["seq"] == seq), None)
            link = message["link"] if message and not step["kind"].endswith("_start") else None
            step["path"] = link if link and (ctx.root / link).is_file() else message["path"] if message else None
        elif surface == "retro":
            path = f"tickets/retro/{run_seq:06d}.md" if run_seq is not None else None
            step["path"] = path if path and (ctx.root / path).is_file() else None
        elif stem := step.get("stem"):
            name = {"implement": RUN_FILE, "check": CHECKS_FILE, "review": REVIEW_FILE, "diagnose": DIAGNOSIS_FILE}.get(surface, TICKET_FILE)
            path = Path(artifact_path(stem, name))
            fallback = Path(ticket_path(stem))
            step["path"] = str(path) if (ctx.root / path).is_file() else str(fallback) if (ctx.root / fallback).is_file() else None
        step["timeDisplay"] = clock(step["ts"])
        step["dateDisplay"] = local(step["ts"]).strftime("%x, %X")
        step["help"] = f"step.{STEP_KINDS[step['kind']]}"
        step["tooltip"] = " · ".join(filter(None, (step["dateDisplay"], step.get("stem"), step["text"]))) + "\n" + help[step["help"]]["text"]
    box_counts = {
        kind: sum(m.status == "pending" if kind == "pending" else m.resolution is not None and m.resolution.kind == ("ticket" if kind == "author" else kind) for m in messages)
        for kind in ("pending", "author", "tombstone", "declined")
    }
    counts = {section: sum(r["section"] == section for r in rows) for section in ("blocked", "queued", "running", "merged")}
    total = counts["queued"] + counts["running" if alive else "blocked"]
    tooltip = f"{counts['running']} running, {counts['queued']} queued" if alive else f"engine stopped: {counts['blocked']} blocked, {counts['queued']} queued"
    badge = {"value": total, "tooltip": tooltip} if total else None
    return {
        **extension_fields(ctx.root),
        **prompt_pick(load_config(ctx.config, cwd=ctx.root), ctx.root, [row["stem"] for row in rows], [row["id"] for row in box_rows]),
        "help": help,
        "helpPick": help_pick_items,
        "headerHelp": {**{section: f"section.{section}" for section in counts}, "engine": "lock.engine", "commit": "lock.commit"},
        "boxHeaderHelp": {kind: f"boxOutcome.{kind}" for kind in box_counts},
        "badge": badge,
        "box": box_rows,
        "boxCounts": box_counts,
        "priorities": priorities,
        "watch": [{"base": str(ctx.root.resolve()), "glob": "tickets/*/ticket.md"}, {"base": str(state.resolve()), "glob": WATCH_STATE_GLOB}],
        "drainCommand": ["engine", "drain", "--detach"],
        "engineVerbs": [
            {"label": "Drain", "detail": help["verb.drain"]["what"], "argv": ["engine", "drain", "--detach"]},
            {"label": "Serve", "detail": help["verb.serve"]["what"], "argv": ["engine", "serve"]},
            {"label": "Stop after the running ticket", "detail": help["verb.stop"]["what"], "argv": ["engine", "stop"]},
            {"label": "Kill (drain or serve)", "detail": help["verb.kill"]["what"], "argv": ["engine", "kill"]},
            {"label": "Status", "detail": help["verb.status"]["what"], "argv": ["view", "status"]},
            {"label": "Retro", "detail": help["verb.retro"]["what"], "argv": ["engine", "retro"]},
        ],
        "counts": counts,
        "runningStem": running[0] if running else None,
        "verdictDecisions": [dict(zip(("request_id", "verb", "stem", "decision", "reason"), row)) for row in project(history).verdict_decisions],
        "verdictDecisionsHelp": "verdict.decisions",
        "verdictCommands": {verb: ["ticket", verb, "--extension"] for verb in ("confirm", "reject")},
        "stateDir": str(state.resolve()),
        "configPath": str(ctx.config.resolve()),
        "at": now.isoformat(),
        "engine": verb in ENGINE_VERBS,
        "lock": lock,
        "commitLock": commit_lock,
        "rows": rows,
        "steps": steps,
        "blockedCount": len(blocked_stems) + len(invalid),
    }


def ping_engine(state_dir, read=Path.read_bytes):
    from clutch import control

    alive = lock_holder(state_dir) is not None
    holder = json.loads(read(state_dir / "clutch.lock")) if alive else {}
    verb = lock_verb(holder, "clutch.lock") if alive else None
    engine = verb in ENGINE_VERBS
    lifecycle, hold = control.read_active(state_dir, read) if engine else (None, None)
    return {"alive": alive, "engine": engine, "verb": verb, "pid": holder.get("pid"), "started_at": holder.get("started_at"), "lifecycle_id": lifecycle, "hold_id": hold}
