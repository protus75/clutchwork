"""Daemon scaffolding contracts with temporary checkouts and shared fake seams."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests the contracts of the shared daemon test helpers (CoreRig, LiveDrain, ctx, approval, conflict, import-closure and wiring assertions) against fake seams and temporary checkouts.
# relates: [clutch/control.py, clutch/daemon.py, clutch/journal.py, clutch/requisition.py, clutch/runner.py, clutch/stages.py, tests/daemon_helpers.py]
# owner: tests/daemon_helpers.py
# verified: f98b9306
# hash: f45a9af3d904990969c12cb9b33cf7cbd9eaa780def3fdfc33e08eeca0838d28

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import runner
from clutch.control import ControlRequest, publish_request
from clutch.daemon import DaemonAdmission
from clutch.journal import EventType
from clutch.lockfile import Lockfile
from clutch.stages import read_review
from tests import daemon_helpers as h
from tests import fakes
from tests.git_fake import GitFake


@pytest.fixture
def context(tmp_path):
    return h.ctx.__wrapped__(tmp_path)


@pytest.fixture
def identity(monkeypatch):
    # The identity owner reads shipped specs; this unit exercises its caller.
    import clutch.requisition

    value = AsyncMock(return_value="fixture-identity")
    monkeypatch.setattr(clutch.requisition, "review_input_identity", value)
    return value


def test_all_names_importable():
    names = "CoreRig LiveDrain admission admission_control approve assert_core_wiring assert_idle assert_reachable assert_startup_pause_wiring capture_pipeline_queue commit conflict ctx facts host import_closure production_writer ready scripted sources tickets turn without_core_import".split()
    # Rules out an incomplete extraction or accidental non-callable re-export.
    assert [name for name in names if callable(getattr(h, name, None))] == names


def test_core_rig(tmp_path, monkeypatch):
    writes = []
    write_bytes, write_text = Path.write_bytes, Path.write_text

    def record_bytes(path, data, *args, **kwargs):
        writes.append(path)
        return write_bytes(path, data, *args, **kwargs)

    def record_text(path, data, *args, **kwargs):
        writes.append(path)
        return write_text(path, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_bytes", record_bytes)
    monkeypatch.setattr(Path, "write_text", record_text)
    rig = h.CoreRig(tmp_path)
    # Rules out replacing the providers config with the CLI helper's default.
    assert (rig.checkout.config.state_dir, (tmp_path / "config.yaml").read_text()) == (tmp_path / "state", h.PROVIDERS_CONFIG)
    added = asyncio.run(rig.add("special", priority="P1"))
    rig.transition("special", "running")
    rig.intake("special")
    # Rules out the real journal/process rig and losing the caller's ticket priority.
    assert (
        bool(writes),
        all(path.is_relative_to(tmp_path) for path in writes),
        isinstance(rig.fs, fakes.FakeFileSystem),
        isinstance(rig.exec, fakes.FakeExec),
        isinstance(rig.time, fakes.FakeClock),
        isinstance(rig.journal, fakes.FakeJournal),
        isinstance(rig.checkout.git, GitFake),
        added.stem,
        added.frontmatter.priority,
        [e.body.get("to", e.body.get("signal")) for e in rig.journal.read()][-2:],
    ) == (True, True, True, True, True, True, True, "special", "P1", ["running", "ticket_intake"])


def test_live_drain(tmp_path, monkeypatch):
    (tmp_path / "config.yaml").write_text(h.CLI_CONFIG)
    rig = h.LiveDrain(tmp_path, monkeypatch)
    lock = Lockfile(rig.checkout.config.state_dir, verb="drain", instance_id="owner", clock=rig.checkout.clock)
    lock.acquire()
    try:
        rig.consumer.publish()
        rig.consumer.poll()
        asyncio.run(rig.resume())
        rig.consumer.poll()
    finally:
        lock.release()
    # Rules out a disk inbox (which cannot see fake requests), and a real executor/git.
    assert (
        isinstance(rig.checkout.exec_, fakes.FakeExec),
        isinstance(rig.checkout.git, GitFake),
        isinstance(rig.checkout.fs, fakes.FakeFileSystem),
        isinstance(rig.checkout.journal, fakes.FakeJournal),
        [e.body.get("request_id") for e in rig.checkout.journal.read() if e.body.get("decision") == "accepted"],
        "10-pause" in rig.consumer.projection.released_hold_ids,
    ) == (True, True, True, True, ["10-pause", "90-resume"], True)


@pytest.mark.parametrize("defect", ["lock", "first-write", "unlocked", "hold-id", "decision"])
def test_live_drain_rejects_invalid_discovery(tmp_path, monkeypatch, defect):
    (tmp_path / "config.yaml").write_text(h.CLI_CONFIG)
    rig = h.LiveDrain(tmp_path, monkeypatch, pause=False)
    lock = Lockfile(rig.checkout.config.state_dir, verb="drain", instance_id="owner", clock=rig.checkout.clock)
    lock.acquire()
    try:
        hold = "chosen-hold" if defect in {"hold-id", "decision"} else None
        rig.checkout.journal.append(EventType.SIGNAL, {"request_id": "other-hold" if defect == "hold-id" else hold, "decision": "rejected" if defect == "decision" else "accepted"})
        if defect == "lock":
            monkeypatch.setattr(Lockfile, "acquire", lambda _: None)
        elif defect == "first-write":
            rig.trace.insert(0, "premature-write")
        elif defect == "unlocked":
            rig.trace.append("unlock")
        # Each case rules out dropping its corresponding discovery invariant;
        # journal rows vary only the hold identity or acceptance decision.
        with pytest.raises((AssertionError, pytest.fail.Exception)):
            rig.checkout.fs.write(rig.checkout.config.state_dir / "control/active.json", json.dumps({"lifecycle_id": "life", "hold_id": hold}).encode())
    finally:
        lock.release()


def test_ctx(context):
    # Rules out a real repository and omitting any of the three setup Git calls.
    assert (
        isinstance(context.git, GitFake),
        [call[0] for call in context.git.calls],
        (context.repo / ".git").exists(),
        isinstance(context.exec_, fakes.FakeExec),
        isinstance(context.fs, fakes.FakeFileSystem),
        isinstance(context.driver.journal, fakes.FakeJournal),
        context.fs.read_bytes(context.repo / "clutch/thing.py"),
    ) == (True, ["init", "add", "commit"], False, True, True, True, b"ok base\n")


def test_commit(context):
    context.git.calls.clear()
    asyncio.run(h.commit(context, context.repo, ["chosen"], "chosen message"))
    # Rules out adding all files, the wrong directory, or dropping the message.
    assert context.git.calls == [("add", (context.repo, ["chosen"]), {}), ("commit", (context.repo, "chosen message"), {})]


def test_approve(context):
    ticket = SimpleNamespace(stem="invoice")
    asyncio.run(h.approve(context, ticket, "explicit-sha"))
    review = read_review(context.fs.read_bytes(context.repo / "tickets/invoice/review.md").decode())
    # Rules out using the fake's HEAD instead of the requested approval SHA.
    assert (review.stem, review.reviewed_sha, review.verdict, context.git.calls[-1]) == (
        "invoice",
        "explicit-sha",
        "approve",
        ("commit", (context.repo, "review"), {}),
    )


def test_ready(context, identity):
    ticket = asyncio.run(h.ready(context, "chosen", priority="P1", changes={"clutch/thing.py": "special change"}, verification=(("special",),)))
    # Rules out ignoring overrides, missing branch setup, or dropping ticket approval.
    assert (
        ticket.stem,
        ticket.frontmatter.priority,
        ticket.verification,
        context.fs.read_bytes(context.worktree("chosen") / "clutch/thing.py"),
        [call for call in context.git.calls if call[0] == "worktree_add"],
        context.driver.journal.read()[-1].body["input_identity"],
        identity.await_count,
    ) == ("chosen", "P1", (("special",),), b"special change", [("worktree_add", (context.repo, context.worktree("chosen"), "chosen", "main"), {})], "fixture-identity", 1)


def test_admission(context):
    calls = []
    result = object()
    queue = SimpleNamespace(offer=lambda ticket, **kwargs: calls.append((ticket, kwargs)), process=AsyncMock(return_value=[result]))
    ticket = object()
    actual = asyncio.run(h.admission(context, ticket, queue=queue, attempt=7))
    # Rules out constructing another queue or losing the attempt identity.
    assert (actual, calls, queue.process.await_count) == (result, [(ticket, {"attempt": 7})], 1)


def test_facts(context):
    journal = context.driver.journal
    journal.append(EventType.SIGNAL, {"kind": "unrelated"})
    wanted = journal.append(EventType.SIGNAL, {"kind": h.CONFLICT_FACTS})
    # Both rows are signals: selecting by type or returning all events is wrong.
    assert h.facts(context) == [wanted]


def test_host():
    value = h.host("special", trigger=["clutch/special.py"], severity="soft", argv=["special-command"])
    # Rules out using any of the defaults in place of explicit host-check fields.
    assert (value.code, value.trigger, value.severity, value.argv) == ("special", ["clutch/special.py"], "soft", ["special-command"])


def test_scripted(context, monkeypatch):
    context.exec_.result = (8, "fallback", "stderr")
    results = [(3, "scripted", "detail"), ValueError("host error")]
    calls = h.scripted(context, monkeypatch, results)

    async def exercise():
        kw = dict(cwd=context.repo, env={"SPECIAL": "yes"}, timeout=17)
        special = await context.exec_.run(["host", "special"], **kw)
        fallback = await context.exec_.run(["other"], **kw)
        with pytest.raises(ValueError, match="host error"):
            await context.exec_.run(["host", "error"], **kw)
        return special, fallback, kw

    special, fallback, kw = asyncio.run(exercise())
    # Rules out consuming the script for non-host commands or losing forwarded kwargs.
    assert (special, fallback, calls, context.exec_.calls) == ((3, "scripted", "detail"), (8, "fallback", "stderr"), [(["host", "special"], kw), (["host", "error"], kw)], [["other"]])


def test_admission_control(context):
    consumer = h.admission_control(context, "special-life", known=lambda _: False)
    publish_request(context.config.state_dir, ControlRequest("pause-request", "special-life", "pause", None), context.fs)
    consumer.poll()
    # Rules out scanning/reading the on-disk inbox instead of the shared fake.
    assert (consumer.projection.lifecycle_id, consumer.projection.pause_id, consumer.inbox.journal is context.driver.journal) == ("special-life", "pause-request", True)


@pytest.mark.parametrize("strategy", ["union", "regenerate"])
def test_conflict(context, identity, strategy):
    ticket, path = asyncio.run(h.conflict(context, strategy=strategy, repeat=True, generator=["special-generator"]))
    selected = context.config.merge.strategies[0]
    # Rules out missing the second branch, swapping main/branch bytes, or ignoring strategy.
    assert (
        ticket.stem,
        path,
        selected.strategy,
        selected.paths,
        context.fs.read_bytes(context.repo / path),
        context.fs.read_bytes(context.worktree(ticket.stem) / path),
        context.fs.read_bytes(context.worktree(ticket.stem) / "clutch/generated-two.txt"),
        getattr(selected, "argv", None),
    ) == (
        h.STEM,
        "clutch/generated.txt",
        strategy,
        ["clutch/generated.txt", "clutch/generated-two.txt"],
        b"base\nmain\n",
        b"base\nbranch-one\n",
        b"base\nbranch-two\n",
        ["special-generator"] if strategy == "regenerate" else None,
    )


def test_import_closure():
    material = {
        "clutch.start": "from clutch import indirect\nimport clutch.direct\nimport outside",
        "clutch.indirect": "from clutch.leaf import item",
        "clutch.direct": "import clutch.start",
        "clutch.leaf": "",
        "clutch.unused": "",
    }
    # Rules out missing direct/from imports, following outside modules, or including unreachable ones.
    assert h.import_closure("clutch.start", material) == {"clutch.start", "clutch.indirect", "clutch.direct", "clutch.leaf"}


def test_tickets(tmp_path):
    first, second = h.tickets.__wrapped__(tmp_path)
    # Rules out duplicate stems, unconfirmed tickets, or a missing context file.
    assert (first.stem, second.stem, first.frontmatter.state, second.frontmatter.state, (tmp_path / "clutch/thing.py").read_text()) == ("first", "second", "confirmed", "confirmed", "")


def test_turn():
    async def exercise():
        calls = []
        asyncio.get_running_loop().call_soon(calls.append, "callback")
        await h.turn()
        return calls

    # Rules out a second polling helper or an async no-op that never yields.
    assert (h.turn is fakes.turn, asyncio.run(exercise())) == (True, ["callback"])


def test_assert_idle():
    admission = DaemonAdmission(AsyncMock())
    h.assert_idle(admission)
    admission.runs["occupied"] = object()
    # Rules out an assertion helper that silently accepts an occupied admission.
    with pytest.raises(AssertionError):
        h.assert_idle(admission)


def test_assert_reachable():
    h.assert_reachable({"clutch.__main__": "from clutch import indirect", "clutch.indirect": "import clutch.daemon", "clutch.daemon": ""})
    # Rules out checking only the presence of the daemon source, rather than reachability.
    with pytest.raises(AssertionError):
        h.assert_reachable({"clutch.__main__": "", "clutch.daemon": ""})


def test_assert_core_wiring(tmp_path):
    rig = h.CoreRig(tmp_path)
    h.assert_core_wiring(rig)
    rig.core.watcher.publish = lambda _: None
    # Rules out dropping the watcher-to-scheduler binding assertion.
    with pytest.raises(AssertionError):
        h.assert_core_wiring(rig)


def test_assert_startup_pause_wiring(tmp_path):
    rig = h.CoreRig(tmp_path)
    h.assert_startup_pause_wiring(rig.core)
    rig.core.admission._before_dispatch.__self__.pause = object()
    # Rules out accepting a boundary bound to another pause consumer.
    with pytest.raises(AssertionError):
        h.assert_startup_pause_wiring(rig.core)


def test_capture_pipeline_queue(context, monkeypatch):
    calls = []
    queue = object()

    def compose(ctx, **kwargs):
        calls.append((ctx, kwargs))
        return queue

    monkeypatch.setattr(runner, "compose_pipeline", compose)
    captured = h.capture_pipeline_queue(monkeypatch)
    escalation, control = object(), object()
    actual = runner.compose_pipeline(context, escalate=escalation, control=control)
    # Rules out recording a different queue or failing to forward the control binding.
    assert (actual, captured, calls) == (queue, [(context, escalation, queue)], [(context, {"escalate": escalation, "control": control})])


def test_production_writer(context):
    checkout, writer = h.production_writer(context, [])
    # Rules out constructing fresh seams or bypassing the production queue binding.
    assert (checkout.git, checkout.exec_, checkout.fs, checkout.journal, writer.ctx.git, writer.queue.ctx.fs, writer.queue.control) == (
        context.git,
        context.exec_,
        context.fs,
        context.driver.journal,
        context.git,
        context.fs,
        checkout.control,
    )


def test_without_core_import():
    material = {
        "clutch.__main__": "from clutch.daemon import (DaemonCore, PauseConsumer, daemon_core)\nfrom clutch.other import keep",
        "clutch.nested": "def nested():\n import clutch.daemon as d\n from clutch import daemon as d\n return 7",
        "clutch.other": "value = 9",
    }
    removed = h.without_core_import(material)
    # Rules out deleting other imports or missing either nested daemon import spelling.
    assert (removed["clutch.__main__"], removed["clutch.nested"], removed["clutch.other"], material["clutch.other"]) == (
        "pass\nfrom clutch.other import keep",
        "def nested():\n    pass\n    pass\n    return 7",
        "value = 9",
        "value = 9",
    )
