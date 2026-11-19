"""Rebuildable, exclusively locked DuckDB projection of the journal."""

import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from pathlib import Path

import duckdb

from clutch.journal import Journal, _parse_complete_lines
from clutch.seams import LocalFileSystem
from clutch.status import SETTLED

SCHEMA_VERSION = 1


def _fingerprint(path, offset):
    with path.open("rb") as stream:
        first = stream.read(min(offset, 4096))
        stream.seek(max(0, offset - 4096))
        last = stream.read(min(offset, 4096))
    return hashlib.sha256(first + last).hexdigest()


def _schema(conn):
    conn.execute("CREATE TABLE meta (schema_version INTEGER)")
    conn.execute("INSERT INTO meta VALUES (?)", [SCHEMA_VERSION])
    conn.execute('CREATE TABLE segments (name VARCHAR PRIMARY KEY, "offset" BIGINT, lines BIGINT, fingerprint VARCHAR)')
    conn.execute("CREATE TABLE events (seq BIGINT, v INTEGER, type VARCHAR, ts VARCHAR, ticket VARCHAR, key VARCHAR, body VARCHAR)")


def _open(path):
    try:
        conn = duckdb.connect(str(path))
        try:
            if conn.execute("SELECT schema_version FROM meta").fetchall() != [(SCHEMA_VERSION,)]:
                raise ValueError("schema version")
            conn.execute('SELECT name, "offset", lines, fingerprint FROM segments LIMIT 0')
            conn.execute("SELECT seq, v, type, ts, ticket, key, body FROM events LIMIT 0")
            return conn
        except duckdb.Error, ValueError:
            conn.close()
    except duckdb.Error:
        pass
    path.unlink(missing_ok=True)
    conn = duckdb.connect(str(path))
    _schema(conn)
    return conn


def _load(conn, paths):
    records = {name: (offset, lines, fingerprint) for name, offset, lines, fingerprint in conn.execute("SELECT * FROM segments").fetchall()}
    names = {p.name for p in paths}
    rebuild = any(name not in names for name in records)
    for path in paths:
        if path.name in records:
            offset, _, fingerprint = records[path.name]
            if path.stat().st_size < offset or _fingerprint(path, offset) != fingerprint or (path.name != paths[-1].name and path.stat().st_size > offset):
                rebuild = True
        elif records and path.name < max(records):
            rebuild = True
    conn.execute("BEGIN TRANSACTION")
    try:
        if rebuild:
            conn.execute("DELETE FROM events")
            conn.execute("DELETE FROM segments")
            records = {}
        seq = conn.execute("SELECT coalesce(max(seq), 0) FROM events").fetchone()[0]
        for path in paths:
            offset, count, _ = records.get(path.name, (0, 0, ""))
            with path.open("rb") as stream:
                stream.seek(offset)
                data = stream.read()
            events, new_offset, count = _parse_complete_lines(path, data, offset, count)
            for event in events:
                seq += 1
                conn.execute("INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?)", [seq, event.v, event.type, event.ts, event.ticket, event.key, json.dumps(event.body)])
            conn.execute("INSERT OR REPLACE INTO segments VALUES (?, ?, ?, ?)", [path.name, new_offset, count, _fingerprint(path, new_offset)])
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


class JournalCache:
    def __init__(self, conn):
        self._conn = conn

    def last_states(self):
        rows = self._conn.execute("""
            SELECT ticket, body FROM events
            WHERE type = 'state_transition' AND ticket IS NOT NULL AND json_exists(body, '$.to')
            QUALIFY row_number() OVER (PARTITION BY ticket ORDER BY seq DESC) = 1
        """).fetchall()
        return {ticket: json.loads(body)["to"] for ticket, body in rows}

    def reject_queue(self):
        rows = self._conn.execute("""
            WITH terminals AS (
                SELECT * FROM events WHERE ticket IS NOT NULL AND type = 'state_transition'
                  AND coalesce(json_extract_string(body, '$.to'), '') != 'running'
            ), actions AS (
                SELECT e.ticket, e.seq, e.body, 'terminal' AS action FROM terminals e
                UNION ALL
                SELECT e.ticket, e.seq, t.body, json_extract_string(e.body, '$.signal') AS action
                FROM events e LEFT JOIN LATERAL (
                    SELECT body FROM terminals t WHERE t.ticket = e.ticket AND t.seq < e.seq ORDER BY seq DESC LIMIT 1
                ) t ON true
                WHERE e.type = 'signal' AND e.ticket IS NOT NULL
                  AND json_extract_string(e.body, '$.signal') IN ('reject_arrival', 'reject_verdict')
            ), latest AS (
                SELECT * FROM actions QUALIFY row_number() OVER (PARTITION BY ticket ORDER BY seq DESC) = 1
            )
            SELECT ticket, body, action FROM latest
        """).fetchall()
        result = {}
        for ticket, body, action in rows:
            if body is None:
                continue
            value = json.loads(body)
            if value.get("to") not in SETTLED and (action == "reject_arrival" or (action == "terminal" and value.get("routed") == "reject_queue")):
                result[ticket] = value
        return result

    def settled(self):
        placeholders = ", ".join("?" for _ in SETTLED)
        rows = self._conn.execute(
            f"""SELECT ticket FROM (
                SELECT ticket, body FROM events
                WHERE type = 'state_transition' AND ticket IS NOT NULL AND json_exists(body, '$.to')
                QUALIFY row_number() OVER (PARTITION BY ticket ORDER BY seq DESC) = 1
            ) WHERE json_extract_string(body, '$.to') IN ({placeholders})""",
            sorted(SETTLED),
        ).fetchall()
        return frozenset(row[0] for row in rows)


@contextmanager
def open_journal_cache(state_dir):
    directory = Path(state_dir) / "cache"
    LocalFileSystem().mkdir(directory)
    fd = os.open(directory / "journal.duckdb.lock", os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        conn = _open(directory / "journal.duckdb")
        try:
            paths = Journal(state_dir, lambda: None).segments()
            _load(conn, paths)
            yield JournalCache(conn)
        finally:
            conn.close()
    finally:
        os.close(fd)
