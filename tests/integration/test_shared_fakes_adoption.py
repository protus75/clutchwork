from datetime import UTC, datetime, timedelta
from pathlib import Path

from tests import fakes
from tests.integration import test_cli, test_drain, test_driver, test_effects, test_merge, test_stages, test_tickets


def test_shared_class_identities():
    assert test_drain.Clock is fakes.FakeClock
    assert test_cli.Clock is fakes.FakeClock
    assert test_tickets.Clock is fakes.FakeClock
    assert test_driver.FakeClock is fakes.FakeClock
    assert test_effects.FakeExec is fakes.FakeExec


def test_merge_uses_imported_config():
    assert test_merge.CONFIG is test_stages.CONFIG
    source = Path(test_merge.__file__).read_text()
    assert "test_stages.py" not in source
    assert "split('CONFIG" not in source


def test_drain_clock_default_and_advance():
    clock = test_drain.Clock()
    assert clock() == datetime(2026, 1, 1, tzinfo=UTC)
    clock.advance(37)
    assert clock() == datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=37)
