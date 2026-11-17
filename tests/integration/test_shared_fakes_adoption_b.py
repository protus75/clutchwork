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
