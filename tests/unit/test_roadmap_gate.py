import asyncio
from types import SimpleNamespace

import pytest

import clutch.__main__ as cli
from clutch import roadmap
from clutch.journal import EventType
from clutch.runner import Refusal
from clutch.seams import ExecutableNotFound
from tests.fakes import FakeJournal


class RecordingExec:
    def __init__(self, answers):
        self.answers = iter(answers)
        self.calls = []

    async def run(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        answer = next(self.answers)
        if isinstance(answer, Exception):
            raise answer
        return answer


def checkout(repo, commands=None, answers=()):
    if commands is not None:
        path = repo / roadmap.ROADMAP
        path.parent.mkdir(parents=True)
        path.write_text("### 1.0.0\n```gate\n" + commands + "\n```\n")
    return SimpleNamespace(
        repo=repo,
        config=SimpleNamespace(drain=SimpleNamespace(max_ticket_minutes=7)),
        env={"PROVIDER_KEY": "secret"},
        exec_=RecordingExec(answers),
        journal=FakeJournal(),
    )


def test_gates_parse():
    # Full-heading keys, blank commands, and whitespace splitting all change this result.
    assert roadmap.gates(
        "### 1.0.0\n| a | b |\n```gate\n./dev.py test\n\nuv run clutch roadmap merged --release 1.0.0 --priority P0 P1\n```\n"
        '### 1.0.0, last group\n### 2.0.0 (conditional)\n```gate\ntool "a b" c\n```\n'
    ) == {
        "1.0.0": (("./dev.py", "test"), ("uv", "run", "clutch", "roadmap", "merged", "--release", "1.0.0", "--priority", "P0", "P1")),
        "2.0.0": (("tool", "a b", "c"),),
    }


@pytest.mark.parametrize(
    ("text", "message", "road"),
    [
        ("```gate\ntool\n```", "no release heading", "add a ```gate block"),
        ("### 1.0.0\n```gate\ntool\n```\n### 1.0.0, last group\n```gate\nother\n```", "duplicate gate", "keep exactly one"),
        ("### 1.0.0\n```gate\ntool", "unclosed gate", "close the gate block"),
        ("### 1.0.0\n```gate\n\n  \n```", "empty gate", "add at least one argv command"),
        ('### 1.0.0\n```gate\ntool "unclosed\n```', "invalid gate command", "fix the command's quoting"),
        ("### 1.0.0\n```gate\n''\n```", "no executable", "non-empty executable"),
        ("### 1.0.0\n```gate\n'  '\n```", "no executable", "non-empty executable"),
    ],
)
def test_gates_refuse(text, message, road):
    # Each malformed block must refuse instead of yielding an empty or replaced gate.
    with pytest.raises(Refusal, match=message) as caught:
        roadmap.gates(text)
    assert road in str(caught.value)


def test_run_gate_passes(tmp_path, monkeypatch):
    c = checkout(tmp_path, "first one\nsecond", [(0, "", ""), (0, "", "")])
    monkeypatch.setattr(roadmap, "child_env", lambda env, config: {"SAFE": "yes"})
    # Running only one command or omitting the verdict changes the returned lines.
    assert asyncio.run(roadmap.run_gate(c, "1.0.0")) == (True, ["gate 1.0.0: ok: first one", "gate 1.0.0: ok: second", "gate 1.0.0: passed"])
    # Wrong cwd, inherited secrets, no timeout, and reordering each differ here.
    assert c.exec_.calls == [
        (["first", "one"], {"cwd": tmp_path, "env": {"SAFE": "yes"}, "timeout": 420.0}),
        (["second"], {"cwd": tmp_path, "env": {"SAFE": "yes"}, "timeout": 420.0}),
    ]
    # Omitting the signal, recording per command, or storing an empty failed string differs.
    assert [(e.type, e.body) for e in c.journal.events] == [(EventType.SIGNAL, {"signal": "roadmap_gate", "release": "1.0.0", "passed": True, "failed": None})]


@pytest.mark.parametrize(
    ("answer", "reason", "suffix"),
    [
        ((3, "out line\n", "warn\n\nlast err\n\n"), "exit 3", " -- last err"),
        (TimeoutError(), "timeout", ""),
        (ExecutableNotFound("second"), "not found", ""),
        ((4, "first out\nlast out\n\n", "\n  \n"), "exit 4", " -- last out"),
        ((5, "", ""), "exit 5", ""),
    ],
)
def test_run_gate_stops_at_first_failure(tmp_path, monkeypatch, answer, reason, suffix):
    c = checkout(tmp_path, "first\nsecond\nthird", [(0, "", ""), answer, (0, "", "")])
    monkeypatch.setattr(roadmap, "child_env", lambda *a: {})
    # Swallowing exceptions, wrong stream/tail selection, and wrong verdict change this.
    assert asyncio.run(roadmap.run_gate(c, "1.0.0")) == (
        False,
        ["gate 1.0.0: ok: first", f"gate 1.0.0: failed ({reason}): second{suffix}", "gate 1.0.0: failed"],
    )
    # Continuing after failure would record third, in every parameter case.
    assert [call[0] for call in c.exec_.calls] == [["first"], ["second"]]
    # An exception path must also record a failure, exactly once.
    assert [(e.type, e.body) for e in c.journal.events] == [(EventType.SIGNAL, {"signal": "roadmap_gate", "release": "1.0.0", "passed": False, "failed": "second"})]


def test_run_gate_refusals(tmp_path):
    unknown_release = checkout(tmp_path / "unknown", "first", [(0, "", "")])
    with pytest.raises(Refusal, match="9.9.9"):
        asyncio.run(roadmap.run_gate(unknown_release, "9.9.9"))
    # These must be checked on each checkout: a later variable must not mask side effects.
    assert unknown_release.exec_.calls == []
    assert unknown_release.journal.events == []

    missing_roadmap = checkout(tmp_path / "missing", answers=[(0, "", "")])
    with pytest.raises(Refusal, match="docs/roadmap.md"):
        asyncio.run(roadmap.run_gate(missing_roadmap, "1.0.0"))
    assert missing_roadmap.exec_.calls == []
    assert missing_roadmap.journal.events == []


def test_run_gate_validates_all_blocks_before_running(tmp_path):
    c = checkout(tmp_path, "first", [(0, "", "")])
    with (tmp_path / roadmap.ROADMAP).open("a") as stream:
        stream.write("### 2.0.0\n```gate\n\n```\n")
    with pytest.raises(Refusal, match="empty gate"):
        asyncio.run(roadmap.run_gate(c, "1.0.0"))
    # Lazy validation would already have run first or journaled its result.
    assert c.exec_.calls == []
    assert c.journal.events == []


@pytest.mark.parametrize(("result", "code", "out", "err"), [(True, 0, "a\nb\n", ""), (False, 1, "c\n", ""), (None, 2, "", "clutch roadmap: no gate -- add one\n")])
def test_main_roadmap_gate(tmp_path, monkeypatch, capsys, result, code, out, err):
    monkeypatch.setattr(cli, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=tmp_path / "state"))
    monkeypatch.setattr(cli, "child_env", lambda *a: {"SAFE": "yes"})
    monkeypatch.setattr(cli, "Journal", lambda *a: FakeJournal())

    class NoLock:
        def __init__(self, *a, **kw):
            pytest.fail("roadmap gate took the writer lock")

    calls = []

    async def fake_gate(c, release):
        calls.append((c.repo, release))
        if result is None:
            raise Refusal("no gate", "add one")
        return result, ["a", "b"] if result else ["c"]

    monkeypatch.setattr(cli, "Lockfile", NoLock)
    monkeypatch.setattr(roadmap, "run_gate", fake_gate)
    # A hard-coded exit code cannot pass both success and failure cases.
    assert cli.main(["roadmap", "gate", "1.0.0"], cwd=tmp_path, env={}) == code
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == (out, err)
    # Ignoring the release or composing another checkout changes this call.
    assert calls == [(tmp_path, "1.0.0")]
