# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks clutch release ship step order under the writer lock (gate, publishable check, bump, journal, publish, packages) for gate failure, publish off/on and no current release, plus its help text
# relates: [clutch/__main__.py, clutch/git.py, clutch/release.py, clutch/roadmap.py]
# owner: engine
# verified: 18f3cf87
# hash: d63b1fe26b7e517b8b2068c0a72799f5bfe3fa359afc7bc033f1d49828f4f637
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from clutch import __main__ as cli
from clutch import release, roadmap
from clutch.git import Git


@pytest.mark.parametrize("gate,enabled,current", [(False, True, "1.0.0"), (True, False, "1.0.0"), (True, True, "1.0.0"), (True, True, None)])
def test_ship(monkeypatch, capsys, gate, enabled, current):
    calls = []
    cfg = NS(state_dir=Path("/state"), release=NS(publish=enabled))
    monkeypatch.setattr(cli, "load_config", lambda *a, **k: cfg)
    monkeypatch.setattr(cli, "child_env", lambda *a, **k: {})

    class Lock:
        def __init__(self, *a, **k):
            pass

        def acquire(self):
            calls.append("lock")

        def release(self):
            calls.append("unlock")

    async def describe(*a):
        return "host"

    async def run_gate(*a):
        calls.append("gate")
        return gate, ["gate command failed" if not gate else "gate passed"]

    async def publishable(*a):
        calls.append("publishable")

    async def bump(*a):
        assert a[-2:] == ("minor", "2026-01-01")
        calls.append("bump")
        return "1.1.0", "sha"

    def journal(*a):
        calls.append("journal")

    async def publish(*a):
        calls.append("publish")
        return "1.1.0", [], True

    async def packages(*a):
        calls.append("packages")
        return ["package: built"]

    monkeypatch.setattr(cli, "Lockfile", Lock)
    monkeypatch.setattr(Git, "describe", describe)
    monkeypatch.setattr(roadmap, "current_release", lambda _: current)
    monkeypatch.setattr(roadmap, "run_gate", run_gate)
    monkeypatch.setattr(release, "publishable", publishable)
    monkeypatch.setattr(release, "release", bump)
    monkeypatch.setattr(release, "journal_release", journal)
    monkeypatch.setattr(release, "publish", publish)
    monkeypatch.setattr(release, "run_packages", packages)
    code = cli.main(["release", "ship"], cwd=Path("/repo"), env={}, clock=lambda: datetime(2026, 1, 1, tzinfo=UTC))
    out = capsys.readouterr()
    if current is None:
        assert code == 2 and "no current release" in out.err
        assert calls == ["lock", "unlock"]
    elif not gate:
        assert code == 1 and "gate command failed" in out.out
        assert calls == ["lock", "gate", "unlock"]
    else:
        assert code == 0 and "package: built" in out.out
        assert calls == ["lock", "gate"] + (["publishable"] if enabled else []) + ["bump", "journal"] + (["publish"] if enabled else []) + ["packages", "unlock"]


def test_help(capsys):
    with pytest.raises(SystemExit):
        cli._parser().parse_args(["release", "ship", "--help"])
    text = capsys.readouterr().out
    assert all(word in text for word in ["Reads:", "Writes:", "Lock:", "Exit codes:", "gate"])
    assert "Reads: Config, roadmap gate" in text
    assert "Writes: Gate and release journal signals" in text
    assert "Lock: Writer lock" in text
    assert "Examples:\nclutch release ship\n" in text
