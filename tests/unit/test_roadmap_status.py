# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verifies read-only clutch roadmap status: per-release row buckets, gate results, next and waiting rows, declined rows, and CLI output
# relates: [clutch/__main__.py, clutch/box.py, clutch/journal.py, clutch/roadmap.py, clutch/runner.py, clutch/seams.py]
# owner: engine
# verified: df236100
# hash: ed8729ad9a2fd7bac83aa888af49468f11e3cacfdddfd70345ef50d1d6714ea8
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

import clutch.__main__ as cli
from clutch import roadmap
from clutch.box import Box, Resolution, RoadmapRow
from clutch.journal import Event, EventType
from clutch.runner import Refusal
from clutch.seams import LocalFileSystem
from tests.git_fake import GitFake

HEADER = "| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n|---|---|---|---|---|---|---|---|\n"


def row(number, stem, content="", priority="P2", depends="", struck=False):
    name = f"`{stem}`"
    if struck:
        name = f"~~{name}~~"
    return f"| {number} | {name} | roadmap | feature | {priority} | {depends} | | {content} |\n"


def fixture(tmp_path):
    text = "### 1.0.0\n" + HEADER
    text += row(1, "m-one", "`tickets/m-one/`") + row(2, "s-two", struck=True)
    text += row(3, "a-three", "`tickets/a-three/`") + row(4, "t-four")
    text += row(5, "x-five", "`tickets/x-five/`") + row(6, "r-six")
    text += row(7, "d-seven", depends="`a-three`")
    text += row(10, "sp-ten", "**Authored** (`tickets/sp-ten/`, `tickets/sp-sib/`).")
    text += row(11, "q-eleven", priority="P1")
    text += "### 1.0.0, last group\n" + HEADER + row(8, "h-eight", "`tickets/h-eight/evidence/a0.txt`")
    text += "### 2.0.0\n" + HEADER + row(9, "n-nine", priority="P0")
    path = tmp_path / roadmap.ROADMAP
    path.parent.mkdir()
    path.write_text(text)
    files = {"docs/roadmap.md", "tickets/t-four/ticket.md"}
    events = [
        Event(1, EventType.STATE_TRANSITION, "ts", stem, None, {"to": state})
        for stem, state in {"m-one": "already_satisfied", "a-three": "running", "x-five": "rejected", "sp-ten": "merged", "sp-sib": "running"}.items()
    ]

    class Journal:
        def read(self):
            return events

        def append(self, *args, **kwargs):
            pytest.fail("status appended to journal")

    checkout = SimpleNamespace(
        repo=tmp_path,
        git=GitFake(_run=lambda *args: "\0".join(sorted(files)) + "\0"),
        journal=Journal(),
        config=SimpleNamespace(state_dir=tmp_path / "state", caps=SimpleNamespace(supervise=2)),
        fs=LocalFileSystem(),
    )
    return checkout, text, files, events


def test_status_buckets(tmp_path):
    checkout, text, files, events = fixture(tmp_path)
    lines = asyncio.run(roadmap.status(checkout))
    assert lines[:3] == [
        "release 1.0.0: 2 merged, 3 authored, 2 ready, 3 blocked; gate not run",
        "release 2.0.0: 0 merged, 0 authored, 0 ready, 1 blocked; gate not run",
        "next: q-eleven, r-six",
    ]
    assert len(lines) == 5
    assert any(line.startswith("waits: row 5 x-five: ") and "rejected" in line for line in lines)
    held = next(line for line in lines if line.startswith("waits: row 8 h-eight: "))
    assert "tickets/h-eight/evidence/a0.txt" in held and " -- " in held
    choice = roadmap.choose(roadmap.parse(text), states=roadmap.last_states(events), files=files)
    assert sum(int(line.split(", ")[1].split()[0]) for line in lines[:2]) == choice.open == 3


def test_status_gate_results(tmp_path):
    checkout, _, _, events = fixture(tmp_path)
    for release, passed, failed, ts in [
        ("1.0.0", False, "./dev.py test", "ts1"),
        ("1.0.0", True, None, "ts2"),
        ("2.0.0", False, "uv run clutch roadmap merged --release 2.0.0", "ts3"),
        ("9.9.9", True, None, "ts4"),
    ]:
        events.append(Event(1, EventType.SIGNAL, ts, None, None, {"signal": "roadmap_gate", "release": release, "passed": passed, "failed": failed}))
    lines = asyncio.run(roadmap.status(checkout))
    assert lines[0].endswith("; gate passed ts2")
    assert lines[1].endswith("; gate failed ts3: uv run clutch roadmap merged --release 2.0.0")
    assert all("9.9.9" not in line for line in lines)


def test_status_is_read_only(tmp_path):
    checkout, text, _, _ = fixture(tmp_path)
    path = tmp_path / roadmap.ROADMAP
    assert asyncio.run(roadmap.status(checkout))
    assert path.read_bytes() == text.encode()
    assert checkout.git.calls == [("_run", (tmp_path, "ls-files", "--cached", "--others", "--exclude-standard", "-z"), {})]
    path.unlink()
    checkout.git.calls.clear()
    with pytest.raises(Refusal, match="docs/roadmap.md"):
        asyncio.run(roadmap.status(checkout))
    assert checkout.git.calls == []


def test_main_roadmap_status(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=Path("/state")))
    monkeypatch.setattr(cli, "child_env", lambda *a: {})
    monkeypatch.setattr(cli, "Lockfile", lambda *a, **kw: pytest.fail("lock taken"))

    async def status(checkout):
        return ["a", "b"]

    monkeypatch.setattr(roadmap, "status", status)
    assert cli.main(["roadmap", "status"], cwd=Path("/repo"), env={}) == 0
    assert capsys.readouterr().out == "a\nb\n"

    async def refuse(checkout):
        raise Refusal("missing", "restore it")

    monkeypatch.setattr(roadmap, "status", refuse)
    assert cli.main(["roadmap", "status"], cwd=Path("/repo"), env={}) == 2
    assert capsys.readouterr().err == "clutch roadmap: missing -- restore it\n"
    with pytest.raises(SystemExit):
        cli._parser().parse_args(["roadmap", "status", "extra"])


def test_status_declined_row_waits(tmp_path):
    checkout, _, _, _ = fixture(tmp_path)
    path = tmp_path / roadmap.ROADMAP
    path.write_text("### 1.0.0\n" + HEADER + row(3, "a-row") + row(4, "b-row"))
    box = Box(checkout.config.state_dir / "box", checkout.fs)
    payload = RoadmapRow(number=3, release="1.0.0", stem="a-row", owner="roadmap", kind="feature", priority="P1", content="Work.", plan=roadmap.ROADMAP)
    id_, _ = box.enqueue(message_class="roadmap_row", origin="roadmap/a-row", summary="Declined work", roadmap_row=payload)
    box.resolve(id_, Resolution(kind="declined", link="missing"))
    lines = asyncio.run(roadmap.status(checkout))
    assert "waits: row 3 a-row: declined -- declined" in lines
    assert "next: b-row" in lines
