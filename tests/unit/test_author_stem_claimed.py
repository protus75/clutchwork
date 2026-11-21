"""Author rechecks ticket ownership after review."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Author rechecks ticket ownership after review.
# relates: [clutch/author.py, clutch/seams.py, tests/fakes.py, tests/unit/test_retro_recurrence.py]
# owner: engine
# verified: 9c24a9bd
# hash: 5cf64f7de2aeaab6446611b45f815ad7e68d660c236bf69049df3610e9670710

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import author
from clutch.seams import LocalFileSystem
from tests.fakes import FakeJournal
from tests.unit.test_retro_recurrence import message


@pytest.mark.asyncio
@pytest.mark.parametrize("claim", [True, False])
async def test_author_rechecks_stem_after_gate(tmp_path, monkeypatch, claim):
    path = tmp_path / "tickets/sample-row/ticket.md"
    original = b"human-owned ticket\n"
    reply = author.AuthorReply(stem="sample-row", ticket="authored ticket")
    decline = AsyncMock(return_value=author.AuthorOutcome(declined="declined-claim"))
    commit = AsyncMock(return_value="commit-sha")

    async def commit_edit(repo, msg, *, only, edit):
        await edit()
        return await commit(repo, msg, only=only)

    async def run(stage, *args, **kwargs):
        await stage.review(reply, 1)
        if claim:
            path.parent.mkdir(parents=True)
            path.write_bytes(original)
        return SimpleNamespace(outcome="ok", artifact=reply)

    async def review(*args, **kwargs):
        return SimpleNamespace(verdict="approve", findings=[], calls=1, ticket_sha="review-sha", provider="fake", model="fake", spec_version="1", input_identity=None)

    async def effect(action, **kwargs):
        return await action()

    monkeypatch.setattr(Path, "read_text", lambda self: "spec")
    monkeypatch.setattr(author, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(effort="medium")))
    monkeypatch.setattr(author, "list_open_tickets", AsyncMock(return_value="none"))
    monkeypatch.setattr(author, "review_with_identity", review)
    monkeypatch.setattr(author, "failure_declined", decline)
    monkeypatch.setattr(author, "stamp", lambda text, *args: text)
    monkeypatch.setattr(author, "validate_ticket", lambda *args: SimpleNamespace(scope_fence=(), frontmatter=SimpleNamespace(gate_bypass=[])))
    monkeypatch.setattr(author, "resolve_baseline", lambda *args, **kwargs: SimpleNamespace(binds=False))
    monkeypatch.setattr(author, "start_state", lambda *args, **kwargs: "draft")
    checkout = SimpleNamespace(
        repo=tmp_path,
        git=SimpleNamespace(ls_files=AsyncMock(return_value=[]), commit_edit=commit_edit),
        fs=LocalFileSystem(),
        journal=FakeJournal(),
        config=SimpleNamespace(state_dir=tmp_path, review=SimpleNamespace(coverage_map=None), routing_default_tier="medium"),
    )
    box = SimpleNamespace(root=tmp_path / "box", resolve=lambda *args: None)
    driver = SimpleNamespace(run=run, effects=SimpleNamespace(run=effect))
    item = message().model_copy(update={"message_class": "suggestion", "proposed_spec_paths": [], "verdict": SimpleNamespace(rationale="test")})

    result = await author.author(checkout, driver, box, item, 1)

    if claim:
        assert path.read_bytes() == original
        commit.assert_not_awaited()
        assert result == author.AuthorOutcome(declined="declined-claim")
        assert "sample-row" in decline.await_args.args[-1] and "claimed" in decline.await_args.args[-1]
    else:
        assert path.read_bytes() == b"authored ticket"
        commit.assert_awaited_once_with(tmp_path, "clutch(sample-row): ticket", only=["tickets/sample-row/ticket.md"])
        assert result == author.AuthorOutcome(stem="sample-row")
        decline.assert_not_awaited()
