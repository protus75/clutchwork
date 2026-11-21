import asyncio
from pathlib import Path

from clutch.__main__ import _run_meta
from clutch.metafill import MetaEntry, MetaReply
from tests.unit.test_meta_refresh import MemoryFS, config


def test_check_refresh_unchanged(capsys):
    fs = MemoryFS({"docs/a.md": "body\n"})
    args = (config(), Path("/repo"), fs, ["docs/a.md"], "abcdef123")
    assert asyncio.run(_run_meta("check", *args)) == 1
    assert capsys.readouterr().out == "docs/a.md: missing\n"
    assert asyncio.run(_run_meta("refresh", *args)) == 0
    assert capsys.readouterr().out == "docs/a.md\n"
    assert asyncio.run(_run_meta("check", *args)) == 1
    assert capsys.readouterr().out == "docs/a.md: empty_purpose\n"


def test_fill_exit_codes():
    async def good(paths, payload):
        return MetaReply(files={p: MetaEntry(purpose="Useful", relates=[], owner="engine") for p in paths})

    async def bad(paths, payload):
        return MetaReply(files={p: MetaEntry(purpose="bad\nline", relates=[], owner="engine") for p in paths})

    async def failed(paths, payload):
        return None

    failed.outcome = "gate_failed"
    for ask, expected in [(good, 0), (bad, 1), (failed, 1)]:
        fs = MemoryFS({"docs/a.md": "body\n"})
        assert asyncio.run(_run_meta("fill", config(), Path("/repo"), fs, ["docs/a.md"], "abcdef123", ask=ask)) == expected
