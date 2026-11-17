import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

import clutch.__main__ as cli
from clutch import roadmap
from clutch.box import Box, Resolution
from clutch.git import Git
from clutch.journal import EventType
from clutch.runner import Refusal
from clutch.seams import LocalFileSystem
from tests.fakes import FakeJournal
from tests.unit.test_roadmap_table import document, row


class FakeGit:
    def __init__(self, repo):
        self.repo, self.dirty, self.files, self.commits = repo, "", [], []

    async def status_porcelain(self, repo, *args):
        assert (repo, args) == (self.repo, ("--", roadmap.ROADMAP))
        return self.dirty

    async def _run(self, repo, *args):
        assert args == ("ls-files", "--cached", "--others", "--exclude-standard", "-z")
        return "\0".join(self.files)

    async def commit(self, repo, message, *, only):
        self.commits.append((message, only, (repo / roadmap.ROADMAP).read_text()))


@pytest.fixture
def setup(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "triage.md").write_text("placeholder")
    monkeypatch.setattr(roadmap, "SPECS_DIR", specs)
    monkeypatch.setattr(roadmap, "load_spec", lambda _: SimpleNamespace(meta=SimpleNamespace(version="9.9")))
    git = FakeGit(repo)
    git.files = ["docs/sample-plan.md"]
    checkout = SimpleNamespace(repo=repo, git=git, config=SimpleNamespace(state_dir=tmp_path / "state", caps=SimpleNamespace(supervise=2)), fs=LocalFileSystem(), journal=FakeJournal())
    return checkout, Box(checkout.config.state_dir / "box", checkout.fs)


def put(checkout, *rows):
    path = checkout.repo / roadmap.ROADMAP
    path.parent.mkdir(exist_ok=True)
    path.write_text(document(*rows))


def r(n, stem, **kw):
    return row(n, f"`{stem}`", owner="sample plan 1", priority="P2", **kw)


def run(checkout, ahead, callback):
    return asyncio.run(roadmap.author_ahead(checkout, ahead, callback))


def test_dirty_or_missing_roadmap_refuses(setup):
    checkout, box = setup
    calls = []

    async def author(ids):
        calls.append(ids)

    checkout.git.dirty = " M docs/roadmap.md"
    with pytest.raises(Refusal, match="docs/roadmap.md"):
        run(checkout, 2, author)
    checkout.git.dirty = ""
    with pytest.raises(Refusal, match="master ticket table"):
        run(checkout, 2, author)
    assert not checkout.git.commits and not box.messages() and not calls


def test_files_until_ahead_and_links(setup):
    checkout, box = setup
    put(checkout, r(1, "a-row", content="**Authored** (`tickets/a-row/`). Existing."), r(2, "b-row", before="`c-row`", content="Build B."), r(3, "c-row", content="Build C."))
    calls = []

    async def author(ids):
        calls.append(ids)
        for id in ids:
            box.resolve(id, Resolution(kind="ticket", link=box.get(id).roadmap_row.stem))

    lines = run(checkout, 2, author)
    (message,) = box.messages()
    assert message.roadmap_row.model_dump() == dict(
        number=2, release="Next", stem="b-row", owner="sample plan 1", kind="feature", priority="P2", depends=[], runs_before=["c-row"], content="Build B.", plan="docs/sample-plan.md"
    )
    assert message.verdict.verdict == "author" and message.verdict.produced_by_spec_version == "9.9"
    assert calls == [[message.id]]
    assert [(m, paths) for m, paths, _ in checkout.git.commits] == [("clutch(roadmap): author b-row", ["docs/roadmap.md"])]
    rows = roadmap.parse((checkout.repo / roadmap.ROADMAP).read_text())
    assert rows[1].linked and not rows[2].linked and rows[2].content == "Build C."
    assert lines[-1] == "roadmap: 2 of 2 rows open"


def test_declined_row_is_skipped(setup):
    checkout, box = setup
    put(checkout, r(1, "a-row", content="**Authored** (`tickets/a-row/`). Existing."), r(2, "b-row"), r(3, "c-row"))

    async def decline(ids):
        box.resolve(ids[0], Resolution(kind="declined", link="declined-record"))

    run(checkout, 2, decline)

    async def author(ids):
        box.resolve(ids[0], Resolution(kind="ticket", link="c-row"))

    lines = run(checkout, 2, author)
    assert any("roadmap: authored row 2 b-row" in line for line in lines)
    assert [m for m, _, _ in checkout.git.commits] == ["clutch(roadmap): author b-row"]


def test_full_window_calls_no_model(setup):
    checkout, box = setup
    put(checkout, r(1, "a-row", content="**Authored** (`tickets/a-row/`). A."), r(2, "b-row", content="**Authored** (`tickets/b-row/`). B."))

    async def author(ids):
        pytest.fail("provider called")

    assert run(checkout, 2, author)[-1] == "roadmap: 2 of 2 rows open"
    assert not box.messages()


def test_strikes_and_links_existing(setup):
    checkout, _ = setup
    put(checkout, r(1, "x-row", content="**Authored** (`tickets/x-row/`). X."), r(2, "y-row"))
    checkout.git.files.append("tickets/y-row/ticket.md")
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="x-row")

    async def author(ids):
        pytest.fail("provider called")

    lines = run(checkout, 1, author)
    assert [(m, p) for m, p, _ in checkout.git.commits] == [("clutch(roadmap): strike x-row", ["docs/roadmap.md"]), ("clutch(roadmap): link y-row", ["docs/roadmap.md"])]
    assert roadmap.parse(checkout.git.commits[0][2])[0].struck
    first, second = roadmap.parse(checkout.git.commits[1][2])
    assert first.struck and second.linked
    assert "roadmap: struck row 1 x-row" in lines and "roadmap: linked row 2 y-row" in lines


def test_unsettled_and_waiting_rows_are_reported(setup):
    checkout, box = setup
    put(checkout, r(1, "a-row"), r(2, "b-row", content="Run hand test."))
    calls = []

    async def pending(ids):
        calls.append(ids)

    lines = run(checkout, 1, pending)
    assert "roadmap: row 1 a-row pending -- run clutch roadmap author again" in lines
    assert any("row 2 b-row waits: capture evidence missing -- run the capture" in line for line in lines)

    async def decline(ids):
        calls.append(ids)
        box.resolve(ids[0], Resolution(kind="declined", link="record-1"))

    lines = run(checkout, 1, decline)
    assert calls[0] == calls[1] and len(box.messages()) == 1
    assert box.messages()[0].verdict.produced_by_spec_version == "9.9"
    assert any("row 1 a-row declined -> record-1" in line for line in lines)
    assert not checkout.git.commits


def test_main_roadmap_author(monkeypatch, capsys, tmp_path):
    events = []
    monkeypatch.setattr(cli, "load_config", lambda *a, **k: SimpleNamespace(state_dir=tmp_path))
    monkeypatch.setattr(cli, "child_env", lambda *a: {})

    class Lock:
        def __init__(self, state_dir, *, verb, instance_id, clock):
            assert verb == "roadmap" and instance_id == "desc"

        def acquire(self):
            events.append("acquire")

        def release(self):
            events.append("release")

    class Session:
        async def close(self):
            events.append("close")

    async def describe(self, repo):
        return "desc"

    async def reap(checkout):
        events.append("reap")

    async def preflight(checkout, session):
        return "llm"

    async def triage(checkout, llm, ids):
        events.append((llm, ids))

    async def author(checkout, ahead, callback):
        events.append(ahead)
        await callback(["box-1"])
        return ["line one", "line two"]

    monkeypatch.setattr(cli, "Lockfile", Lock)
    monkeypatch.setattr(Git, "describe", describe)
    monkeypatch.setattr(cli.runner, "reap", reap)
    monkeypatch.setattr(cli, "build_control", lambda checkout: SimpleNamespace(providers=Session()))
    monkeypatch.setattr(cli, "_preflighted_llm", preflight)
    monkeypatch.setattr(cli.triage, "triage_pass", triage)
    monkeypatch.setattr(roadmap, "author_ahead", author)
    assert cli.main(["roadmap", "author", "--ahead", "3"], cwd=tmp_path, env={}) == 0
    assert events == ["acquire", "reap", 3, ("llm", frozenset({"box-1"})), "close", "release"]
    assert capsys.readouterr().out == "line one\nline two\n"

    async def refusal(*args):
        raise Refusal("blocked", "repair")

    monkeypatch.setattr(roadmap, "author_ahead", refusal)
    events.clear()
    assert cli.main(["roadmap", "author"], cwd=tmp_path, env={}) == 2
    assert capsys.readouterr().err.startswith("clutch roadmap:")
    assert events == ["acquire", "reap", "close", "release"]
    events.clear()
    assert cli.main(["roadmap", "author", "--ahead", "0"], cwd=tmp_path, env={}) == 2
    assert not events and capsys.readouterr().err.startswith("clutch roadmap:")
    with pytest.raises(SystemExit):
        cli._parser().parse_args(["roadmap"])
    assert cli._parser().parse_args(["roadmap", "author"]).ahead == 2
