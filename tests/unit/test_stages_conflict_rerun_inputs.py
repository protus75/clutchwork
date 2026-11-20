# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test stages conflict rerun inputs
# relates: [clutch/artifacts.py, clutch/journal.py, clutch/seams.py, clutch/stages.py]
# owner: engine
# verified: 9a610809
# hash: 6e3232dffc80b16a26d02eab36e502180de76a03b8e306f1a254a70be4610341
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch.artifacts import Finding
from clutch.journal import Event, EventType
from clutch.seams import LocalFileSystem
from clutch.stages import ApprovedInvoice, lift_prior_diff, prior_attempts, render_review


def event(stem, attempt):
    return Event(1, EventType.SIGNAL, "now", stem, None, {"signal": "merge_conflict_rerun", "attempt": attempt})


def test_marker_reads_latest_attempt_without_terminal(tmp_path):
    root = tmp_path / "tickets" / "item"
    (root / "attempts" / "2").mkdir(parents=True)
    (root / "run.md").write_text("discarded decisions")
    (root / "attempts" / "2" / "prior.diff").write_text("retained patch")
    finding = Finding(code="review", message="approved observation", paved_road="keep it")
    review = ApprovedInvoice(
        verdict="approve", produced_by_spec_version=1, produced_at_sha="abc", stem="item", reviewed_sha="abc", summary="good", findings=[finding], spec_version="1", provider=None, model=None
    )
    (root / "review.md").write_text(render_review(review))
    history = [event("item", 1), event("item", 2), event("other", 1)]
    ctx = SimpleNamespace(repo=tmp_path, driver=SimpleNamespace(journal=SimpleNamespace(read=lambda: history)))
    result = prior_attempts(ctx, "item")
    assert "conflict_rerun" in result and "discarded decisions" in result and "retained patch" in result and "approved observation" in result
    (root / "attempts" / "2" / "prior.diff").unlink()
    assert "discarded decisions" in prior_attempts(ctx, "item")
    history.clear()
    assert prior_attempts(ctx, "item") is None


@pytest.mark.asyncio
async def test_lift_excludes_conflicted_sections(tmp_path):
    async def effect(action, *, key, ticket):
        assert (key, ticket) == ("ticket-plane/item/3/prior-diff", "item")
        return await action()

    git = SimpleNamespace(commit=AsyncMock(return_value="commit-sha"))
    ctx = SimpleNamespace(repo=tmp_path, fs=LocalFileSystem(), git=git, driver=SimpleNamespace(effects=SimpleNamespace(run=effect)))
    diff = "diff --git a/bad b/bad\n--- a/bad\n+++ b/bad\n@@ -1 +1 @@\n-old\n+conflicted\ndiff --git a/good b/good\n--- a/good\n+++ b/good\n@@ -1 +1 @@\n-old\n+retained\n"
    sha = await lift_prior_diff(ctx, "item", attempt=3, diff=diff, conflicted=["bad"])
    saved = (tmp_path / "tickets/item/attempts/3/prior.diff").read_text()
    assert sha == "commit-sha"
    assert saved == diff[diff.index("diff --git a/good") :]
    git.commit.assert_awaited_once_with(tmp_path, "clutch(item): prior-diff", only=["tickets/item/attempts/3/prior.diff"])
    assert await lift_prior_diff(ctx, "item", attempt=3, diff=diff, conflicted=["bad", "good"]) is None
