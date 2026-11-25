# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for index.query covering ranking, metadata parsing, box/ticket exclusion, limits, embedding fallback, input validation, and closed refusal outcomes using fake DuckDB connections.
# relates: [clutch/index.py]
# owner: clutch/index.py
# verified: 8b0df903
# hash: c344d08b94fec4eb8d3736912363d461fb9b513ac1c4b96baac28d945c2a507d
import asyncio
from pathlib import Path
from types import SimpleNamespace as NS

import duckdb
import pytest

from clutch import index


class FS:
    def __init__(self, error=None):
        self.error = error

    def size(self, path):
        if self.error:
            raise self.error
        return 1


class Conn:
    def __init__(self, rows=(), *, fts=True, embeddings=True, error=None):
        self.rows, self.fts, self.embeddings, self.error = rows, fts, embeddings, error
        self.sql = ""
        self.closed = False

    def execute(self, sql, params=None):
        self.sql = sql
        if self.error:
            raise self.error
        return self

    def fetchone(self):
        if "schemata" in self.sql:
            return (self.fts,)
        if "information_schema.tables" in self.sql:
            return (self.embeddings,)
        return ("FLOAT[2]",)

    def fetchall(self):
        assert "NOT c.path LIKE 'box:%'" in self.sql and "NOT c.path LIKE 'tickets/%'" in self.sql
        return [row for row in self.rows if not row[0].startswith(("box:", "tickets/"))]

    def close(self):
        self.closed = True


class Creator:
    def __init__(self, failures=None):
        self.failures = failures or {}

    def load(self, conn, kind):
        return self.failures.get(kind, [])


def run(conn=None, text="topic", limit=10, embed=None, fs=None, creator=None, connect=None):
    conn = conn or Conn()
    config = NS(state_dir=Path("/state"), index=NS(embed=embed))

    def open_db(path, *, read_only):
        assert path == "/state/index.duckdb" and read_only
        return conn

    return asyncio.run(index.query(config, Path("/repo"), text, fs=fs or FS(), exec_=None, env={}, creator=creator or Creator(), limit=limit, connect=connect or open_db))


def test_rank_metadata_exclusions_and_limit():
    rows = [
        ("z.py", "code", "z.py::z", "Z", '["a", "b"]', "team", 2.0),
        ("a.py", "guide", "a.py::a", "A", "invalid", "owner", 2.0),
        ("box:x", "box", "box:x#summary", "x", "[]", "", 9.0),
        ("tickets/x", "ticket", "tickets/x#x", "x", "[]", "", 8.0),
        ("nan.py", "", "nan", "", "[]", "", float("nan")),
        ("null.py", "", "null", "", "[]", "", None),
    ]
    conn = Conn(rows)
    result = run(conn, limit=2)
    assert result == index.QueryResult(
        "found", "fulltext", (index.QueryHit("a.py", "guide", "a.py::a", "A", (), "owner", 2.0), index.QueryHit("z.py", "code", "z.py::z", "Z", ("a", "b"), "team", 2.0))
    )
    assert conn.closed
    assert len(run(Conn(rows), limit=1).hits) == 1


def test_embedding_and_fallback(monkeypatch):
    async def vector(*args):
        return [0.2, 0.8], None

    monkeypatch.setattr(index, "_embed_vector", vector)
    row = ("a.py", "code", "a.py::a", "purpose", "[]", "owner", 0.8)
    result = run(Conn([row]), embed=["embed"])
    assert result.mode == "embedding" and result.hits[0].score == 0.8
    fallback = run(Conn([row]), embed=["embed"], creator=Creator({"vss": ["unavailable"]}))
    assert fallback.mode == "fulltext" and fallback.findings == ("embed_failed: unavailable",)
    assert run(Conn(embeddings=False), embed=["embed"]).findings == ("embed_failed: embeddings table missing",)


@pytest.mark.parametrize("text,limit", [(" ", 10), ("x" * 8001, 10), (None, 10), ("x", 0), ("x", 51), ("x", True)])
def test_invalid(text, limit):
    assert run(text=text, limit=limit).outcome == "invalid_input"


def test_closed_outcomes():
    assert run().outcome == "no_match"
    assert run(fs=FS(FileNotFoundError())).outcome == "no_index"
    assert run(fs=FS(OSError("disk"))).outcome == "index_unreadable"
    assert run(Conn(error=duckdb.Error("bad schema"))).outcome == "index_unreadable"
    assert run(Conn(fts=False)).outcome == "fulltext_unavailable"
    assert run(creator=Creator({"fts": ["fts unavailable"]})).findings == ("fts unavailable",)

    def bad_connect(*args, **kwargs):
        raise duckdb.Error("open")

    assert run(connect=bad_connect).outcome == "index_unreadable"
