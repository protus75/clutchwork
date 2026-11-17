import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from clutch import roadmap
from clutch.box import Box
from clutch.git import CommitLock, Git
from clutch.journal import EventType, Journal
from clutch.seams import LocalFileSystem, SubprocessExec
from tests.integration.test_cli import ENV


def run(coro):
    return asyncio.run(coro)


@pytest.mark.parametrize("collision", ["none", "row", "file"])
def test_signal_renames_and_updates_dependencies(tmp_path, collision):
    git, checkout, box, path = setup_repo(tmp_path, collision)
    checkout.journal.append(EventType.SIGNAL, {"signal": "diagnosis"}, ticket="x")
    received = []

    async def author(ids):
        received.extend(box.get(id).roadmap_row.stem for id in ids)

    run(roadmap.author_ahead(checkout, 1, author))
    stem = "x-r1" if collision == "none" else "x-r2"
    rows = roadmap.parse(path.read_text())
    assert rows[0].stem == stem
    assert rows[1].depends == f"`{stem}`"
    assert received == [stem]
    assert run(git._run(tmp_path, "log", "-1", "--format=%s")).strip() == f"clutch(roadmap): refile x as {stem}"


def test_unused_stem_is_unchanged(tmp_path):
    git, checkout, box, path = setup_repo(tmp_path, "none")
    before = path.read_text()
    received = []

    async def author(ids):
        received.extend(box.get(id).roadmap_row.stem for id in ids)

    run(roadmap.author_ahead(checkout, 1, author))
    assert path.read_text() == before
    assert received == ["x"]
    assert run(git._run(tmp_path, "log", "-1", "--format=%s")).strip() == "initial"


def test_rejected_stem_skips_journal_collision(tmp_path):
    git, checkout, box, path = setup_repo(tmp_path, "none")
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="x")
    checkout.journal.append(EventType.SIGNAL, {"signal": "diagnosis"}, ticket="x-r1")
    received = []

    async def author(ids):
        received.extend(box.get(id).roadmap_row.stem for id in ids)

    run(roadmap.author_ahead(checkout, 1, author))
    rows = roadmap.parse(path.read_text())
    assert rows[0].stem == "x-r2"
    assert rows[1].depends == "`x-r2`"
    assert received == ["x-r2"]


def setup_repo(tmp_path, collision):
    def clock():
        return datetime.now(UTC)

    git = Git(SubprocessExec(), env=ENV, timeout=10, commit_lock=CommitLock(tmp_path / "state", clock=clock, sleep=asyncio.sleep))
    run(git.init(tmp_path, branch="main"))
    path = tmp_path / roadmap.ROADMAP
    path.parent.mkdir()
    text = (
        "### 1.0.0\n| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n"
        "|---|---|---|---|---|---|---|---|\n"
        "| 1 | `x` | roadmap | feature | P1 | | | Build x. |\n"
        "| 2 | `dependent` | roadmap | feature | P1 | `x` | | Build dependent. |\n"
    )
    if collision == "row":
        text += "| 3 | `x-r1` | roadmap | feature | P1 | `x` | | Build later. |\n"
    path.write_text(text)
    paths = [roadmap.ROADMAP]
    if collision == "file":
        ticket = tmp_path / "tickets/x-r1/evidence/data"
        ticket.parent.mkdir(parents=True)
        ticket.write_text("evidence")
        paths.append("tickets/x-r1/evidence/data")
    run(git.add(tmp_path, paths))
    run(git.commit(tmp_path, "initial"))
    fs = LocalFileSystem()
    checkout = SimpleNamespace(repo=tmp_path, git=git, fs=fs, config=SimpleNamespace(state_dir=tmp_path / "state", caps=SimpleNamespace(supervise=2)), journal=Journal(tmp_path / "state", clock))
    return git, checkout, Box(checkout.config.state_dir / "box", fs), path
