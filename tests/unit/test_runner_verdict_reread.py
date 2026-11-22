"""Operator keep admission observes dispatch during the git await."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that runner.verdict_locked refuses an operator keep when a re-offer marks the ticket running during the rev_parse await, and accepts the keep when there is no re-offer
# relates: [clutch/drain.py, clutch/journal.py, clutch/runner.py]
# owner: engine
# verified: 10f08d74
# hash: f1fee260c350e3be09872fe72ab373f87864445e3041d7f95b612caa5c7fad07

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from clutch import runner
from clutch.drain import record_reoffer
from clutch.journal import EventType, Journal
from tests.git_fake import GitFake


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    ticket = tmp_path / "tickets/work/ticket.md"
    ticket.parent.mkdir(parents=True)
    ticket.write_text("---\nstate: confirmed\n---\n")
    journal = Journal(tmp_path / "state", lambda: datetime(2026, 1, 1, tzinfo=UTC))
    runner.mark_running(journal, "work", "old-sha")
    journal.append(EventType.STATE_TRANSITION, {"to": "gate_failed", "routed": "reject_queue", "dispatch": "reject_queue"}, ticket="work")

    async def intake(*args, **kwargs):
        return SimpleNamespace(refused={})

    monkeypatch.setattr(runner, "intake", intake)
    return SimpleNamespace(repo=tmp_path, journal=journal, git=GitFake(), fs=None, config=SimpleNamespace())


def keeps(journal):
    return [e.body for e in journal.read() if e.ticket == "work" and e.type == EventType.SIGNAL and e.body.get("signal") == "reject_verdict" and e.body.get("verdict") == "keep"]


@pytest.mark.asyncio
async def test_reoffer_during_rev_parse_refuses_operator_keep(checkout):
    async def rev_parse(repo, ref):
        if ref == "HEAD:tickets/work/ticket.md":
            record_reoffer(checkout.journal, checkout.journal.read(), "work", "new-sha")
            runner.mark_running(checkout.journal, "work", "new-sha")
        return "new-sha"

    checkout.git = GitFake(rev_parse=rev_parse)
    with pytest.raises(runner.Refusal, match="is running"):
        await runner.verdict_locked("work", checkout, kill=False)
    assert [body["actor"] for body in keeps(checkout.journal)] == ["machine"]


@pytest.mark.asyncio
async def test_keep_without_reoffer_succeeds(checkout):
    async def rev_parse(repo, ref):
        return "new-sha"

    checkout.git = GitFake(rev_parse=rev_parse)
    assert await runner.verdict_locked("work", checkout, kill=False) == runner.EXIT_MERGED
    assert [body["actor"] for body in keeps(checkout.journal)] == ["operator"]
