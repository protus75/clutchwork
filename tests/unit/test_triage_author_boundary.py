# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test triage author boundary
# relates: [clutch/journal.py, clutch/triage.py]
# owner: engine
# verified: 9a610809
# hash: 3b7bc8ca547745e841c5237de5e50b2308412b3a26a64126dd26b7959d6b1468
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from clutch import triage
from clutch.journal import EventType


class Journal:
    def __init__(self, events):
        self.events = events
        self.calls = 0

    def read(self):
        self.calls += 1
        return list(self.events)


def event(type, body, key=None):
    return SimpleNamespace(type=type, body=body, key=key)


def settle(monkeypatch, events):
    journal = Journal(events)
    checkout = SimpleNamespace(journal=journal, repo=None)
    message = SimpleNamespace(id="message-1", reopen=True, verdict=SimpleNamespace(verdict="author", produced_by_spec_version="1.0"))
    box = SimpleNamespace(pending=lambda: [message])
    spec = SimpleNamespace(meta=SimpleNamespace(version="1.0"))
    author = AsyncMock(return_value=SimpleNamespace(stem="new-ticket", declined=None))
    declined = AsyncMock(return_value=SimpleNamespace(stem=None, declined="declined-message-1"))
    monkeypatch.setattr(triage, "recover_retro_ticket", AsyncMock(return_value=None))
    monkeypatch.setattr(triage, "read_registry", lambda repo: [])
    monkeypatch.setattr(triage, "author", author)
    monkeypatch.setattr(triage, "failure_declined", declined)
    asyncio.run(triage._settle_pass(checkout, None, box, spec, [], 0, frozenset()))
    return journal, author, declined


def signal():
    return event(EventType.SIGNAL, {"signal": "author_invoked", "message": "message-1"})


def boundary():
    return event(EventType.EFFECT_INTENT, {"reopened": True}, "retro-recurrence/message-1/new")


def test_reopened_stale_author_invoked_calls_author(monkeypatch):
    _, author, declined = settle(monkeypatch, [signal(), boundary()])
    author.assert_awaited_once()
    declined.assert_not_awaited()


def test_author_invoked_after_boundary_declines(monkeypatch):
    _, author, declined = settle(monkeypatch, [boundary(), signal()])
    declined.assert_awaited_once()
    author.assert_not_awaited()


def test_guard_reads_journal_once(monkeypatch):
    journal, author, declined = settle(monkeypatch, [signal(), boundary()])
    assert journal.calls == 1
    author.assert_awaited_once()
    declined.assert_not_awaited()
