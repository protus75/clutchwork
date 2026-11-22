"""Shared daemon and merge-queue scaffolding over the in-memory test seams."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared daemon and merge-queue test scaffolding over in-memory fake seams: CoreRig, LiveDrain, the ctx and tickets fixtures, ticket readiness and approval, conflict setup, scripted host checks, pause-consumer construction, and import-closure and wiring assertions.
# relates: [clutch/__main__.py, clutch/caps.py, clutch/config.py, clutch/control.py, clutch/daemon.py, clutch/drain.py, clutch/driver.py, clutch/git.py]
# owner: engine
# verified: f98b9306
# hash: b44c538c53c90264929c33eb11273ecdcdaf63169713642a4f1700774befb19d

import ast
import asyncio
import dataclasses
import json
from dataclasses import replace
from pathlib import Path

import pytest

from clutch import __main__ as cli
from clutch import daemon, runner, stages
from clutch.config import MechanicalCheck, RegenerateStrategy, UnionStrategy, load_config
from clutch.daemon import DaemonAdmission, PauseConsumer
from clutch.driver import Driver
from clutch.git import blob_sha
from clutch.journal import EventType
from clutch.llm import FakeLLM
from clutch.mergequeue import CONFLICT_FACTS, MergeQueue
from clutch.scheduler import Scheduler
from clutch.stages import ApprovedInvoice, StageContext, render_review
from clutch.tickets import INTAKE_SIGNAL, parse_ticket, validate_ticket
from clutch.watcher import Watcher
from tests.cli_helpers import CONFIG as CLI_CONFIG
from tests.cli_helpers import ticket, write
from tests.dispatch_settle import dispatch_settled
from tests.fakes import FakeClock, FakeExec, FakeFileSystem, FakeJournal, turn
from tests.git_fake import GitFake
from tests.integration.test_providers import CONFIG as PROVIDERS_CONFIG
from tests.stages_helpers import CONFIG, ENV, SECRET, SPECS, STEM, TICKET, adopt_conduct


class CoreRig:
    def __init__(self, root, *, prepare=None, config=PROVIDERS_CONFIG, config_path=None):
        self.root = root
        (root / "clutch").mkdir(exist_ok=True)
        (root / "clutch/thing.py").write_text("")
        self.config_path = config_path
        self.put_config(config)
        self.time = FakeClock()
        self.fs = FakeFileSystem()
        self.exec = FakeExec()
        self.journal = FakeJournal(self.time)
        initial = load_config(config_path, cwd=root)

        async def sleep(seconds):
            self.time.advance(seconds)
            await turn()

        self.checkout = runner.Checkout(
            root,
            initial,
            ENV,
            self.exec,
            GitFake(rev_parse="a" * 40),
            self.journal,
            self.fs,
            self.time,
            sleep,
        )
        self.files = {}
        self.quarantine, self.drought = set(), set()
        self.unmerged = 0
        self.calls, self.locals = [], []
        kwargs = {} if prepare is None else {"prepare": prepare}
        self.core = cli.build_daemon_core(
            self.checkout,
            config_path=config_path,
            read=self.files.get,
            debounce=5,
            quarantined=lambda: self.quarantine,
            drought_parked=lambda: self.drought,
            completed_unmerged=lambda: self.unmerged,
            **kwargs,
        )

        self.core.control.inbox.files = lambda: (self.checkout.config.state_dir / "control/inbox" / name for name in self.fs.entries(self.checkout.config.state_dir / "control/inbox"))
        self.core.control.inbox.read = self.fs.read_bytes

    def put_config(self, config):
        (self.config_path or self.root / "config.yaml").write_text(config)

    async def publish(self, *stems):
        async def changes():
            for stem in stems:
                yield stem

        consumer = asyncio.create_task(self.core.watcher.run(changes()))
        await turn()
        await turn()
        self.time.advance(5)
        await consumer

    async def add(self, stem, priority="P2", state="confirmed", depends="none"):
        self.files[stem] = ticket(depends).replace("priority: P2", f"state: {state}\nsource: human\npriority: {priority}", 1)
        write(self.root, stem, self.files[stem])
        await self.publish(stem)
        return self.core.scheduler.pending[stem]

    def transition(self, stem, to, **body):
        self.journal.append(EventType.STATE_TRANSITION, {"to": to, **body}, ticket=stem)

    def intake(self, stem):
        self.journal.append(EventType.SIGNAL, {"signal": INTAKE_SIGNAL, "source": "human", "state": "confirmed", "new": True, "commit": "abc"}, ticket=stem)

    async def drain(self):
        while await dispatch_settled(self.core.scheduler) is not None:
            pass


def assert_core_wiring(rig):
    core = rig.core
    assert isinstance(core.admission, DaemonAdmission)
    assert isinstance(core.scheduler, Scheduler) and isinstance(core.watcher, Watcher)
    assert core.scheduler.journal is core.watcher.journal is rig.checkout.journal
    assert core.scheduler.dispatch == core.admission.dispatch
    assert core.watcher.publish == core.scheduler.update
    assert core.watcher.remove == core.scheduler.remove
    assert core.watcher.read == rig.files.get
    assert core.watcher.clock is rig.checkout.clock and core.watcher.sleep == rig.checkout.sleep
    assert core.watcher.debounce == 5
    assert core.scheduler.max_unmerged == rig.checkout.config.scheduler.max_unmerged


def assert_startup_pause_wiring(core):
    boundary = core.admission._before_dispatch
    assert boundary is not None
    assert isinstance(boundary.__self__, daemon.StartupBoundary)
    assert boundary == boundary.__self__.checkpoint
    assert boundary.__self__.restart is core.restart
    assert boundary.__self__.pause is core.control


def capture_pipeline_queue(monkeypatch):
    captured = []
    compose = runner.compose_pipeline

    def recording(ctx, *, escalate, control):
        queue = compose(ctx, escalate=escalate, control=control)
        captured.append((ctx, escalate, queue))
        return queue

    monkeypatch.setattr(runner, "compose_pipeline", recording)
    return captured


def sources():
    root = Path(__file__).resolve().parents[1]
    material = {".".join(p.relative_to(root).with_suffix("").parts): p.read_text() for p in (root / "clutch").rglob("*.py")}
    material["clutch"] = material.pop("clutch.__init__")
    return material


def without_core_import(material):
    main = ast.parse(material["clutch.__main__"])
    assert any(
        isinstance(node, ast.ImportFrom) and node.module == "clutch.daemon" and {"DaemonCore", "PauseConsumer", "daemon_core"} <= {alias.name for alias in node.names} for node in ast.walk(main)
    )

    class RemoveDaemon(ast.NodeTransformer):
        def visit_Import(self, node):
            return ast.copy_location(ast.Pass(), node) if any(alias.name == "clutch.daemon" for alias in node.names) else node

        def visit_ImportFrom(self, node):
            target = node.module == "clutch.daemon" or (node.module == "clutch" and any(alias.name == "daemon" for alias in node.names))
            return ast.copy_location(ast.Pass(), node) if target else node

    return {name: ast.unparse(RemoveDaemon().visit(ast.parse(source))) for name, source in material.items()}


def production_writer(source, script):
    """Reuse the production bind and its queue with the disposable admission repository."""
    checkout = runner.Checkout(source.repo, source.config, source.env, source.exec_, source.git, source.driver.journal, source.fs, source.driver.clock, source.driver.sleep)
    checkout = replace(checkout, control=cli.build_control(checkout))
    checkout.control.inbox.files = lambda: (checkout.config.state_dir / "control/inbox" / name for name in checkout.fs.entries(checkout.config.state_dir / "control/inbox"))
    checkout.control.inbox.read = checkout.fs.read_bytes
    writer = runner.bind(checkout, FakeLLM(script))
    return checkout, writer


class LiveDrain:
    """The real drain and CLI control factory, with filesystem traces and barrier wakeups."""

    def __init__(self, root, monkeypatch, *, pause=True):
        from clutch.control import ControlRequest, publish_request
        from clutch.lockfile import Lockfile, LockHeld
        from tests.cli_helpers import ENV as checkout_env

        process = FakeExec()
        clock = FakeClock()
        self.checkout = runner.Checkout(
            root,
            load_config(None, cwd=root),
            checkout_env,
            process,
            GitFake(describe="live-drain"),
            FakeJournal(clock),
            FakeFileSystem(),
            clock,
        )
        self.trace, self.consumers, self.calls = [], [], []
        self.pause = pause
        self.held = asyncio.Queue()
        self.wake = asyncio.Queue()
        original_acquire, original_release = Lockfile.acquire, Lockfile.release

        def acquire(lock):
            original_acquire(lock)
            self.trace.append("lock")

        def release(lock):
            self.trace.append("unlock")
            original_release(lock)

        monkeypatch.setattr(Lockfile, "acquire", acquire)
        monkeypatch.setattr(Lockfile, "release", release)
        original = cli.build_control

        def build(checkout):
            assert checkout is self.checkout
            consumer = original(checkout)
            self.consumers.append(consumer)
            consume = consumer.inbox.consume

            def consumed():
                self.trace.append("consume")
                consume()

            consumer.inbox.consume = consumed
            return consumer

        monkeypatch.setattr(cli, "build_control", build)
        append = self.checkout.journal.append

        def appended(*args, **kwargs):
            event = append(*args, **kwargs)
            if event.body.get("kind") == "control_decision":
                self.trace.append(("decision", event.body.copy()))
            return event

        monkeypatch.setattr(self.checkout.journal, "append", appended)
        fs = self.checkout.fs
        write_file = fs.write

        def written(path, data):
            if path == self.checkout.config.state_dir / "control/active.json":
                contender = Lockfile(self.checkout.config.state_dir, verb="drain", instance_id="trace", clock=self.checkout.clock)
                with pytest.raises(LockHeld):
                    contender.acquire()
                assert self.trace[0] == "lock" and "unlock" not in self.trace
                if data != b"null\n":
                    value = json.loads(data)
                    if value["hold_id"] is not None:
                        assert any(e.body.get("request_id") == value["hold_id"] and e.body.get("decision") == "accepted" for e in self.checkout.journal.read())
                self.trace.append(("discovery", json.loads(data)))
            write_file(path, data)
            if path.name == "active.json" and data != b"null\n" and self.pause:
                self.pause = False
                publish_request(self.checkout.config.state_dir, ControlRequest("10-pause", json.loads(data)["lifecycle_id"], "pause", None), fs)

        monkeypatch.setattr(fs, "write", written)

        async def sleep(delay):
            assert delay > 0
            await self.held.put(self.consumer.projection)
            await self.wake.get()

        self.checkout = replace(self.checkout, fs=fs, sleep=sleep, control=None)
        self.checkout = replace(self.checkout, control=cli.build_control(self.checkout))
        self.consumer.inbox.files = lambda: (self.checkout.config.state_dir / "control/inbox" / name for name in fs.entries(self.checkout.config.state_dir / "control/inbox"))
        self.consumer.inbox.read = fs.read_bytes

    @property
    def consumer(self):
        return self.consumers[-1]

    def request(self, id, verb, hold=None, life=None):
        from clutch.control import ControlRequest, publish_request

        publish_request(self.checkout.config.state_dir, ControlRequest(id, life or self.consumer.inbox.lifecycle_id, verb, hold), self.checkout.fs)
        self.wake.put_nowait(None)

    async def resume(self):
        self.request("90-resume", "resume", self.consumer.projection.pause_id)

    async def run(self, dispatch=None, reexec=None, before_dispatch=None):
        from clutch.drain import drain
        from tests.drain_helpers import NoChild

        async def callback(ticket):
            self.calls.append(ticket.stem)
            self.trace.append("dispatch")
            self.checkout.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket=ticket.stem)
            return "merged"

        return await drain(self.checkout, dispatch or callback, reexec=reexec or NoChild(), before_dispatch=before_dispatch)


@pytest.fixture
def ctx(tmp_path):
    repo = tmp_path / "repo"
    (repo / "clutch").mkdir(parents=True)
    (repo / "clutch/thing.py").write_text("ok base\n")
    (repo / "clutch/other.py").write_text("")
    (repo / "CLUTCH_PLAN.md").write_text("# Plan\n")
    (repo / ".gitignore").write_text(".clutch/\n")
    (repo / "config.yaml").write_text(CONFIG)
    conduct = adopt_conduct(repo)
    config = load_config(None, cwd=repo)
    exec_ = FakeExec()
    clock = FakeClock()
    fs = FakeFileSystem()
    for rel in ["clutch/thing.py", "clutch/other.py", "config.yaml", "CLUTCH_PLAN.md", ".gitignore", *conduct]:
        fs.write(repo / rel, (repo / rel).read_bytes())
    driver = Driver.from_config(
        config,
        journal=FakeJournal(clock),
        llm=FakeLLM([]),
        env=ENV,
        clock=clock,
        sleep=lambda _: turn(),
        fs=fs,
    )
    context = StageContext(repo, config, ENV, exec_, GitFake(rev_parse="a" * 40, commit="b" * 40), fs, driver, SPECS)

    async def init():
        await context.git.init(repo, branch="main")
        await context.git.add(repo, [".gitignore", "config.yaml", "CLUTCH_PLAN.md", "clutch", *conduct])
        await context.git.commit(repo, "base")

    asyncio.run(init())
    return context


async def commit(ctx, root, paths, message="work"):
    await ctx.git.add(root, paths)
    await ctx.git.commit(root, message)


async def approve(ctx, ticket, sha=None):
    sha = sha or await ctx.git.rev_parse(ctx.repo, ticket.stem)
    review = ApprovedInvoice(
        produced_by_spec_version=1, produced_at_sha=sha, stem=ticket.stem, reviewed_sha=sha, verdict="approve", summary="approved", findings=[], spec_version="1.0", provider="fake", model="fake"
    )
    path = f"tickets/{ticket.stem}/review.md"
    ctx.fs.write(ctx.repo / path, render_review(review).encode())
    await commit(ctx, ctx.repo, [path], "review")


async def ready(ctx, stem=STEM, *, changes=None, fence=("clutch/thing.py",), verification=(("true",),), priority="P2", lifted=False, commits=None):
    text = TICKET.format(bypass="").replace("priority: P2", f"priority: {priority}")
    text = text.replace("## Scope fence\n- clutch/thing.py", "## Scope fence\n" + "\n".join("- " + f for f in fence))
    root = ctx.repo / "tickets" / stem
    ctx.fs.write(root / "ticket.md", text.encode())
    record = "".join(f"## {name}\n\n{'ok' if name == 'Outcome' else 'none'}\n\n" for name in stages.RUN_RECORD_SECTIONS)
    ctx.fs.write(root / "run.md", record.encode())
    await commit(ctx, ctx.repo, [f"tickets/{stem}"], "ticket and run record")
    ticket = dataclasses.replace(validate_ticket(stem, text, ctx.repo), verification=verification)
    from clutch.caps import capability
    from clutch.requisition import review_input_identity

    history = ctx.driver.journal.read()
    identity = await review_input_identity(ctx.repo, text, ticket, ctx.config, ctx.git, ctx.specs_dir, None, history, tier=capability(ticket, history)[0])
    ctx.driver.journal.append(
        EventType.SIGNAL,
        {"signal": "requisition_verdict", "verdict": "approve", "ticket_sha": blob_sha(text.encode()), "provider": "fixture", "model": "fixture", "spec_version": "1.0", "input_identity": identity},
        ticket=stem,
    )
    await ctx.git.worktree_add(ctx.repo, ctx.worktree(stem), stem, "main")
    for batch in commits or [changes or {"clutch/thing.py": f"ok {stem}\n"}]:
        for path, data in batch.items():
            ctx.fs.write(ctx.worktree(stem) / path, data.encode())
        await commit(ctx, ctx.worktree(stem), list(batch))
    await approve(ctx, ticket)
    if lifted:
        ctx.fs.remove(ctx.worktree(stem) / "tickets" / stem / "run.md")
    return ticket


async def admission(ctx, ticket, *, queue=None, attempt=0):
    queue = queue or MergeQueue(ctx, escalate=lambda _: None)
    queue.offer(ticket, attempt=attempt)
    [result] = await queue.process()
    return result


def facts(ctx):
    return [e for e in ctx.driver.journal.read() if e.body.get("kind") == CONFLICT_FACTS]


def host(code, *, trigger="always", severity="hard", argv=None):
    return MechanicalCheck(code=code, argv=argv or ["host", code], trigger=trigger, severity=severity)


def scripted(ctx, monkeypatch, results):
    original = ctx.exec_.run
    calls = []

    async def execute(argv, **kw):
        if argv[0] == "host":
            calls.append((list(argv), kw))
            value = results.pop(0)
            if isinstance(value, BaseException):
                raise value
            return value
        return await original(argv, **kw)

    monkeypatch.setattr(ctx.exec_, "run", execute)
    return calls


def admission_control(ctx, lifecycle="admission-life", *, known):
    return PauseConsumer(
        journal=ctx.driver.journal,
        lifecycle_id=lifecycle,
        known=known,
        state_dir=ctx.config.state_dir,
        fs=ctx.fs,
        sleep=ctx.driver.sleep,
        files=lambda: (ctx.config.state_dir / "control/inbox" / name for name in ctx.fs.entries(ctx.config.state_dir / "control/inbox")),
        read=ctx.fs.read_bytes,
    )


async def conflict(ctx, *, strategy="union", generator=None, fence=("clutch/thing.py",), repeat=False):
    generated = "clutch/generated.txt"
    paths = [generated, "clutch/generated-two.txt"] if repeat else [generated]
    for path in paths:
        ctx.fs.write(ctx.repo / path, b"base\n")
    await commit(ctx, ctx.repo, paths)
    ticket = await ready(ctx, fence=fence, commits=[{"clutch/thing.py": "ok work\n", generated: "base\nbranch-one\n"}, *([{paths[1]: "base\nbranch-two\n"}] if repeat else [])])
    for path in paths:
        ctx.fs.write(ctx.repo / path, b"base\nmain\n")
    await commit(ctx, ctx.repo, paths, "main conflicts")
    if strategy == "union":
        ctx.config.merge.strategies = [UnionStrategy(paths=paths, strategy="union")]
    elif strategy == "regenerate":
        ctx.config.merge.strategies = [
            RegenerateStrategy(paths=paths, strategy="regenerate", argv=generator or ["python3", "-c", "from pathlib import Path; Path('clutch/generated.txt').write_text('regenerated\\n')"])
        ]
    return ticket, generated


def import_closure(root, sources):
    pending, reached = [root], set()
    while pending:
        module = pending.pop()
        if module in reached:
            continue
        reached.add(module)
        tree = ast.parse(sources.get(module, ""))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                pending.extend(a.name for a in node.names if a.name.startswith("clutch."))
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("clutch."):
                    pending.append(node.module)
                elif node.module == "clutch":
                    pending.extend("clutch." + a.name for a in node.names if "clutch." + a.name in sources)
    return reached


@pytest.fixture
def tickets(tmp_path):
    (tmp_path / "clutch").mkdir()
    (tmp_path / "clutch/thing.py").write_text("")
    text = ticket().replace("priority: P2", "state: confirmed\nsource: human\npriority: P2", 1)
    return tuple(parse_ticket(stem, text, tmp_path) for stem in ("first", "second"))


def assert_idle(admission):
    assert not admission.occupied()
    assert not admission.occupied()


def assert_reachable(sources):
    pending, reached = ["clutch.__main__", "clutch"], set()
    while pending:
        module = pending.pop()
        if module in reached or module not in sources:
            continue
        reached.add(module)
        for node in ast.walk(ast.parse(sources[module])):
            if isinstance(node, ast.Import):
                pending.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                pending.append(node.module)
                pending.extend(f"{node.module}.{alias.name}" for alias in node.names)
    assert "clutch.daemon" in reached
