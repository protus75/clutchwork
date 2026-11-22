# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Retained admission loads the ticket from main or a lift commit, and refuses on a review SHA mismatch, a snag verdict, a missing worktree, a dirty worktree, or a moved HEAD
# relates: [clutch/mergequeue.py, clutch/stages.py]
# owner: engine
# verified: 452057e3
# hash: c3f5ca2e4e4a3fdaad718222b291e5fe4b778643a41731962f79643808222708
from types import SimpleNamespace

import pytest

from clutch import stages
from clutch.mergequeue import MergeQueue
from tests.git_fake import GitFake

TICKET = """---
state: confirmed
source: human
priority: P2
kind: feature
---

## Depends on
none

## Context
- context.txt

## Goal / Why
Create one thing.

## Boundary contract
none
- reason: unchanged behavior

## Scope in / Scope out
In: thing. Out: the rest.

## Scope fence
- thing.py

## Acceptance criteria
1. `thing.py` exists, checked by `test -f thing.py`.

## Verification
```
test -f thing.py
```

## Definition of rejected
Needs an outside file.

## Time budget
- expected: 10m
- stuck: 20m
"""


def rig(tmp_path, *, verdict="approve", reviewed_sha="reviewed", lifts=()):
    (tmp_path / "context.txt").write_text("context")
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    cls = stages.ApprovedInvoice if verdict == "approve" else stages.SnagList
    review = cls(
        verdict=verdict, stem="work", reviewed_sha=reviewed_sha, summary="reviewed", findings=[], spec_version="1", produced_by_spec_version=1, produced_at_sha="abc", provider=None, model=None
    )
    state = SimpleNamespace(review=stages.render_review(review), shows=[], status="", head="head-sha", lift_review="review-sha")

    def run(repo, verb, ref):
        assert verb == "show"
        state.shows.append(ref)
        return state.review if ref.endswith("/review.md") else TICKET

    def rev_parse(repo, ref):
        if ref == "HEAD":
            return state.head
        if ref == "work":
            return "head-sha"
        return state.lift_review if ref.startswith("c1:") else "review-sha"

    git = GitFake(_run=run, rev_parse=rev_parse, status_porcelain=lambda *args: state.status)
    git.state = state
    effects = SimpleNamespace(recorded=lambda key: list(lifts))
    ctx = SimpleNamespace(repo=tmp_path, worktree=lambda stem: worktree, git=git, driver=SimpleNamespace(effects=effects))
    receipt = {"attempt": 2, "reviewed_sha": "reviewed", "review_provider": None, "review_model": None}
    return MergeQueue(ctx, escalate=lambda event: None), git, receipt, worktree


@pytest.mark.asyncio
async def test_retained_ticket_uses_main(tmp_path):
    queue, git, receipt, _ = rig(tmp_path)
    ticket = await queue.retained_ticket("work", receipt)
    assert ticket.stem == "work"
    assert git.state.shows == ["main:tickets/work/ticket.md", "main:tickets/work/review.md"]


@pytest.mark.asyncio
async def test_retained_ticket_uses_lift_and_checks_review(tmp_path):
    queue, git, receipt, _ = rig(tmp_path, lifts=[{"commit": "c1"}])
    assert (await queue.retained_ticket("work", receipt)).stem == "work"
    assert git.state.shows[0] == "c1:tickets/work/ticket.md"
    git.state.lift_review = "different"
    with pytest.raises(ValueError, match="retained admission work is unavailable.*restore the retained committed ticket"):
        await queue.retained_ticket("work", receipt)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["sha", "snag", "missing", "dirty", "head"])
async def test_unavailable_retained_ticket(tmp_path, failure):
    queue, git, receipt, worktree = rig(tmp_path, verdict="snag" if failure == "snag" else "approve", reviewed_sha="other" if failure == "sha" else "reviewed")
    if failure == "missing":
        worktree.rmdir()
    if failure == "dirty":
        git.state.status = " M code.py\0"
    if failure == "head":
        git.state.head = "different"
    with pytest.raises(ValueError, match="retained admission work is unavailable.*restore the retained committed ticket"):
        await queue.retained_ticket("work", receipt)
