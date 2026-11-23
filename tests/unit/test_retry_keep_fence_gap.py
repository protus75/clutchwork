# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that an Implement retry keeps the existing worktree only after an Implement premise_failed transition marked fence_gap, with no later merge-conflict rerun signal.
# relates: [clutch/journal.py, clutch/stages.py, tests/fakes.py]
# owner: engine
# verified: 800fa1a3
# hash: dcd9ed81db6e56e18e2b6c4e9d923c6fbe68739887ee0252187b746fa720f285
import asyncio
from types import SimpleNamespace

import pytest

from clutch import stages
from clutch.journal import EventType
from tests.fakes import FakeJournal


@pytest.mark.parametrize(
    ("outcome", "stage", "marker", "conflict", "expected"),
    [
        ("premise_failed", "implement", True, False, True),
        ("premise_failed", "implement", False, False, False),
        ("premise_failed", "review", True, False, False),
        ("incomplete", "implement", True, False, False),
        ("timeout", "implement", True, False, False),
        ("premise_failed", "implement", True, True, False),
    ],
)
def test_keep_after_fence_gap(monkeypatch, outcome, stage, marker, conflict, expected):
    journal = FakeJournal()
    body = {"to": outcome, "stage": stage}
    if marker:
        body["fence_gap"] = True
    journal.append(EventType.STATE_TRANSITION, body, ticket="feature")
    if conflict:
        journal.append(EventType.SIGNAL, {"signal": "merge_conflict_rerun"}, ticket="feature")
    observed = []

    async def prepare(ctx, stem, *, keep=False):
        observed.append(keep)
        raise StopAsyncIteration

    monkeypatch.setattr(stages, "prepare_worktree", prepare)
    with pytest.raises(StopAsyncIteration):
        asyncio.run(stages.implement(SimpleNamespace(driver=SimpleNamespace(journal=journal)), SimpleNamespace(stem="feature"), attempt=1))
    # Wrong: keep every Implement failure, ignore the marker or ignore a later conflict.
    assert observed == [expected]
