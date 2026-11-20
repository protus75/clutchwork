# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test shared fakes adoption b
# relates: [tests/fakes.py, tests/integration/test_journal.py, tests/unit/test_retro_recurrence.py, tests/unit/test_suggest_box.py]
# owner: engine
# verified: 96e46658
# hash: b6555b0e1f9d6bd98a75218eec9ec24579413103ab4be48e55dd0b21323eaf12
from datetime import UTC, datetime, timedelta

from tests import fakes
from tests.integration import test_journal
from tests.unit import test_retro_recurrence, test_suggest_box


def test_shared_fake_identities():
    assert test_journal.FakeClock is fakes.FakeClock
    assert test_suggest_box.FakeFileSystem is fakes.FakeFileSystem
    assert test_retro_recurrence.FakeJournal is fakes.FakeJournal
    assert not hasattr(test_suggest_box, "MemoryFS")
    assert not hasattr(test_retro_recurrence, "MemoryJournal")


def test_journal_clock_uses_start_and_advances():
    start = datetime(2026, 8, 4, 12, tzinfo=UTC)
    clock = test_journal.FakeClock(test_journal.T0)
    assert clock() == start
    clock.advance(5)
    assert clock() == start + timedelta(seconds=5)
