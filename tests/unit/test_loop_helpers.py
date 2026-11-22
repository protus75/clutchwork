# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the tests/loop_helpers.py exports (Rig, the fake Time clock, the ticket text builder, the scheduler import closure, and the triage, terminal, restart and serve helpers), checking that fixtures write only under tmp_path, never touch real git, and match what serve_rig re-exports
# relates: [tests/fakes.py, tests/loop_helpers.py]
# owner: engine
# verified: 810808b8
# hash: c3962b2d4728240d7a45b6bdc6b3d03c3f044be963cc1a24b74be05dc86e95a2
import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from tests import fakes, loop_helpers
from tests.loop_helpers import (
    Rig,
    Time,
    repo,  # noqa: F401 -- fixture
    scheduler_import_closure,
    text,
    turn,
)


def test_exports():
    assert all(
        getattr(loop_helpers, name) is value
        for name, value in {
            "Rig": Rig,
            "Time": Time,
            "text": text,
            "turn": turn,
            "scheduler_import_closure": scheduler_import_closure,
        }.items()
    )


def test_rig_writes_under_root(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    rig = Rig(root)
    ticket = rig.add("example", priority="P0")
    assert ticket.stem == "example"
    assert (root / "tickets/example/ticket.md").read_text() == rig.files["example"]
    assert sorted(p.name for p in tmp_path.iterdir()) == ["root"]


@pytest.mark.asyncio
async def test_time_wakes_at_deadline():
    clock = Time()
    start = clock()
    sleeper = asyncio.create_task(clock.sleep(5))
    await turn()
    clock.advance(4)
    assert not clock.waits[0][1].done()
    clock.advance(1)
    await turn()
    assert sleeper.done()
    assert clock() == start + timedelta(seconds=5) == datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=5)
    await sleeper


def test_text_formats_parameters():
    result = text("P0", "draft", "- parent")
    assert "state: draft\nsource: human\npriority: P0" in result
    assert "## Depends on\n- parent" in result


@pytest.mark.asyncio
async def test_turn_is_shared_and_yields():
    assert turn is fakes.turn
    events = []
    asyncio.get_running_loop().call_soon(events.append, "callback")
    await turn()
    assert events == ["callback"]


def test_scheduler_import_closure_uses_supplied_sources():
    sources = {"clutch.__main__": "from clutch import a", "clutch": "", "clutch.a": "import clutch.b", "clutch.b": "", "clutch.unused": ""}
    assert scheduler_import_closure(sources) == {"clutch.__main__", "clutch", "clutch.a", "clutch.b"}


def test_triage_exports():
    from tests.loop_helpers import author_reply, enqueue, escape_report, escape_rig, reply, requisition_reply, root_with_box, run

    # Rules out leaving an export on the skipped hub alone.
    assert all(
        getattr(loop_helpers, name) is value
        for name, value in {
            "author_reply": author_reply,
            "enqueue": enqueue,
            "escape_report": escape_report,
            "escape_rig": escape_rig,
            "reply": reply,
            "requisition_reply": requisition_reply,
            "root_with_box": root_with_box,
            "run": run,
        }.items()
    )


def test_triage_reply():
    # Rules out losing supplied evidence/link/days or serializing a verdict differently.
    assert loop_helpers.reply("declined", link="known", summary="specific", evidence=["trace"], days=9) == (
        '{"verdict": "declined", "link": "known", "summary": "specific", "rationale": "Observed and classified", "evidence": ["trace"], "reopen_after_days": 9}'
    )
    # Rules out using the days argument for author verdicts.
    assert loop_helpers.reply("author", days=9) == (
        '{"verdict": "author", "link": null, "summary": "Triage\'s own summary", "rationale": "Observed and classified", "evidence": [], "reopen_after_days": null}'
    )


def test_triage_author_reply():
    import json

    # Rules out changing any ticket bytes or ignoring the requested stem.
    expected = """---
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
"""
    assert loop_helpers.author_reply("distinct-stem") == json.dumps({"stem": "distinct-stem", "ticket": expected})


def test_triage_requisition_reply():
    from tests.stage_replies import requisition_reply

    # Rules out a copied wrapper with the same output.
    assert loop_helpers.requisition_reply is requisition_reply


def test_triage_root_with_box(tmp_path, monkeypatch):
    from pathlib import Path

    import yaml

    root = tmp_path / "repo"
    write_bytes, write_text, mkdir = Path.write_bytes, Path.write_text, Path.mkdir
    written = []

    def confined(method):
        def call(path, *args, **kwargs):
            if not path.is_relative_to(tmp_path):
                pytest.fail(f"fixture wrote outside tmp_path: {path}")
            written.append(path)
            return method(path, *args, **kwargs)

        return call

    monkeypatch.setattr(Path, "write_bytes", confined(write_bytes))
    monkeypatch.setattr(Path, "write_text", confined(write_text))
    monkeypatch.setattr(Path, "mkdir", confined(mkdir))
    actual, box = loop_helpers.root_with_box(tmp_path)
    # Rules out returning another root/box or omitting author/review routing.
    assert (actual, box.root, len(yaml.safe_load((root / "config.yaml").read_text())["routing"]), root / "config.yaml" in written) == (
        root,
        root / ".clutch/state/box",
        9,
        True,
    )


def test_triage_enqueue(tmp_path):
    from clutch.box import Box
    from clutch.seams import LocalFileSystem

    box = Box(tmp_path / "box", LocalFileSystem())
    ident = loop_helpers.enqueue(box, "distinct concern")
    message = box.get(ident)
    # Rules out dropping the supplied summary, origin, class or returned id.
    assert (ident, message.summary, message.origin, message.message_class) == (box.messages()[0].id, "distinct concern", "test", "suggestion")


def test_triage_run(tmp_path, monkeypatch):
    from clutch.llm import FakeLLM
    from tests.cli_helpers import ENV
    from tests.fakes import FakeClock

    llm = FakeLLM(["distinct reply"])
    calls = []
    monkeypatch.setattr(loop_helpers, "main", lambda argv, **kwargs: calls.append((argv, kwargs)) or 17)
    result = loop_helpers.run(tmp_path, monkeypatch, llm)
    argv, kwargs = calls[0]
    import clutch.__main__ as main_module

    # Rules out dropping the exit status, using a different command/root/env/clock or replacing the supplied LLM.
    assert (result, argv, kwargs["cwd"], kwargs["env"], type(kwargs["clock"]), main_module.ProviderLLM()) == (
        17,
        ["box", "triage"],
        tmp_path,
        ENV,
        FakeClock,
        llm,
    )


@pytest.mark.asyncio
async def test_triage_escape_rig(tmp_path, monkeypatch):
    from clutch import stages
    from clutch.specs import Spec, SpecMeta
    from tests.fakes import FakeExec, FakeFileSystem
    from tests.git_fake import GitFake

    def spec(ctx, surface):
        inputs = ("ticket", "context", "related_files", "retry_findings") if surface == "implement" else ("ticket", "diff", "prior_review", "retry_findings")
        return Spec(SpecMeta(llm_surface=surface, tier="medium", effort="medium", version="1.0"), "in-memory prompt", inputs)

    monkeypatch.setattr(stages, "_spec", spec)
    c, writer, box, checked, admitted = await loop_helpers.escape_rig(tmp_path)
    # Rules out retaining real git/process seams, creating .git, or returning an unchecked/unreviewed admission.
    assert (type(c.git), type(c.exec_), type(c.fs), list(tmp_path.rglob(".git")), checked.passed, admitted.reviewed_sha) == (
        GitFake,
        FakeExec,
        FakeFileSystem,
        [],
        True,
        checked.produced_at_sha,
    )
    # Rules out a no-op worktree/merge callback that leaves changed contents out of the shared filesystem.
    assert c.fs.read_bytes(c.repo / "outside.py") == b"changed\n"


@pytest.mark.asyncio
async def test_triage_escape_report(tmp_path, monkeypatch):
    import json
    from dataclasses import replace

    from clutch import triage
    from clutch.box import Box, Resolution
    from clutch.inbox import ingest
    from clutch.seams import LocalFileSystem
    from tests.drain_helpers import pause_checkout

    root, _ = loop_helpers.root_with_box(tmp_path)
    c = replace(pause_checkout(root), fs=LocalFileSystem())
    captured = []

    async def settle(checkout, llm):
        box = Box(checkout.config.state_dir / "box", checkout.fs)
        ingest(box, root=root, inbox=checkout.config.report_inbox, diagnostic=pytest.fail)
        message = box.messages()[0]
        captured.extend(llm.script)
        box.resolve(message.id, Resolution(kind="ticket", link="distinct-repair"))

    monkeypatch.setattr(triage, "triage_pass", settle)
    checkout, message, llm = await loop_helpers.escape_report(c, commit="a" * 40, paths=["specific.py"], stem="distinct-repair")
    data = json.loads(captured[1])
    report = json.loads((root / "inbox/a.json").read_text())
    # Rules out losing caller parameters, the bug evidence/regression changes, intake config or returned objects.
    assert (
        checkout.config.report_inbox,
        message.resolution.link,
        report["app_commit"],
        report["implicated_paths"],
        data["stem"],
        "kind: bug" in data["ticket"],
        "tickets/distinct-repair/evidence/replay.json" in data["ticket"],
        "## Scope fence\n- tests/report_regression.py\n" in data["ticket"],
        "- carries: tests/report_regression.py" in data["ticket"],
        llm.script == captured,
    ) == (
        root / "inbox",
        "distinct-repair",
        "a" * 40,
        ["specific.py"],
        "distinct-repair",
        True,
        True,
        True,
        True,
        True,
    )


def test_terminal_exports():
    from tests.loop_helpers import author, clock, diagnosis_reply, repo, transitions

    # Rules out leaving any export solely on the skipped hub.
    assert (author, clock, diagnosis_reply, repo, transitions) == tuple(getattr(loop_helpers, name) for name in ("author", "clock", "diagnosis_reply", "repo", "transitions"))


def test_repo(repo, tmp_path):
    # Rules out using the wrong root, omitting tracked fixture files, or initializing git.
    assert (repo, (repo / "config.yaml").is_file(), (repo / "clutch/thing.py").is_file(), (repo / ".git").exists()) == (tmp_path / "repo", True, True, False)


def test_terminal_author(repo):
    from tests.loop_helpers import author

    author(repo, "distinct", "- parent")
    content = (repo / "tickets/distinct/ticket.md").read_text()
    # Rules out ignoring the stem or dependency and recording an approval.
    assert "## Depends on\n- parent" in content and not (repo / ".clutch").exists()
    author(repo)
    assert (repo / "tickets/add-thing/ticket.md").is_file()


def test_terminal_clock():
    from tests.loop_helpers import clock

    # Rules out a current or different fixture time.
    assert clock() == datetime(2026, 10, 5, tzinfo=UTC)


def test_terminal_diagnosis_reply():
    import json

    from tests.loop_helpers import diagnosis_reply

    # Rules out dropping supplied lessons or changing the verdict.
    assert json.loads(diagnosis_reply("a")) == {"verdict": "retry", "lessons": ["a"]}
    assert json.loads(diagnosis_reply())["lessons"] == ["Apply the terminal findings."]


def test_terminal_transitions(tmp_path):
    from clutch.journal import EventType, Journal
    from tests.loop_helpers import clock, transitions
    from tests.stages_helpers import STEM

    journal = Journal(tmp_path / ".clutch/state", clock)
    journal.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket=STEM)
    journal.append(EventType.STATE_TRANSITION, {"to": "other"}, ticket="other")
    journal.append(EventType.SIGNAL, {"signal": "ticket_intake"}, ticket=STEM)
    # Rules out including another ticket or non-transition event.
    assert transitions(tmp_path) == [{"to": "running"}]


def test_restart_exports():
    from tests.loop_helpers import held, orphan, repository

    assert (held, orphan, repository) == (loop_helpers.held, loop_helpers.orphan, loop_helpers.repository)


@pytest.mark.asyncio
async def test_restart_repository(tmp_path, monkeypatch):
    from tests.git_fake import GitFake
    from tests.loop_helpers import repository

    rig = await repository(tmp_path, monkeypatch)
    assert isinstance(rig.checkout.git, GitFake)
    assert [call[0] for call in rig.checkout.git.calls] == ["add", "commit"]
    assert not (tmp_path / ".git").exists()
    assert isinstance(rig.fs, fakes.FakeFileSystem)


@pytest.mark.asyncio
async def test_restart_orphan(tmp_path, monkeypatch):
    from clutch.journal import EventType
    from tests.loop_helpers import orphan, repository

    rig = await repository(tmp_path, monkeypatch)
    path = await orphan(rig, "distinct", intent=True)
    assert path == tmp_path / "recovery-workspaces/distinct"
    assert (path / "interrupted.py").read_text() == "unfinished"
    assert rig.journal.events[-1].type == EventType.EFFECT_INTENT
    assert rig.journal.events[-1].key == "test/distinct/0"
    assert rig.checkout.git.calls[-1][0] == "worktree_add"


@pytest.mark.asyncio
async def test_restart_held(tmp_path, monkeypatch):
    from tests.loop_helpers import held, repository

    rig = await repository(tmp_path, monkeypatch)
    lock = held(rig)
    try:
        assert lock.held
        identity = __import__("json").loads(lock.path.read_text())
        assert identity["verb"] == "drain"
        assert identity["instance_id"] == "restart-test"
    finally:
        lock.release()


def test_serve_exports():
    from tests.loop_helpers import UpgradeChild, admission_config, admission_graph, enable_upgrade, graph, notify_command, terminals

    assert (UpgradeChild, admission_config, admission_graph, enable_upgrade, graph, notify_command, terminals) == tuple(
        getattr(loop_helpers, name) for name in ("UpgradeChild", "admission_config", "admission_graph", "enable_upgrade", "graph", "notify_command", "terminals")
    )


def test_serve_notify_command(tmp_path):
    import yaml

    from tests.config_fixture import build_config
    from tests.loop_helpers import notify_command

    (tmp_path / "config.yaml").write_text(build_config())
    notify_command(tmp_path)
    assert yaml.safe_load((tmp_path / "config.yaml").read_text())["notify"] == ["notify-sink"]
    notify_command(tmp_path, enabled=False)
    assert "notify" not in yaml.safe_load((tmp_path / "config.yaml").read_text())


def test_serve_admission_config(tmp_path):
    import yaml

    from tests.config_fixture import build_config
    from tests.loop_helpers import admission_config

    (tmp_path / "config.yaml").write_text(build_config())
    admission_config(tmp_path, command=["check"], safety=True, strategies=["specific"])
    data = yaml.safe_load((tmp_path / "config.yaml").read_text())
    assert data["review"]["mechanical"][0]["argv"] == ["check"]
    assert data["merge"] == {"safety_checks": ["combined"], "strategies": ["specific"]}


def test_serve_terminals():
    from types import SimpleNamespace

    from clutch.journal import EventType
    from tests.loop_helpers import terminals

    journal = fakes.FakeJournal()
    journal.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="a")
    selected = journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="a")
    journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="b")
    journal.append(EventType.SIGNAL, {"signal": "x"}, ticket="a")
    assert terminals(SimpleNamespace(journal=journal), "a") == [selected]


@pytest.mark.asyncio
async def test_serve_graph(tmp_path, monkeypatch):
    from tests.git_fake import GitFake
    from tests.loop_helpers import graph

    rig = await graph(tmp_path, monkeypatch)
    assert isinstance(rig.checkout.git, GitFake) and isinstance(rig.fs, fakes.FakeFileSystem)
    assert not (tmp_path / ".git").exists()
    assert rig.exec.reply == loop_helpers.reply("declined")


@pytest.mark.asyncio
async def test_serve_admission_graph(tmp_path, monkeypatch):
    from tests.git_fake import GitFake
    from tests.loop_helpers import admission_graph

    rig = await admission_graph(tmp_path, monkeypatch, {"one": {"a": "changed"}})
    assert isinstance(rig.checkout.git, GitFake) and isinstance(rig.fs, fakes.FakeFileSystem)
    assert not (tmp_path / ".git").exists()
    assert rig.models == [] and rig.returns == [] and callable(rig.prepare)


@pytest.mark.asyncio
async def test_serve_notify_exec(tmp_path, monkeypatch):
    import clutch.__main__ as cli
    from tests.loop_helpers import repository

    rig = await repository(tmp_path, monkeypatch)
    kwargs = dict(cwd=tmp_path, env={}, timeout=1)
    assert await rig.exec.run(["notify-sink", "first"], **kwargs) == (0, "", "")
    (tmp_path / "notify-fails").touch()
    assert await cli.SubprocessExec().run(["notify-sink", "second"], **kwargs) == (1, "", "")
    assert (tmp_path / "deliveries.jsonl").read_text() == "first\nsecond\n"


@pytest.mark.asyncio
async def test_serve_upgrade_child(tmp_path, monkeypatch):
    from tests.loop_helpers import UpgradeChild, graph

    rig = await graph(tmp_path, monkeypatch)
    child = UpgradeChild(rig)
    assert await child.replace(["clutch", "serve"], cwd=tmp_path, env={"X": "y"}) == 7
    assert child.calls == [(["clutch", "serve"], tmp_path, {"X": "y"})]


@pytest.mark.asyncio
async def test_serve_enable_upgrade(tmp_path, monkeypatch):
    from tests.loop_helpers import UpgradeChild, enable_upgrade, graph

    root = tmp_path / "repo"
    root.mkdir()
    rig = await graph(root, monkeypatch)
    engine = tmp_path / "engine"
    await enable_upgrade(rig, engine)
    assert (engine / "clutch/specs/base.md").read_text() == "base"
    assert (rig.owner.engine, rig.owner.argv, type(rig.owner.reexec)) == (engine, ("--config", "config.yaml", "serve"), UpgradeChild)
    assert rig.checkout.git.calls[-1][0] == "commit"


def test_serve_hub_exports():
    from tests.integration import serve_rig

    assert serve_rig.turn is fakes.turn
    assert callable(serve_rig.until)
    for name in ("graph", "admission_graph", "admission_config", "enable_upgrade", "notify_command", "terminals", "UpgradeChild"):
        assert getattr(serve_rig, name) is getattr(loop_helpers, name)
