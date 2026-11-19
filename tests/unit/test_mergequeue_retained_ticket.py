from types import SimpleNamespace

import pytest

from clutch import stages
from clutch.mergequeue import MergeQueue

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


class Git:
    def __init__(self, review):
        self.review = review
        self.shows = []
        self.status = ""
        self.head = "head-sha"
        self.lift_review = "review-sha"

    async def _run(self, repo, verb, ref):
        assert verb == "show"
        self.shows.append(ref)
        return self.review if ref.endswith("/review.md") else TICKET

    async def rev_parse(self, repo, ref):
        if ref == "HEAD":
            return self.head
        if ref == "work":
            return "head-sha"
        return self.lift_review if ref.startswith("c1:") else "review-sha"

    async def status_porcelain(self, *args):
        return self.status


def rig(tmp_path, *, verdict="approve", reviewed_sha="reviewed", lifts=()):
    (tmp_path / "context.txt").write_text("context")
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    cls = stages.ApprovedInvoice if verdict == "approve" else stages.SnagList
    review = cls(
        verdict=verdict, stem="work", reviewed_sha=reviewed_sha, summary="reviewed", findings=[], spec_version="1", produced_by_spec_version=1, produced_at_sha="abc", provider=None, model=None
    )
    git = Git(stages.render_review(review))
    effects = SimpleNamespace(recorded=lambda key: list(lifts))
    ctx = SimpleNamespace(repo=tmp_path, worktree=lambda stem: worktree, git=git, driver=SimpleNamespace(effects=effects))
    receipt = {"attempt": 2, "reviewed_sha": "reviewed", "review_provider": None, "review_model": None}
    return MergeQueue(ctx, escalate=lambda event: None), git, receipt, worktree


@pytest.mark.asyncio
async def test_retained_ticket_uses_main(tmp_path):
    queue, git, receipt, _ = rig(tmp_path)
    ticket = await queue.retained_ticket("work", receipt)
    assert ticket.stem == "work"
    assert git.shows == ["main:tickets/work/ticket.md", "main:tickets/work/review.md"]


@pytest.mark.asyncio
async def test_retained_ticket_uses_lift_and_checks_review(tmp_path):
    queue, git, receipt, _ = rig(tmp_path, lifts=[{"commit": "c1"}])
    assert (await queue.retained_ticket("work", receipt)).stem == "work"
    assert git.shows[0] == "c1:tickets/work/ticket.md"
    git.lift_review = "different"
    with pytest.raises(ValueError, match="retained admission work is unavailable.*restore the retained committed ticket"):
        await queue.retained_ticket("work", receipt)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["sha", "snag", "missing", "dirty", "head"])
async def test_unavailable_retained_ticket(tmp_path, failure):
    queue, git, receipt, worktree = rig(tmp_path, verdict="snag" if failure == "snag" else "approve", reviewed_sha="other" if failure == "sha" else "reviewed")
    if failure == "missing":
        worktree.rmdir()
    if failure == "dirty":
        git.status = " M code.py\0"
    if failure == "head":
        git.head = "different"
    with pytest.raises(ValueError, match="retained admission work is unavailable.*restore the retained committed ticket"):
        await queue.retained_ticket("work", receipt)
