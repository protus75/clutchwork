# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for duplicate-heading selector suffixing in index extract/build, FTS query and neighbors, and context suggest filtering of suffixed headings
# relates: [clutch/context.py, clutch/index.py]
# owner: engine
# verified: 0a7791a2
# hash: 7d0a3191b0f266d4c44762df169af61f14626b132e6a5c129fb1d1ed4021418d
import hashlib
from pathlib import Path
from types import SimpleNamespace as NS

import duckdb
import pytest

from clutch import context, index
from tests.git_fake import GitFake

DATA = b"# Top\na\n## Dup\nb\n## Dup\nc\n## Dup (2)\nd\n"


class FS:
    def read_bytes(self, path):
        return DATA

    def size(self, path):
        return 1

    def listdir(self, path):
        raise FileNotFoundError(path)


class Store:
    def call_keys(self, prefix):
        return []


class Connection:
    def __init__(self, conn):
        self.conn = conn

    def execute(self, *args):
        return self.conn.execute(*args)

    def close(self):
        pass


def test_extract_collision_and_python_compatibility():
    selectors = [row[1] for row in index._extract("doc.md", DATA)[4]]
    assert selectors == ["doc.md#Top", "doc.md#Dup", "doc.md#Dup (2)", "doc.md#Dup (2) (2)"]
    assert [row[1] for row in index._extract("a.py", b"def name(): pass\nclass C:\n def method(self): pass\n")[4]] == ["a.py::name", "a.py::C", "a.py::C.method"]


@pytest.mark.asyncio
async def test_refresh_and_fts():
    conn = duckdb.connect(":memory:")
    conn.execute("LOAD fts")
    conn.execute("CREATE TABLE files (path VARCHAR, kind VARCHAR, purpose VARCHAR, relates VARCHAR, owner VARCHAR, hash VARCHAR, size BIGINT)")
    conn.execute("CREATE TABLE chunks (path VARCHAR, selector VARCHAR, text VARCHAR, tokens BIGINT)")
    conn.execute("INSERT INTO files VALUES ('doc.md', '', '', '[]', '', ?, ?)", [hashlib.sha256(DATA).hexdigest(), len(DATA)])
    conn.execute("INSERT INTO chunks VALUES ('doc.md', 'doc.md#Dup', 'Dup alpha', 2), ('doc.md', 'doc.md#Dup', 'Dup beta', 2)")
    config = NS(state_dir=Path("/state"), index=NS(embed=None))
    creator = index.default_creator

    # Load is already done; avoid installation and keep all database access in memory.
    class Creator:
        def load(self, conn, kind):
            return []

        def create(self, conn, kind):
            return creator.create(conn, kind)

    creator_fake = Creator()

    def connect(*args, **kwargs):
        return Connection(conn)

    git = GitFake(ls_files=["doc.md"])
    findings = await index.build(config, Path("/repo"), fs=FS(), git=git, exec_=None, env={}, store=Store(), creator=creator_fake, connect=connect)
    assert findings == []
    assert [row[0] for row in conn.execute("SELECT selector FROM chunks ORDER BY selector").fetchall()] == ["doc.md#Dup", "doc.md#Dup (2)", "doc.md#Dup (2) (2)", "doc.md#Top"]
    result = await index.query(config, Path("/repo"), "Dup", fs=FS(), exec_=None, env={}, creator=creator_fake, connect=connect)
    assert result.outcome == "found"
    result = await index.neighbors(config, Path("/repo"), "Dup", fs=FS(), exec_=None, env={}, creator=creator_fake, connect=connect)
    assert (result.outcome, result.mode) == ("no_match", "fulltext")
    conn.close()


def test_suggest_filters_only_suffixed_headings_with_base():
    conn = duckdb.connect(":memory:")
    conn.execute("CREATE TABLE files (path VARCHAR)")
    conn.execute("CREATE TABLE chunks (path VARCHAR, selector VARCHAR, text VARCHAR)")
    conn.execute("CREATE TABLE touches (ticket VARCHAR, path VARCHAR)")
    conn.execute("INSERT INTO files VALUES ('doc.md'), ('a.py')")
    conn.executemany(
        "INSERT INTO chunks VALUES (?, ?, ?)", [("doc.md", selector, "alpha bravo") for selector in ("doc.md#Dup", "doc.md#Dup (2)", "doc.md#Solo (2)")] + [("a.py", "a.py::name", "alpha bravo")]
    )
    _, sections = context.suggest(conn, "ticket", [], [], "`alpha bravo`")
    assert sections == [("a.py::name", "matches alpha, bravo"), ("doc.md#Dup", "matches alpha, bravo"), ("doc.md#Solo (2)", "matches alpha, bravo")]
    conn.close()
