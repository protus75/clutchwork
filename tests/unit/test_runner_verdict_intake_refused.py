"""Verdict admission contains intake refusals for the serve worker."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests checking that verdict admission (confirm/reject) and Serve.apply_verdict return an IntakeRefused error as a refusal result and log a verdict_refused event, and that an ordinary Refusal is still returned.
# relates: [clutch/artifacts.py, clutch/runner.py, clutch/serve.py, clutch/tickets.py, tests/fakes.py, tests/git_fake.py]
# owner: engine
# verified: 334cd5c4
# hash: b30b9b0e4cd666daa25a45082e919b69ef04d053e9f6df856f79060217f01c32

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import runner
from clutch.artifacts import Finding
from clutch.serve import Serve
from clutch.tickets import IntakeRefused
from tests.fakes import FakeClock, FakeJournal
from tests.git_fake import GitFake


@pytest.fixture
def checkout():
    class Repo:
        def __truediv__(self, path):
            return self

    return SimpleNamespace(repo=Repo(), journal=FakeJournal(FakeClock()), git=GitFake(rev_parse="base"))


@pytest.fixture
def intake_refusal(monkeypatch):
    error = IntakeRefused(Finding(code="intake_stray", message="staged config.yaml", paved_road="unstage it"))
    monkeypatch.setattr(runner, "verdict_locked", AsyncMock(side_effect=error))
    return str(error)


@pytest.mark.asyncio
@pytest.mark.parametrize("verb", ["confirm", "reject"])
async def test_admission_returns_intake_refusal(checkout, intake_refusal, verb):
    result = await runner.apply_admission("work", verb, "key", "operator", checkout)
    assert result == {"refusal": intake_refusal}


@pytest.mark.asyncio
async def test_serve_logs_intake_refusal(checkout, intake_refusal):
    events = []
    owner = Serve.__new__(Serve)
    owner.checkout = checkout
    owner.log = SimpleNamespace(event=lambda name, **fields: events.append((name, fields)))
    result = await owner.apply_verdict("work", "reject", "key", "operator")
    assert result == {"refusal": intake_refusal}
    assert events == [("verdict_refused", {"stem": "work", "verb": "reject", "reason": intake_refusal})]


@pytest.mark.asyncio
async def test_admission_still_returns_refusal(checkout, monkeypatch):
    monkeypatch.setattr(runner, "verdict_locked", AsyncMock(side_effect=runner.Refusal("ticket is running", "wait")))
    result = await runner.apply_admission("work", "reject", "key", "operator", checkout)
    assert result == {"refusal": "ticket is running -- wait"}
