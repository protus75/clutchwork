# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify squash merges carry ticket config.yaml edits while keeping the owner's uncommitted local config.yaml edits, and still refuse other dirty paths
# relates: [tests/integration/test_mergequeue.py]
# owner: tests/integration/test_mergequeue.py
# verified: 92889fdb
# hash: ad74242aca1d461a1bb0eab1e05fc6f72026acf909be5ac89d4c98f51ffa9002
import asyncio

import pytest

from tests.daemon_helpers import admission, ctx, ready

pytestmark = pytest.mark.disk_io_skip


def test_config_local_merge(ctx):
    async def exercise():
        base = (ctx.repo / "config.yaml").read_text()
        ticket = await ready(ctx, changes={"config.yaml": base.replace("schema_version: 1", "schema_version: 1\nticket: yes")}, fence=("config.yaml",))
        (ctx.repo / "config.yaml").write_text(base + "\nowner: yes\n")
        result = await admission(ctx, ticket)
        assert result.outcome == "ok", result.findings
        committed = await ctx.git._run(ctx.repo, "show", "HEAD:config.yaml")
        assert "ticket: yes" in committed and "owner: yes" not in committed
        working = (ctx.repo / "config.yaml").read_text()
        assert "ticket: yes" in working and "owner: yes" in working

    asyncio.run(exercise())


def test_unrelated_ticket_preserves_config(ctx):
    async def exercise():
        ticket = await ready(ctx)
        config = ctx.repo / "config.yaml"
        edited = config.read_text() + "\nowner: yes\n"
        config.write_text(edited)
        result = await admission(ctx, ticket)
        assert result.outcome == "ok", result.findings
        assert config.read_text() == edited

    asyncio.run(exercise())


def test_other_dirty_path_refused(ctx):
    async def exercise():
        ticket = await ready(ctx)
        (ctx.repo / "clutch/thing.py").write_text("owner edit\n")
        result = await admission(ctx, ticket)
        assert result.outcome != "ok" and any(f.code == "dirty_checkout" for f in result.findings)

    asyncio.run(exercise())
