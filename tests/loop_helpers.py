"""Shared scheduler and triage test scaffolding."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared test scaffolding for the scheduler, triage, restart and serve tests: a fake clock, ticket text builder, scheduler and watcher Rig, import-closure walker, triage escape rigs, repository, orphan and held fixtures, and serve graph, admission, notify and upgrade helpers
# relates: [clutch/config.py, clutch/journal.py, clutch/scheduler.py, clutch/seams.py, clutch/tickets.py, clutch/watcher.py, tests/cli_helpers.py]
# owner: engine
# verified: 58c46bba
# hash: b226427d49583c9eafabe741b72de429701eab24419f342d1db0b444b37b6a66

import ast
import asyncio
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from clutch import runner, serve, stages
from clutch.__main__ import main
from clutch.box import Box, Resolution
from clutch.config import Caps
from clutch.daemon import TicketWriter
from clutch.journal import EventType, Journal
from clutch.llm import FakeLLM
from clutch.lockfile import Lockfile
from clutch.scheduler import Scheduler
from clutch.seams import LocalFileSystem
from clutch.tickets import INTAKE_SIGNAL, parse_ticket
from clutch.watcher import Watcher
from tests.cli_helpers import ENV, TICKET, git_fake
from tests.config_fixture import amend_config
from tests.dispatch_settle import dispatch_settled
from tests.drain_helpers import Clock, confirmed, make_root
from tests.fakes import FakeExec, turn
from tests.stage_replies import requisition_reply
from tests.stages_helpers import STEM as TERMINAL_STEM


class Time:
    def __init__(self):
        self.now = datetime(2026, 1, 1, tzinfo=UTC)
        self.waits = []

    def __call__(self):
        return self.now

    async def sleep(self, seconds):
        future = asyncio.get_running_loop().create_future()
        self.waits.append((self.now + timedelta(seconds=seconds), future))
        await future

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)
        for deadline, future in self.waits:
            if deadline <= self.now and not future.done():
                future.set_result(None)


def text(priority="P2", state="confirmed", depends="none"):
    return TICKET.format(depends=depends).replace("priority: P2", f"state: {state}\nsource: human\npriority: {priority}", 1)


class Rig:
    def __init__(self, root):
        self.root = root
        (root / "clutch").mkdir()
        (root / "clutch/thing.py").write_text("")
        self.time = Time()
        self.journal = Journal(root / "state", self.time)
        self.quarantine = set()
        self.drought = set()
        self.unmerged = 0
        self.calls = []
        self.active = None
        self.scheduler = Scheduler(
            self.journal,
            self.dispatch,
            state_dir=root / "state",
            fs=LocalFileSystem(),
            clock=self.time,
            caps=Caps,
            ticket_sha=self.ticket_sha,
            quarantined=lambda: self.quarantine,
            drought_parked=lambda: self.drought,
            completed_unmerged=lambda: self.unmerged,
            max_unmerged=2,
        )
        self.files = {}
        clock = self.time
        self.watcher = Watcher(
            root,
            read=self.files.get,
            journal=self.journal,
            publish=self.scheduler.update,
            remove=self.scheduler.remove,
            clock=self.time,
            sleep=clock.sleep,
            debounce=5,
        )

    async def ticket_sha(self, stem):
        return self.files.get(stem, "")

    async def dispatch(self, ticket):
        self.calls.append(ticket.stem)

    def add(self, stem, priority="P2", state="confirmed", depends="none"):
        raw = text(priority, state, depends)
        path = self.root / "tickets" / stem / "ticket.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw)
        self.files[stem] = raw
        ticket = parse_ticket(stem, raw, self.root)
        self.scheduler.update(ticket)
        return ticket

    def transition(self, stem, to, **body):
        self.journal.append(EventType.STATE_TRANSITION, {"to": to, **body}, ticket=stem)

    def intake(self, stem):
        self.journal.append(EventType.SIGNAL, {"signal": INTAKE_SIGNAL, "source": "human", "state": "confirmed", "new": True, "commit": "abc"}, ticket=stem)

    async def publish(self, *stems):
        for stem in stems:
            self.watcher.change(stem)
        await turn()
        self.time.advance(5)
        await turn()

    async def drain(self):
        while await dispatch_settled(self.scheduler) is not None:
            pass


def scheduler_import_closure(sources):
    pending, reached = ["clutch.__main__"], set()
    while pending:
        module = pending.pop()
        if module in reached or module not in sources:
            continue
        reached.add(module)
        if module != "clutch":
            pending.append("clutch")  # Package initialization is also reachable.
        for node in ast.walk(ast.parse(sources[module])):
            if isinstance(node, ast.Import):
                pending.extend(a.name for a in node.names if a.name.split(".")[0] == "clutch")
            elif isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    package = module.split(".")[: -node.level]
                    base = ".".join([*package, *([base] if base else [])])
                if base == "clutch" or base.startswith("clutch."):
                    pending.append(base)
                    pending.extend(f"{base}.{a.name}" for a in node.names)
    return reached


def root_with_box(tmp_path: Path) -> tuple[Path, Box]:
    root = make_root(tmp_path)
    config = root.joinpath("config.yaml")
    config.write_text(
        config.read_text().replace(
            "  - {tier: medium, surface: implement, candidates: [{provider: claude}]}",
            """  - {tier: medium, surface: implement, candidates: [{provider: claude}]}
  - {tier: low, surface: author, candidates: [{provider: claude}]}
  - {tier: medium, surface: author, candidates: [{provider: claude}]}
  - {tier: high, surface: author, candidates: [{provider: claude}]}
  - {tier: max, surface: author, candidates: [{provider: claude}]}
  - {tier: low, surface: review, candidates: [{provider: claude}]}
  - {tier: medium, surface: review, candidates: [{provider: claude}]}
  - {tier: high, surface: review, candidates: [{provider: claude}]}
  - {tier: max, surface: review, candidates: [{provider: claude}]}
""",
        )
    )
    return root, Box(root / ".clutch" / "state" / "box", LocalFileSystem())


def enqueue(box: Box, summary: str) -> str:
    return box.enqueue(message_class="suggestion", origin="test", summary=summary)[0]


def reply(verdict: str, *, link=None, summary="Triage's own summary", evidence=None, days=30) -> str:
    return json.dumps(
        {"verdict": verdict, "link": link, "summary": summary, "rationale": "Observed and classified", "evidence": evidence or [], "reopen_after_days": None if verdict == "author" else days}
    )


def author_reply(stem: str) -> str:
    return json.dumps(
        {
            "stem": stem,
            "ticket": """---
priority: P2
kind: feature
---

## Depends on
- none

## Context
- clutch/thing.py

## Goal / Why
`clutch/thing.py` is repaired.

## Boundary contract
none
- reason: unchanged behavior

## Scope in / Scope out
- In: `clutch/thing.py`.
- Out: unrelated files.

## Scope fence
- clutch/thing.py

## Acceptance criteria
- `uv run pytest` exits 0.

## Verification
```
uv run pytest
```

## Definition of rejected
- `clutch/thing.py` cannot be changed safely.

## Time budget
- expected: 10m
- stuck: 20m
""",
        }
    )


def run(root: Path, monkeypatch, llm: FakeLLM) -> int:
    monkeypatch.setattr("clutch.__main__.ProviderLLM", lambda *args, **kwargs: llm)
    monkeypatch.setattr("clutch.__main__.Subprocess" + "Exec", FakeExec)
    monkeypatch.setattr("clutch.__main__.Git", lambda *args, **kwargs: git_fake(root))
    return main(["box", "triage"], cwd=root, env=ENV, clock=Clock())


async def escape_rig(tmp_path):
    from clutch import runner, stages
    from clutch.tickets import validate_ticket
    from tests.drain_helpers import pause_checkout
    from tests.stages_helpers import implement_reply

    root, box = root_with_box(tmp_path)
    c = pause_checkout(root)
    # Stage readers still use Path; mirror fixture writes only inside the caller's root.
    write = c.fs.write
    remove = c.fs.remove

    def write_visible(path, data):
        write(path, data)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def remove_visible(path):
        remove(path)
        path.unlink(missing_ok=True)

    c.fs.write = write_visible
    c.fs.remove = remove_visible
    heads = {root: "1" * 40}

    def worktree_add(directory, path, branch, start):
        heads[path] = heads[directory]
        for source in list(root.rglob("*")):
            if source.is_file() and not source.is_relative_to(root / ".clutch"):
                c.fs.write(path / source.relative_to(root), source.read_bytes())

    def git_read(directory, *args):
        from clutch.git import GitError

        if args[0] == "show":
            rel = args[1].split(":", 1)[1]
            path = directory / rel
            if path in c.fs.files:
                return c.fs.read_bytes(path).decode()
            if path.is_file():
                return path.read_text()
            raise GitError(list(args), 128, "", "missing fixture path")
        return ""

    def rev_parse(directory, rev):
        from clutch.git import blob_sha

        if ":" in rev:
            return blob_sha(git_read(directory, "show", rev).encode())
        if rev == "candidate":
            return heads[c.config.worktree_root / "candidate"]
        return heads[directory]

    def commit(directory, message, *, only=()):
        heads[directory] = f"{int(heads[directory], 16) + 1:040x}"
        return heads[directory]

    def merge_squash(directory, branch, message):
        worktree = c.config.worktree_root / branch
        for path, data in list(c.fs.files.items()):
            if path.is_relative_to(worktree):
                c.fs.write(directory / path.relative_to(worktree), data)
        return commit(directory, message)

    c.git._overrides.update(
        _run=git_read,
        merge_base=lambda directory, a, b: b,
        worktree_add=worktree_add,
        rev_parse=rev_parse,
        commit=commit,
        diff_names=lambda directory, base, stem: ["clutch/thing.py", "outside.py"],
        merge_squash=merge_squash,
    )
    writer = runner.bind(c, FakeLLM([implement_reply()]))
    text = confirmed().replace("uv run pytest", "true").replace("kind: feature", "kind: feature\ngate_bypass:\n  - {code: scope_fence, reason: witnessed fixture}")
    ticket_path = root / "tickets/candidate/ticket.md"
    c.fs.write(ticket_path, text.encode())
    await c.git.add(root, ["tickets/candidate/ticket.md"])
    await c.git.commit(root, "clutch(candidate): ticket", only=["tickets/candidate/ticket.md"])
    ticket = validate_ticket("candidate", text, root)
    slip = (await stages.implement(writer.ctx, ticket, attempt=0)).artifact
    wt = writer.ctx.worktree(ticket.stem)
    for path in ("clutch/thing.py", "outside.py"):
        c.fs.write(wt / path, b"changed\n")
    await c.git.add(wt, ["clutch/thing.py", "outside.py"])
    await c.git.commit(wt, "code")
    checked = (await stages.check(writer.ctx, ticket, slip, attempt=0)).artifact
    assert checked.passed and "scope_fence" in checked.bypassed
    writer.stages.driver.llm = FakeLLM([requisition_reply("approve")])
    review = (await stages.review(writer.ctx, ticket, checked, attempt=0)).artifact
    # A process commit forces the production admission's clean-rebase approval carry.
    c.fs.write(root / "tickets/process/note.md", b"process\n")
    await c.git.add(root, ["tickets/process/note.md"])
    await c.git.commit(root, "process")
    writer.queue.offer(ticket, attempt=0)
    [admitted] = await writer.queue.process()
    assert admitted.outcome == "ok", admitted.findings
    assert admitted.artifact.reviewed_sha == review.reviewed_sha == checked.produced_at_sha
    return c, writer, box, checked, admitted.artifact


async def escape_report(c, *, commit, paths=(), stem="repair"):
    from dataclasses import replace

    from clutch import triage

    root = c.repo
    (root / "inbox").mkdir(exist_ok=True)
    (root / "replay.json").write_text(json.dumps({"initial_state": {"score": 0}, "actions": []}))
    (root / "log.txt").write_text("structured log\n")
    (root / "inbox/a.json").write_text(
        json.dumps(
            dict(
                schema_version=1,
                origin="player",
                summary="Observed scoring defect",
                app_commit=commit,
                app_version="1.2.3",
                implicated_paths=list(paths),
                evidence={"replay": "replay.json", "log": "log.txt"},
            )
        )
    )
    data = json.loads(author_reply(stem))
    data["ticket"] = data["ticket"].replace("kind: feature", "kind: bug")
    data["ticket"] = data["ticket"].replace("- clutch/thing.py\n\n## Goal", f"- clutch/thing.py\n- tickets/{stem}/evidence/replay.json\n\n## Goal")
    data["ticket"] = data["ticket"].replace("## Scope fence\n", "## Scope fence\n- tests/report_regression.py\n")
    data["ticket"] += "\n## Regression\n```\npython tests/report_regression.py\n```\n- carries: tests/report_regression.py\n"
    config = c.repo / "config.yaml"
    config.write_text(config.read_text() + "report_inbox: inbox\n")
    from clutch.config import load_config

    c = replace(c, config=load_config(None, cwd=c.repo))
    llm = FakeLLM([reply("author"), json.dumps(data), requisition_reply("approve")])
    await triage.triage_pass(c, llm)
    box = Box(c.config.state_dir / "box", c.fs)
    [message] = box.messages()
    assert message.resolution == Resolution(kind="ticket", link=stem)
    assert message.report and message.report.custody.replay
    return c, message, llm


def clock() -> datetime:
    return datetime(2026, 10, 5, tzinfo=UTC)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    from tests.stages_helpers import CONFIG, adopt_conduct

    root = tmp_path / "repo"
    (root / "clutch").mkdir(parents=True)
    (root / "clutch" / "thing.py").write_text("")
    (root / "CLUTCH_PLAN.md").write_text("# Plan\n")
    (root / "config.yaml").write_text(CONFIG)
    (root / ".gitignore").write_text(".clutch/\n")
    adopt_conduct(root)
    return root


def author(repo: Path, stem: str = TERMINAL_STEM, depends: str = "none") -> None:
    """Hand-author the ticket file only: `run` intake commits it."""
    from tests.stages_helpers import TICKET as STAGE_TICKET

    path = repo / "tickets" / stem / "ticket.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(STAGE_TICKET.format(bypass="").replace("## Depends on\nnone", f"## Depends on\n{depends}"))


def diagnosis_reply(*lessons: str) -> str:
    return json.dumps({"verdict": "retry", "lessons": list(lessons or ("Apply the terminal findings.",))})


def transitions(repo: Path) -> list[dict]:
    from tests.stages_helpers import STEM

    return [e.body for e in Journal(repo / ".clutch" / "state", clock).read() if e.type == EventType.STATE_TRANSITION and e.ticket == STEM]


async def repository(root, monkeypatch, *, prepare=None):
    """Build a restart rig using the shared in-memory I/O seams."""
    from tests.config_helpers import CONFIG
    from tests.daemon_helpers import CoreRig
    from tests.stages_helpers import adopt_conduct

    rig = CoreRig(root, prepare=prepare, config=CONFIG + "worktree_root: recovery-workspaces\n")
    process = FakeExec()
    scripted = rig.exec.run

    async def run(argv, **kwargs):
        if argv[0] == "notify-sink":
            with (root / "deliveries.jsonl").open("a") as output:
                output.write(argv[-1] + "\n")
            return (1 if (root / "notify-fails").exists() else 0, "", "")
        if argv[0] in {"git", "true"}:
            return await process.run(argv, **kwargs)
        return await scripted(argv, **kwargs)

    monkeypatch.setattr(rig.exec, "run", run)
    monkeypatch.setattr("clutch.__main__.Subprocess" + "Exec", lambda: rig.exec)
    (root / ".gitignore").write_text(".clutch/\nstate/\nrecovery-workspaces/\n")
    conduct = adopt_conduct(root)
    await rig.checkout.git.add(root, ["config.yaml", ".gitignore", "clutch/thing.py", *conduct])
    await rig.checkout.git.commit(root, "restart fixture config")
    return rig


async def orphan(rig, stem, *, intent=False, worktree=True):
    journal = rig.journal
    if intent:
        journal.append(EventType.EFFECT_INTENT, {}, ticket=stem, key=f"test/{stem}/0")
    else:
        rig.transition(stem, "running")
    path = rig.checkout.config.worktree_root / stem
    if worktree:
        path.mkdir(parents=True, exist_ok=True)
        await rig.checkout.git.worktree_add(rig.root, path, stem, "main")
        (path / "interrupted.py").write_text("unfinished")
    return path


def held(rig):
    from clutch.lockfile import Lockfile

    lock = Lockfile(rig.checkout.config.state_dir, verb="drain", instance_id="restart-test", clock=rig.time)
    lock.acquire()
    return lock


async def graph(root, monkeypatch, **kwargs):
    rig = await repository(root, monkeypatch)
    rig.exec.reply = reply("declined")
    owner = serve.Serve(
        rig.checkout,
        read=lambda stem: (root / f"tickets/{stem}/ticket.md").read_text() if (root / f"tickets/{stem}/ticket.md").is_file() else None,
        stems=lambda: (p.parent.name for p in (root / "tickets").glob("*/ticket.md")),
        **kwargs,
    )
    rig.owner = owner
    return rig


def terminals(rig, stem=None):
    return [e for e in rig.journal.read() if e.type == EventType.STATE_TRANSITION and e.body.get("to") != "running" and (stem is None or e.ticket == stem)]


async def admission_graph(root, monkeypatch, changes, *, endings=None, settled=None):
    """The merged CoreRig, actual CLI serve composition and real stages with scripted model replies."""
    from tests.stages_helpers import SNAG, implement_reply, verdict

    endings = endings if endings is not None else {}
    models, contexts, returns = [], {}, []

    class Model(FakeLLM):
        async def call(self, req):
            stem = req.subject
            if req.surface == "implement":
                for path, data in changes.get(stem, {}).items():
                    rig.fs.write(req.worktree / path, data.encode())
                if changes.get(stem):
                    await rig.checkout.git.add(req.worktree, list(changes[stem]))
                    await rig.checkout.git.commit(req.worktree, "scripted implementation")
                failed = endings.get(stem) == "implement"
                value = implement_reply(
                    "premise_failed" if failed else "already_satisfied" if endings.get(stem) == "noop" else "ok",
                    [{"code": "premise", "path": f"tickets/{stem}/ticket.md", "message": "scripted premise refusal", "paved_road": "revise this ticket"}] if failed else [],
                )
            elif req.surface == "review":
                value = verdict("snag", [SNAG]) if endings.get(stem) == "review" else verdict()
            elif req.surface == "diagnose":
                value = json.dumps({"verdict": "abandon-human", "lessons": ["inspect the admission findings"]})
            elif req.surface == "rework":
                value = json.dumps({"action": "escalate", "tickets": []})
            else:
                raise AssertionError(f"unexpected scripted surface {req.surface}")
            self.script.append(value)
            return await super().call(req)

    async def prepare(local):
        llm = Model([])
        models.append(llm)
        writer = runner.bind(local, llm)
        return writer

    rig = await graph(root, monkeypatch, prepare=prepare)
    rig.prepare, rig.models, rig.contexts, rig.returns = prepare, models, contexts, returns
    rig.fixture_confirm = True
    rig.held_returns = []
    review = stages.review

    async def reviewed(ctx, ticket, invoice, *, attempt):
        result = await review(ctx, ticket, invoice, attempt=attempt)
        contexts[ticket.stem] = ctx
        if result.outcome == "ok" and settled is not None:
            await settled(rig, ctx, ticket, attempt)
        return result

    monkeypatch.setattr(stages, "review", reviewed)
    drive = runner.drive

    async def driving(ctx, ticket, **kwargs):
        result = await drive(ctx, ticket, **kwargs)
        (rig.held_returns if result == "running" else returns).append((ticket.stem, result))
        return result

    monkeypatch.setattr(runner, "drive", driving)
    consume = TicketWriter.consume_result

    async def consumed(writer, ticket, result, *, attempt):
        live = (ticket.stem, attempt) in writer.admission.results
        await consume(writer, ticket, result, attempt=attempt)
        if not live:
            terminal = terminals(rig, ticket.stem)[-1].body["to"]
            returns.append((ticket.stem, terminal))

    monkeypatch.setattr(TicketWriter, "consume_result", consumed)
    return rig


def admission_config(root, *, command=None, safety=False, strategies=()):
    amend_config(
        root,
        review={"mechanical": [{"code": "combined", "argv": command or ["true"], "trigger": "always", "severity": "hard"}]},
        merge={"safety_checks": ["combined"] if safety else [], "strategies": list(strategies)},
    )


def notify_command(root, *, enabled=True):
    amend_config(root, notify=["notify-sink"] if enabled else None)


class UpgradeChild:
    def __init__(self, rig):
        self.rig = rig
        self.calls = []

    async def replace(self, argv, *, cwd, env):
        lock = Lockfile(self.rig.checkout.config.state_dir, verb="drain", instance_id="probe", clock=self.rig.time)
        lock.acquire()
        lock.release()
        self.calls.append((list(argv), cwd, env))
        return 7


async def enable_upgrade(rig, engine):
    (engine / "clutch/specs").mkdir(parents=True, exist_ok=True)
    (engine / "clutch/specs/base.md").write_text("base")
    await rig.checkout.git.add(engine, ["clutch/specs/base.md"])
    await rig.checkout.git.commit(engine, "engine trees")
    rig.owner.engine = engine
    rig.owner.reexec = UpgradeChild(rig)
    rig.owner.argv = ("--config", "config.yaml", "serve")
