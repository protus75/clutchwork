import asyncio
from types import SimpleNamespace as NS

import pytest

from clutch import release, roadmap
from clutch.journal import EventType
from clutch.runner import Refusal
from tests.unit.test_retro_recurrence import MemoryJournal


def test_ship_steps(tmp_path, monkeypatch):
    calls = []
    c = NS(repo=tmp_path, git=object(), env={"a": "b"}, config=NS(release=NS(publish=False)), exec_=object(), fs=object(), journal=object())
    passed = [False]
    blocked = [False]

    async def gate(checkout, current):
        calls.append(("gate", checkout, current))
        return passed[0], ["gate line"]

    async def publishable(*args):
        calls.append(("publishable", *args))
        if blocked[0]:
            raise Refusal("blocked", "fix")

    async def bump(*args):
        calls.append(("release", *args))
        return "1.1.0", "sha"

    def journal(*args):
        calls.append(("journal", *args))

    async def publish(*args):
        calls.append(("publish", *args))
        return "1.1.0", [], True

    monkeypatch.setattr(roadmap, "run_gate", gate)
    monkeypatch.setattr(roadmap, "child_env", lambda *args: {"safe": "env"})
    monkeypatch.setattr(release, "publishable", publishable)
    monkeypatch.setattr(release, "release", bump)
    monkeypatch.setattr(release, "journal_release", journal)
    monkeypatch.setattr(release, "publish", publish)
    assert asyncio.run(roadmap.ship(c)) == [] and calls == []
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="1.0.0"')
    assert asyncio.run(roadmap.ship(c)) == ["gate line"]
    assert calls == [("gate", c, "1.0.0")]
    calls.clear()
    passed[0] = True
    assert asyncio.run(roadmap.ship(c)) == ["gate line", "release: tagged v1.1.0 at sha"]
    assert calls == [("gate", c, "1.0.0"), ("release", c.repo, c.git, c.exec_, {"safe": "env"}, "minor"), ("journal", c.journal, "1.1.0", "sha")]
    calls.clear()
    c.config.release.publish = True
    assert asyncio.run(roadmap.ship(c))[-1] == "publish: uploaded 1.1.0 to PyPI"
    assert [x[0] for x in calls] == ["gate", "publishable", "release", "journal", "publish"]
    calls.clear()
    blocked[0] = True
    with pytest.raises(Refusal, match="blocked"):
        asyncio.run(roadmap.ship(c))
    assert [x[0] for x in calls] == ["gate", "publishable"]


def test_release_helpers(tmp_path):
    class Git:
        calls = []
        dirty = ""

        async def status_porcelain(self, *args):
            self.calls.append(args)
            return self.dirty

    git = Git()
    cfg = NS(release=NS(publish=True, pypi_token="TOKEN"))
    with pytest.raises(Refusal) as helper:
        asyncio.run(release.publishable(tmp_path, git, {}, cfg))
    with pytest.raises(Refusal) as full:
        asyncio.run(release.publish(tmp_path, git, None, None, {}, cfg))
    assert str(helper.value) == str(full.value) and git.calls == []
    git.dirty = " M x"
    with pytest.raises(Refusal, match="uncommitted tracked files"):
        asyncio.run(release.publishable(tmp_path, git, {"TOKEN": "secret"}, cfg))
    assert git.calls == [(tmp_path, "--untracked-files=no")]
    git.dirty = ""
    cfg.release.publish = False
    assert asyncio.run(release.publishable(tmp_path, git, {}, cfg)) is None
    journal = MemoryJournal()
    release.journal_release(journal, "0.4.0", "abc")
    assert [(e.type, e.body) for e in journal.events] == [(EventType.SIGNAL, {"signal": "release", "version": "0.4.0", "tag": "v0.4.0", "commit": "abc"})]
