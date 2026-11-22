"""Merge index refresh behavior."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Post-merge index refresh: skipped without an index, logs built/findings/failed outcomes, never breaks the squash, and loads extensions without installing them
# relates: [clutch/evidence/store.py, clutch/merge.py, clutch/providers.py, clutch/seams.py]
# owner: engine
# verified: 452057e3
# hash: cbf522d5ae012143cb7efe6c3604c9696034237ef1afb03ba88db98efa78e698

import asyncio
import json
from datetime import UTC, datetime
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import duckdb
import pytest

from clutch import merge
from clutch.evidence.store import EvidenceStore
from clutch.providers import child_env
from clutch.seams import LocalFileSystem
from tests.git_fake import GitFake


def context(tmp_path):
    config = NS(state_dir=tmp_path, index=NS(embed=None), providers=[NS(auth="SECRET")], release=NS(pypi_token="TOKEN"))
    driver = NS(redactor=NS(scrub=lambda s: s), clock=lambda: datetime(2026, 1, 1, tzinfo=UTC))
    return NS(config=config, repo=tmp_path, fs=LocalFileSystem(), git=GitFake(), exec_=object(), env={"SECRET": "hidden", "KEEP": "yes"}, driver=driver)


def records(ctx):
    return [json.loads(line) for line in (ctx.config.state_dir / "engine.log").read_text().splitlines()]


@pytest.mark.asyncio
async def test_outcomes(tmp_path, monkeypatch):
    ctx = context(tmp_path)
    build = AsyncMock(return_value=[])
    monkeypatch.setattr(merge.index, "build", build)
    assert await merge.refresh_index(ctx) is None
    assert build.await_count == 0
    assert not (tmp_path / "index.duckdb").exists()
    assert not (tmp_path / "engine.log").exists()
    (tmp_path / "index.duckdb").touch()
    assert await merge.refresh_index(ctx) is None
    assert build.await_count == 1
    args, kwargs = build.await_args
    assert args[0] is ctx.config and args[1] == ctx.repo
    assert kwargs["fs"] is ctx.fs and kwargs["git"] is ctx.git and kwargs["exec_"] is ctx.exec_
    assert kwargs["creator"] is merge.MERGE_CREATOR and isinstance(kwargs["store"], EvidenceStore)
    assert kwargs["env"] == child_env(ctx.env, ctx.config) == {"KEEP": "yes"}
    assert [(r["event"], r["outcome"]) for r in records(ctx)] == [("index_refresh", "built")]
    (tmp_path / "engine.log").unlink()
    build.return_value = ["git_failed: x"]
    assert await merge.refresh_index(ctx) is None
    assert [(r["outcome"], r["findings"]) for r in records(ctx)] == [("built_with_findings", ["git_failed: x"])]


@pytest.mark.asyncio
async def test_failures(tmp_path, monkeypatch):
    ctx = context(tmp_path)
    (tmp_path / "index.duckdb").touch()
    build = AsyncMock()
    monkeypatch.setattr(merge.index, "build", build)
    for exc in (RuntimeError("bad"), duckdb.Error("bad"), OSError("bad")):
        build.side_effect = exc
        assert await merge.refresh_index(ctx) is None
        row = records(ctx).pop()
        assert (row["event"], row["outcome"], row["error"], row["detail"]) == ("index_refresh", "failed", type(exc).__name__, "bad")
        (tmp_path / "engine.log").unlink()
    ctx.fs = NS(size=lambda p: 1)
    assert await merge.refresh_index(ctx) is None
    assert [(r["outcome"], r["error"]) for r in records(ctx)] == [("failed", "AttributeError")]
    (tmp_path / "engine.log").unlink()
    ctx.config = NS()
    build.reset_mock()
    assert await merge.refresh_index(ctx) is None
    assert build.await_count == 0 and not (tmp_path / "engine.log").exists()
    ctx = context(tmp_path)
    build.side_effect = asyncio.CancelledError()
    with pytest.raises(asyncio.CancelledError):
        await merge.refresh_index(ctx)
    (tmp_path / "engine.log").mkdir()
    build.side_effect = RuntimeError("bad")
    assert await merge.refresh_index(ctx) is None


def test_creator():
    for kind in ("vss", "fts"):
        conn = NS(execute=lambda sql: calls.append(sql))
        calls = []
        assert merge.MERGE_CREATOR.load(conn, kind) == []
        assert calls == [f"LOAD {kind}"]
        calls.clear()
        assert merge.MERGE_CREATOR.create(conn, kind) == [] and calls == []

        def fail(sql):
            raise duckdb.Error("offline")

        assert merge.MERGE_CREATOR.load(NS(execute=fail), kind) == [f"{kind} unavailable: offline"]


@pytest.mark.asyncio
async def test_squash_order_and_failure(tmp_path, monkeypatch):
    ctx = context(tmp_path)
    events = []
    ctx.driver.journal = NS(read=lambda: [], append=lambda typ, body, **kw: events.append((typ, body, kw)))

    async def run(fn, **kwargs):
        return await fn()

    ctx.driver.effects = NS(run=run)
    ctx.git = GitFake(status_porcelain="", diff_names=["a"], merge_squash="commit", rev_parse="head")
    ticket = NS(stem="work", frontmatter=NS(source="human"), sections={"Goal / Why": "goal"})
    original = merge.refresh_index

    async def hook(ctx):
        events.append("hook")
        await original(ctx)

    monkeypatch.setattr(merge, "refresh_index", hook)
    first = await merge.write_squash(ctx, ticket, "reviewed", attempt=1)
    first_events = events[:]
    assert first_events[0][1]["to"] == "merged" and first_events[1] == "hook"
    events.clear()
    (tmp_path / "index.duckdb").touch()
    monkeypatch.setattr(merge.index, "build", AsyncMock(side_effect=RuntimeError("bad")))
    second = await merge.write_squash(ctx, ticket, "reviewed", attempt=1)
    assert second == first and events == first_events
    assert records(ctx)[0]["outcome"] == "failed"


@pytest.mark.asyncio
async def test_real_build(tmp_path, monkeypatch):
    ctx = context(tmp_path)
    (tmp_path / "a.md").write_text("# Heading\ncontent\n")
    duckdb.connect(str(tmp_path / "index.duckdb")).close()
    ctx.git = GitFake(ls_files=["a.md"], ticket_touches=[])
    loads, statements = [], []
    monkeypatch.setattr(merge.MERGE_CREATOR, "load", lambda conn, kind: (loads.append(kind), [])[1])
    monkeypatch.setattr(merge, "EvidenceStore", lambda *args: NS(call_keys=lambda prefix: []))
    original = merge.index.build

    class Connection:
        def __init__(self, path):
            self.conn = duckdb.connect(path)

        def execute(self, sql, *args):
            statements.append(sql)
            return self.conn.execute(sql, *args)

        def close(self):
            self.conn.close()

    async def build(*args, **kwargs):
        return await original(*args, **kwargs, connect=Connection)

    monkeypatch.setattr(merge.index, "build", build)
    await merge.refresh_index(ctx)
    conn = duckdb.connect(str(tmp_path / "index.duckdb"))
    try:
        assert conn.execute("SELECT path FROM files").fetchall() == [("a.md",)]
    finally:
        conn.close()
    assert loads == ["fts"] and not any(s.upper().startswith("INSTALL") for s in statements)
    assert [r["outcome"] for r in records(ctx)] == ["built"]
