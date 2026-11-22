"""Shared scheduler test scaffolding."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared scheduler test scaffolding: fake clock, ticket text builder, scheduler/watcher Rig and the CLI import-closure walker
# relates: [clutch/config.py, clutch/journal.py, clutch/scheduler.py, clutch/seams.py, clutch/tickets.py, clutch/watcher.py, tests/cli_helpers.py]
# owner: engine
# verified: 82d23237
# hash: 01c26d08bbcde7c62ed86e60e7013510b7d72a089c197686190bd42a0f9fc722

import ast
import asyncio
from datetime import UTC, datetime, timedelta

from clutch.config import Caps
from clutch.journal import EventType, Journal
from clutch.scheduler import Scheduler
from clutch.seams import LocalFileSystem
from clutch.tickets import INTAKE_SIGNAL, parse_ticket
from clutch.watcher import Watcher
from tests.cli_helpers import TICKET
from tests.dispatch_settle import dispatch_settled
from tests.fakes import turn


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
