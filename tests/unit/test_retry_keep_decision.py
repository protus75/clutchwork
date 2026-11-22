# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests Implement keeps the prior branch only after a Check or Review gate failure without a merge conflict rerun
# relates: [clutch/journal.py, clutch/stages.py, tests/fakes.py]
# owner: clutch/stages.py
# verified: 52843322
# hash: 956b9b3124813b56add681b36cedec32a55769a678149dd9d856a5b00e5ff2a2
import asyncio
from types import SimpleNamespace

import pytest

from clutch import stages
from clutch.journal import EventType
from tests.fakes import FakeJournal


@pytest.mark.parametrize(
    ("terminal", "stage", "conflict", "expected"),
    [
        (None, None, False, False),
        ("gate_failed", "check", False, True),
        ("gate_failed", "review", False, True),
        ("premise_failed", "implement", False, False),
        ("incomplete", "implement", False, False),
        ("timeout", "implement", False, False),
        ("gate_failed", "check", True, False),
    ],
)
def test_implement_keep(monkeypatch, terminal, stage, conflict, expected):
    journal = FakeJournal()
    if terminal:
        journal.append(EventType.STATE_TRANSITION, {"to": terminal, "stage": stage}, ticket="feature")
    if conflict:
        journal.append(EventType.SIGNAL, {"signal": "merge_conflict_rerun"}, ticket="feature")
    observed = []

    async def prepare(ctx, stem, *, keep=False):
        observed.append((stem, keep))
        raise StopAsyncIteration

    monkeypatch.setattr(stages, "prepare_worktree", prepare)
    ctx = SimpleNamespace(driver=SimpleNamespace(journal=journal))
    with pytest.raises(StopAsyncIteration):
        asyncio.run(stages.implement(ctx, SimpleNamespace(stem="feature"), attempt=1))
    assert observed == [("feature", expected)]
