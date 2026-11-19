import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace as NS

from clutch import merge, roadmap
from clutch.git import Git
from tests.unit.test_roadmap_table import document, row


class Exec:
    def __init__(self, events):
        self.events = events

    async def run(self, argv, **kwargs):
        self.events.append(argv[3:])
        return 0, "sha\n", ""


@asynccontextmanager
async def commit_lock():
    yield


def make_git(events):
    return Git(Exec(events), env={}, timeout=None, commit_lock=commit_lock())


def test_lock_is_per_instance():
    first, second = make_git([]), make_git([])
    assert isinstance(first.main_write(), asyncio.Lock)
    assert first.main_write() is first.main_write()
    assert first.main_write() is not second.main_write()


def test_waiting_callers(tmp_path, monkeypatch):
    async def check():
        events = []
        git = make_git(events)
        path = tmp_path / roadmap.ROADMAP
        path.parent.mkdir()
        original = document(row(1, "`a-row`", content="Before."))
        path.write_text(original)
        selected = roadmap.parse(original)[0]
        checkout = NS(repo=tmp_path, git=git, fs=NS(write=lambda p, data: p.write_bytes(data)))

        async def commit(*args, **kwargs):
            events.append("commit")

        async def gate(*args):
            events.append("gate")
            return False, ["blocked"]

        async def status(*args):
            events.append("status")
            return ""

        async def diff(*args):
            events.append("diff")
            return []

        monkeypatch.setattr(git, "commit", commit)
        monkeypatch.setattr(git, "status_porcelain", status)
        monkeypatch.setattr(git, "diff_names", diff)
        monkeypatch.setattr(roadmap, "current_release", lambda repo: "1.0.0")
        monkeypatch.setattr(roadmap, "run_gate", gate)

        calls = [
            lambda: git.merge_squash(tmp_path, "branch", "message"),
            lambda: roadmap._write_row(checkout, selected, lambda text, fresh: text.replace("Before.", "After."), "edit", "message", []),
            lambda: roadmap.ship(checkout),
            lambda: merge.dirty_overlap(NS(repo=tmp_path, git=git), "branch"),
        ]
        expected = [[["merge", "--squash", "branch"], ["commit", "-m", "message"], ["rev-parse", "--verify", "HEAD"]], ["commit"], ["gate"], ["status", "diff"]]
        for call, want in zip(calls, expected, strict=True):
            events.clear()
            async with git.main_write():
                task = asyncio.create_task(call())
                await asyncio.sleep(0)
                assert events == []
                assert path.read_text() == original
                assert not task.done()
            await asyncio.wait_for(task, 1)
            assert events == want
            if want == ["commit"]:
                assert path.read_text() == original.replace("Before.", "After.")
                path.write_text(original)

    asyncio.run(check())


def test_overlapping_pairs(tmp_path, monkeypatch):
    async def check():
        events = []
        git = make_git(events)
        path = tmp_path / roadmap.ROADMAP
        path.parent.mkdir()
        original = document(row(1, "`a-row`", content="Before."))
        path.write_text(original)
        selected = roadmap.parse(original)[0]
        checkout = NS(repo=tmp_path, git=git, fs=NS(write=lambda p, data: p.write_bytes(data)))
        entered, release = asyncio.Event(), asyncio.Event()

        async def commit(*args, **kwargs):
            events.append("commit-start")
            entered.set()
            await release.wait()
            events.append("commit-end")

        async def status(*args):
            events.append("status")
            return ""

        async def diff(*args):
            events.append("diff")
            return []

        monkeypatch.setattr(git, "commit", commit)
        monkeypatch.setattr(git, "status_porcelain", status)
        monkeypatch.setattr(git, "diff_names", diff)
        first = asyncio.create_task(roadmap._write_row(checkout, selected, lambda text, fresh: text.replace("Before.", "After."), "edit", "message", []))
        await asyncio.wait_for(entered.wait(), 1)
        second = asyncio.create_task(merge.dirty_overlap(NS(repo=tmp_path, git=git), "branch"))
        await asyncio.sleep(0)
        assert events == ["commit-start"]
        assert path.read_text() == original.replace("Before.", "After.")
        release.set()
        await asyncio.wait_for(asyncio.gather(first, second), 1)
        assert events == ["commit-start", "commit-end", "status", "diff"]

        events.clear()
        entered.clear()
        release.clear()

        async def gate(*args):
            events.append("gate-start")
            entered.set()
            await release.wait()
            events.append("gate-end")
            return False, []

        monkeypatch.setattr(roadmap, "current_release", lambda repo: "1.0.0")
        monkeypatch.setattr(roadmap, "run_gate", gate)
        first = asyncio.create_task(roadmap.ship(checkout))
        await asyncio.wait_for(entered.wait(), 1)
        second = asyncio.create_task(git.merge_squash(tmp_path, "branch", "message"))
        await asyncio.sleep(0)
        assert events == ["gate-start"]
        release.set()
        await asyncio.wait_for(asyncio.gather(first, second), 1)
        assert events == ["gate-start", "gate-end", ["merge", "--squash", "branch"], ["commit", "-m", "message"], ["rev-parse", "--verify", "HEAD"]]

    asyncio.run(check())
