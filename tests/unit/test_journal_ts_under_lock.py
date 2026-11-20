# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test journal ts under lock
# relates: [clutch/audit.py, clutch/journal.py]
# owner: engine
# verified: 0a308920
# hash: 0595c3e0208ddfee40e32a41cd9708590dca97fd828454a5d54b90f9e5a1884e
import fcntl
import os
from datetime import UTC, datetime, timedelta

import pytest

from clutch.audit import audit_journal
from clutch.journal import Journal

NOW = datetime(2026, 8, 4, 12, tzinfo=UTC)


def test_clock_read_while_lock_held(tmp_path):
    calls = []

    def clock():
        fd = os.open(tmp_path / "journal.lock", os.O_RDWR | os.O_CREAT, 0o644)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                calls.append("refused")
            else:
                calls.append("not refused")
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
        return NOW

    Journal(tmp_path, clock).append("timer_armed", {})
    assert calls
    assert all(call == "refused" for call in calls)


def test_ts_follows_append_order_across_handles(tmp_path):
    moments = iter(NOW + timedelta(seconds=n) for n in range(4))

    def clock():
        return next(moments)

    journal = Journal(tmp_path, clock)
    other = Journal(tmp_path, clock)
    for n, handle in enumerate((journal, other, journal, other)):
        handle.append("timer_armed", {"n": n})
    timestamps = [event.ts for event in journal.read()]
    assert timestamps == sorted(timestamps)
    assert audit_journal(journal) == []


def test_invalid_event_never_reads_clock(tmp_path):
    calls = []

    def clock():
        calls.append(True)
        return NOW

    with pytest.raises(ValueError):
        Journal(tmp_path, clock).append("checkpoint", {})
    assert calls == []
