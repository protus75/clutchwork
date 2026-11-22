# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verifies requisition prior_review picks the latest matching verdict for a stem, renders its findings with a ticket diff, and returns FIRST_REVIEW when none exists
# relates: [clutch/journal.py, clutch/requisition.py]
# owner: engine
# verified: df236100
# hash: 89a4efbe1232ccc5013e6306cbd3352ef24a8de88df0b555c25c29ab3ec26911
import asyncio
import inspect

from clutch.journal import Event, EventType
from clutch.requisition import FIRST_REVIEW, prior_review, render_prior_review, review_ticket
from tests.git_fake import GitFake


def event(stem, body, type=EventType.SIGNAL):
    return Event(1, type, "time", stem, None, body)


def verdict(stem, sha, findings, verdict="snag"):
    return event(stem, {"signal": "requisition_verdict", "ticket_sha": sha, "verdict": verdict, "findings": findings})


def test_prior_is_required():
    assert inspect.signature(review_ticket).parameters["prior"].default is inspect.Parameter.empty


def test_missing_or_legacy_verdict_returns_first_review():
    git = GitFake(_run=lambda repo, *args: {"old-sha": "a\n", "new-sha": "later\n"}[args[1]])
    for events in ([], [verdict("other", "old-sha", [])], [event("one", {"signal": "requisition_verdict"})], [event("one", {"signal": "other", "findings": []})]):
        assert asyncio.run(prior_review(git, "repo", events, "one", "current")) == FIRST_REVIEW
    assert git.calls == []


def test_findings_and_diff_use_latest_matching_verdict():
    git = GitFake(_run=lambda repo, *args: {"old-sha": "a\n", "new-sha": "later\n"}[args[1]])
    events = [verdict("one", "new-sha", [{"code": "old", "message": "obsolete"}]), verdict("one", "old-sha", [{"code": "fence_gap", "message": "missing x"}])]
    result = asyncio.run(prior_review(git, "repo", events, "one", "a\nb\n"))
    assert "Verdict: snag" in result
    assert "- [fence_gap] missing x" in result
    assert "+b" in result
    assert "obsolete" not in result
    assert git.calls == [("_run", ("repo", "show", "old-sha"), {})]


def test_approval_with_no_findings_and_unchanged_text():
    git = GitFake(_run=lambda repo, *args: {"old-sha": "a\n", "new-sha": "later\n"}[args[1]])
    result = asyncio.run(prior_review(git, "repo", [verdict("one", "old-sha", [], "approve")], "one", "a\n"))
    assert "Verdict: approve" in result
    assert "- none" in result
    assert "(unchanged)" in result


def test_shared_renderer_matches_recorded_review():
    findings = [{"code": "gap", "message": "missing\ncase"}]
    recorded = asyncio.run(prior_review(GitFake(_run=lambda repo, *args: {"old-sha": "a\n", "new-sha": "later\n"}[args[1]]), "repo", [verdict("one", "old-sha", findings)], "one", "a\nnew\n"))
    assert render_prior_review("snag", findings, "a\n", "a\nnew\n") == recorded
    assert "- [gap] missing case" in recorded and "+new" in recorded
