# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test journal duckdb cache
# relates: [clutch/journal.py, clutch/journalcache.py, clutch/status.py]
# owner: engine
# verified: 0a308920
# hash: eee68340eda207f5b3451ce02474cfb5eaef46553ac1702748890262cac16723
import json
from pathlib import Path

import duckdb
import pytest

from clutch import journalcache
from clutch.journal import Journal, JournalCorruption
from clutch.journalcache import open_journal_cache
from clutch.status import SETTLED, last_states, reject_queue


def line(ticket, body, type="state_transition"):
    return (json.dumps(dict(v=1, type=type, ts="2026-08-04T12:00:00+00:00", ticket=ticket, key=None, body=body)) + "\n").encode()


def segment(tmp_path, name="000001-20260804.jsonl"):
    path = tmp_path / "journal" / name
    path.parent.mkdir(exist_ok=True)
    return path


def check(tmp_path):
    events = Journal(tmp_path, lambda: None).read()
    with open_journal_cache(tmp_path) as cache:
        assert cache.last_states() == last_states(events)
        assert cache.reject_queue() == reject_queue(events)
        assert cache.settled() == frozenset(s for s, st in last_states(events).items() if st in SETTLED)


def test_folds_and_order(tmp_path):
    check(tmp_path)
    segment(tmp_path).write_bytes(
        b"".join(
            [
                line("a", {"to": "running"}),
                line("a", {"to": "rejected", "routed": "reject_queue"}),
                line("a", {"signal": "reject_verdict"}, "signal"),
                line("b", {"signal": "reject_arrival"}, "signal"),
                line("b", {"to": "rejected"}),
                line("b", {"signal": "reject_arrival"}, "signal"),
                line("c", {"to": "rejected", "routed": "reject_queue"}),
                line("c", {"to": "running"}),
                line("c", {"to": "merged"}),
                line("d", {"to": "merged", "routed": "reject_queue"}),
                line("e", {"to": "rejected", "routed": "reject_queue"}),
                line("f", {"to": "rejected"}),
                line("f", {"signal": "reject_arrival"}, "signal"),
            ]
        )
    )
    segment(tmp_path, "000002-20260804.jsonl").write_bytes(line("b", {"to": "running"}) + line("b", {"to": "merged"}))
    check(tmp_path)
    with open_journal_cache(tmp_path) as cache:
        assert cache.last_states()["b"] == "merged"
        assert cache.reject_queue() == {"e": {"to": "rejected", "routed": "reject_queue"}, "f": {"to": "rejected"}}


def test_incremental_and_partial(tmp_path, monkeypatch):
    path = segment(tmp_path)
    first, second, third = line("a", {"to": "running"}), line("a", {"to": "rejected"}), line("a", {"to": "merged"})
    path.write_bytes(first)
    check(tmp_path)
    with path.open("ab") as stream:
        stream.write(second + third[:20])
    seen = []
    original = journalcache._parse_complete_lines

    def count(path, data, offset, lines):
        seen.append((data, offset))
        return original(path, data, offset, lines)

    monkeypatch.setattr(journalcache, "_parse_complete_lines", count)
    with open_journal_cache(tmp_path) as cache:
        assert cache.last_states() == {"a": "rejected"}
        assert cache._conn.execute("SELECT count(*) FROM events").fetchone()[0] == 2
        assert cache._conn.execute('SELECT "offset" FROM segments').fetchone()[0] == len(first + second)
    assert seen == [(second + third[:20], len(first))]
    with path.open("ab") as stream:
        stream.write(third[20:])
    check(tmp_path)
    with open_journal_cache(tmp_path) as cache:
        assert cache.last_states() == {"a": "merged"}


@pytest.mark.parametrize("trigger", ["deleted", "garbage", "version", "removed", "truncated", "rewritten"])
def test_rebuild(tmp_path, trigger):
    path = segment(tmp_path)
    path.write_bytes(line("a", {"to": "running"}))
    other = segment(tmp_path, "000002-20260804.jsonl")
    other.write_bytes(line("b", {"to": "rejected"}))
    check(tmp_path)
    db = tmp_path / "cache/journal.duckdb"
    if trigger == "deleted":
        db.unlink()
    elif trigger == "garbage":
        db.write_bytes(b"garbage")
    elif trigger == "version":
        with duckdb.connect(str(db)) as conn:
            conn.execute("UPDATE meta SET schema_version = 999")
    elif trigger == "removed":
        other.unlink()
    elif trigger == "truncated":
        path.write_bytes(b"")
    else:
        old = path.read_bytes()
        new = old.replace(b"running", b"merged ")
        # Equal-length replacement keeps valid JSON and changes the result.
        new = new.replace(b"merged ", b"merged_")
        assert len(new) == len(old)
        path.write_bytes(new)
    check(tmp_path)
    if trigger == "rewritten":
        with open_journal_cache(tmp_path) as cache:
            assert cache.last_states()["a"] == "merged_"


def test_corruption_rolls_back(tmp_path):
    path = segment(tmp_path)
    path.write_bytes(line("a", {"to": "running"}))
    check(tmp_path)
    with path.open("ab") as stream:
        stream.write(line("a", {"to": "merged"}) + b"bad\n")
    with pytest.raises(JournalCorruption):
        with open_journal_cache(tmp_path):
            pass
    with duckdb.connect(str(tmp_path / "cache/journal.duckdb")) as conn:
        assert conn.execute("SELECT count(*) FROM events").fetchone()[0] == 1
    path.write_bytes(line("a", {"to": "running"}) + line("a", {"to": "merged"}))
    check(tmp_path)
