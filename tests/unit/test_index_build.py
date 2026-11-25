"""Index projection and incremental updates."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks the DuckDB index build: file, chunk, touch and call rows, metadata parsing, incremental updates and deletion, git and creator failures, and embeddings
# relates: [clutch/evidence/store.py, clutch/git.py, clutch/index.py, clutch/seams.py]
# owner: engine
# verified: 01d081d3
# hash: bccaae65b79299c60ffbf974a683d193bd8b83af09460869ccc02e200f2c24bc

import hashlib
from types import SimpleNamespace as NS

import duckdb
import pytest

from clutch.evidence.store import SKIP
from clutch.git import GitError
from clutch.index import build, default_creator
from clutch.seams import LocalFileSystem
from tests.git_fake import GitFake


class FS(LocalFileSystem):
    def __init__(self):
        self.reads = []
        self.removed = []

    def read_bytes(self, path):
        self.reads.append(path)
        return super().read_bytes(path)

    def remove(self, path):
        self.removed.append(path)
        super().remove(path)


class Store:
    def __init__(self):
        self.records = {"good": (NS(stem=None, surface="edit", repo=NS(tree_before="before")), NS(repo=NS(tree_after="after", changed_paths=["a.md"])))}

    def call_keys(self, prefix):
        return sorted(self.records)

    def read_record(self, key, kind):
        value = self.records[key][kind == "end"]
        if isinstance(value, Exception):
            raise value
        return value


class Creator:
    def __init__(self, failures=None):
        self.calls = []
        self.failures = failures or {}

    def load(self, conn, kind):
        self.calls.append(("load", kind))
        return self.failures.get(("load", kind), [])

    def create(self, conn, kind):
        self.calls.append(("create", kind))
        return self.failures.get(("create", kind), [])


class Exec:
    def __init__(self, replies=None):
        self.calls = []
        self.replies = list(replies or [(0, "[1,2,3]", "")])

    async def run(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        reply = self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]
        if isinstance(reply, Exception):
            raise reply
        return reply


class Connection:
    def __init__(self, path, statements):
        self.conn = duckdb.connect(path)
        self.statements = statements

    def execute(self, sql, *args):
        self.statements.append(sql + " " + str(args))
        return self.conn.execute(sql, *args)

    def close(self):
        self.conn.close()


@pytest.fixture
def rig(tmp_path):
    fs = FS()
    fs.write(tmp_path / "a.md", b"intro\n# First\nhello world\n## Next\nbye\n")
    fs.write(tmp_path / "b.py", b'"""Module purpose.\nMore."""\ndef fun():\n    return 1\nclass C:\n    def method(self):\n        return 2\n')
    fs.write(tmp_path / "tickets/x.md", b"# secret\n")
    cfg = NS(state_dir=tmp_path, index=NS(embed=None))
    git = GitFake()
    git.paths = ["a.md", "b.py", "tickets/x.md"]
    git.touches = [("one", "abc", ["a.md", "b.py"])]
    git.fail_ls = False
    git.fail_touches = False

    def ls_files(root):
        if git.fail_ls:
            raise GitError(["ls"], 1, "", "bad ls")
        return git.paths

    def ticket_touches(root):
        if git.fail_touches:
            raise GitError(["log"], 1, "", "bad log")
        return git.touches

    git._overrides.update(ls_files=ls_files, ticket_touches=ticket_touches)
    return NS(root=tmp_path, fs=fs, config=cfg, git=git, store=Store(), creator=Creator(), exec=Exec(), statements=[])


async def run(rig, connect=None):
    return await build(
        rig.config, rig.root, fs=rig.fs, git=rig.git, exec_=rig.exec, env={"X": "y"}, store=rig.store, creator=rig.creator, connect=connect or (lambda path: Connection(path, rig.statements))
    )


def rows(rig, table):
    conn = duckdb.connect(str(rig.root / "index.duckdb"))
    try:
        return conn.execute(f"SELECT * FROM {table} ORDER BY 1, 2").fetchall()
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_rows_and_open(rig):
    paths = []
    assert await run(rig, lambda path: (paths.append(path), Connection(path, rig.statements))[1]) == []
    assert paths == [str(rig.root / "index.duckdb")]
    assert (rig.root / "index.duckdb").exists()
    a, b = rows(rig, "files")
    assert a == ("a.md", "", "", "[]", "", hashlib.sha256((rig.root / "a.md").read_bytes()).hexdigest(), 38)
    assert b[0:5] == ("b.py", "", "Module purpose.", "[]", "")
    assert [r[1] for r in rows(rig, "chunks")] == ["a.md#First", "a.md#Next", "b.py::C", "b.py::C.method", "b.py::fun"]
    assert rows(rig, "chunks")[0] == ("a.md", "a.md#First", "# First\nhello world\n", 4)
    with pytest.raises(duckdb.Error):
        rows(rig, "embeddings")
    assert not rig.exec.calls
    assert rows(rig, "touches") == [("one", "abc", "a.md"), ("one", "abc", "b.py")]
    assert rows(rig, "calls") == [("good", "", "edit", "before", "after", ["a.md"])]
    assert rig.creator.calls == [("load", "fts"), ("create", "fts")]
    assert not any(s.upper().startswith(("INSTALL", "LOAD", "SET HNSW", "CREATE INDEX", "PRAGMA CREATE_FTS_INDEX")) for s in rig.statements)


@pytest.mark.asyncio
async def test_markdown_fences_and_heading_hash(rig):
    rig.fs.write(rig.root / "a.md", b"# First\n```python\n# comment\n```\nkept\n# C#\nend\n")
    assert await run(rig) == []
    chunks = [r for r in rows(rig, "chunks") if r[0] == "a.md"]
    assert chunks == [
        ("a.md", "a.md#C#", "# C#\nend\n", 3),
        ("a.md", "a.md#First", "# First\n```python\n# comment\n```\nkept\n", 7),
    ]


@pytest.mark.asyncio
async def test_open_failure(rig):
    def fail(path):
        raise ValueError("broken")

    assert await run(rig, fail) == ["db_open_failed: broken"]
    assert rig.creator.calls == []
    assert not (rig.root / "index.duckdb").exists()


@pytest.mark.asyncio
async def test_metadata_and_bad_sources(rig):
    rig.fs.write(rig.root / "a.md", b"<!-- clutch:meta\nschema: clutch.meta/1.0\nkind: doc\npurpose: annotated\nrelates: [b.py]\nowner: team\nverified: x\nhash: x\n-->\n# Title\ntext\n")
    rig.fs.write(rig.root / "bad.md", b"<!-- clutch:meta\nbad\n-->\n# Heading\n")
    rig.fs.write(rig.root / "binary.md", b"\xff")
    rig.fs.write(rig.root / "syntax.py", b"def broken(:\n")
    rig.git.paths += ["bad.md", "binary.md", "syntax.py"]
    assert await run(rig) == []
    result = {r[0]: r for r in rows(rig, "files")}
    assert result["a.md"][1:5] == ("doc", "annotated", '["b.py"]', "team")
    assert result["bad.md"][1:5] == ("", "", "", "")[:2] + ("[]", "")
    assert {r[0] for r in rows(rig, "chunks")}.isdisjoint({"binary.md", "syntax.py"})
    assert {"binary.md", "syntax.py"} <= result.keys()


@pytest.mark.asyncio
async def test_incremental_and_deletion(rig):
    rig.config.index.embed = ["fake"]
    assert await run(rig) == []
    original = rows(rig, "embeddings")
    rig.statements.clear()
    rig.fs.reads.clear()
    assert await run(rig) == []
    assert sorted(p.name for p in rig.fs.reads) == ["a.md", "b.py"]
    assert not any(
        s.upper().startswith(
            (
                "INSERT INTO FILES",
                "INSERT INTO CHUNKS",
                "INSERT INTO EMBEDDINGS",
                "UPDATE FILES",
                "UPDATE CHUNKS",
                "UPDATE EMBEDDINGS",
                "DELETE FROM FILES",
                "DELETE FROM CHUNKS",
                "DELETE FROM EMBEDDINGS",
            )
        )
        for s in rig.statements
    )
    assert len(rows(rig, "touches")) == 2 and len(rows(rig, "calls")) == 1
    rig.fs.write(rig.root / "a.md", b"# Changed\nnew\n")
    assert await run(rig) == []
    assert [r for r in rows(rig, "embeddings") if r[0] == "b.py"] == [r for r in original if r[0] == "b.py"]
    rig.git.paths.remove("b.py")
    assert await run(rig) == []
    assert [r[0] for r in rows(rig, "files")] == ["a.md"]
    assert [r[1] for r in rows(rig, "chunks")] == ["a.md#Changed"]
    assert [r[1] for r in rows(rig, "embeddings")] == ["a.md#Changed"]
    assert len(original) == 5


@pytest.mark.asyncio
async def test_git_failures_and_calls(rig):
    assert await run(rig) == []
    old_files, old_chunks, old_touches = (rows(rig, t) for t in ("files", "chunks", "touches"))
    rig.git.fail_ls = True
    rig.git.touches = [("two", "def", ["new"])]
    rig.store.records.update(
        {
            "bad": (ValueError("broken"), None),
            "skip": (SKIP, None),
            "skip_end": (NS(stem="x", surface="s", repo=None), SKIP),
            "start": (NS(stem="x", surface="s", repo=None), FileNotFoundError()),
            "null": (NS(stem="x", surface="s", repo=None), NS(repo=None)),
        }
    )
    findings = await run(rig)
    assert len(findings) == 2 and findings[0].startswith("git_failed:") and findings[1] == "call_unreadable: bad"
    assert rows(rig, "files") == old_files and rows(rig, "chunks") == old_chunks
    assert ("two", "def", "new") in rows(rig, "touches")
    assert ("null", "x", "s", "", "", []) in rows(rig, "calls")
    rig.git.fail_ls = False
    rig.git.fail_touches = True
    rig.store.records.pop("bad")
    rig.fs.write(rig.root / "a.md", b"# Updated\n")
    findings = await run(rig)
    assert len(findings) == 1 and findings[0].startswith("git_failed:")
    assert rows(rig, "touches") == old_touches + [("two", "def", "new")]
    assert "a.md#Updated" in [r[1] for r in rows(rig, "chunks")]


@pytest.mark.asyncio
async def test_creator_failures(rig):
    rig.config.index.embed = ["fake"]
    rig.creator = Creator({("load", "vss"): ["vss unavailable"], ("create", "fts"): ["create failed"]})
    assert await run(rig) == ["vss unavailable", "create failed"]
    assert not rig.exec.calls
    assert not any("embeddings" in s.lower() for s in rig.statements)
    assert rig.creator.calls == [("load", "vss"), ("load", "fts"), ("create", "fts")]
    rig.creator = Creator({("load", "vss"): ["v"], ("load", "fts"): ["f"]})
    assert await run(rig) == ["v", "f"]
    assert rig.creator.calls == [("load", "vss"), ("load", "fts")]


def test_default_creator():
    class Recorder:
        def __init__(self, fail=False):
            self.calls = []
            self.fail = fail

        def execute(self, sql):
            self.calls.append(sql)
            if self.fail:
                raise duckdb.Error("offline")

    for kind in ("vss", "fts"):
        conn = Recorder()
        assert default_creator.load(conn, kind) == []
        assert conn.calls == [f"LOAD {kind}"]
        conn.calls.clear()
        assert default_creator.create(conn, kind) == []
        assert (conn.calls[0].startswith("SET hnsw") and "USING HNSW" in conn.calls[1]) if kind == "vss" else conn.calls[0].startswith("PRAGMA create_fts_index")
        assert default_creator.load(Recorder(True), kind) == [f"{kind} unavailable: offline"]
        assert default_creator.create(Recorder(True), kind) == [f"{kind} unavailable: offline"]


@pytest.mark.asyncio
async def test_failed_listing_never_reads_embeddings(rig):
    rig.config.index.embed = ["fake"]
    assert await run(rig) == []
    old = rows(rig, "embeddings")
    rig.statements.clear()
    rig.exec.calls.clear()
    rig.git.fail_ls = True
    findings = await run(rig)
    assert len(findings) == 1 and findings[0].startswith("git_failed:")
    assert not any("embeddings" in sql.lower() for sql in rig.statements)
    assert not rig.exec.calls
    assert rows(rig, "embeddings") == old


@pytest.mark.asyncio
async def test_creator_loads_before_statements_and_findings_follow_own(rig):
    class Ordered(Creator):
        def load(self, conn, kind):
            assert rig.statements == []
            return super().load(conn, kind)

    rig.config.index.embed = ["fake"]
    rig.creator = Ordered({("load", "vss"): ["unavailable"], ("create", "fts"): ["create issue"]})
    rig.store.records["broken"] = (ValueError(), None)
    assert await run(rig) == ["call_unreadable: broken", "unavailable", "create issue"]
