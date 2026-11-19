import multiprocessing
from datetime import UTC, datetime

from clutch import journal as journal_module
from clutch.journal import Journal
from clutch.journalcache import open_journal_cache
from clutch.status import last_states, reject_queue


def reader(path, start, results):
    start.wait()
    with open_journal_cache(path) as cache:
        results.put(cache.last_states())


def test_concurrent_processes(tmp_path):
    journal = Journal(tmp_path, lambda: datetime(2026, 8, 4, tzinfo=UTC))
    journal.append("state_transition", {"to": "merged"}, ticket="a")
    ctx = multiprocessing.get_context("spawn")
    start, results = ctx.Event(), ctx.Queue()
    workers = [ctx.Process(target=reader, args=(tmp_path, start, results)) for _ in range(2)]
    for worker in workers:
        worker.start()
    start.set()
    assert [results.get(timeout=30) for _ in workers] == [last_states(journal.read())] * 2
    for worker in workers:
        worker.join(30)
        assert worker.exitcode == 0


def test_journal_appends_and_roll(tmp_path, monkeypatch):
    journal = Journal(tmp_path, lambda: datetime(2026, 8, 4, tzinfo=UTC))
    journal.append("state_transition", {"to": "running"}, ticket="a")
    with open_journal_cache(tmp_path) as cache:
        assert cache.last_states() == last_states(journal.read())
    monkeypatch.setattr(journal_module, "ROLL_BYTES", 1)
    journal.append("state_transition", {"to": "rejected", "routed": "reject_queue"}, ticket="a")
    assert len(journal.segments()) == 2
    with open_journal_cache(tmp_path) as cache:
        assert cache.last_states() == last_states(journal.read())
        assert cache.reject_queue() == reject_queue(journal.read())
