"""Neighbor ranking, validation, fallback and read-only behavior."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify neighbor ranking and query failure behavior.
# relates: [clutch/box.py, clutch/index.py, tests/unit/test_index_build.py, tests/unit/test_index_sources.py]
# owner: engine
# verified: 8a803ea2
# hash: b50b32d88e3b8586552d6b14ed0a929d1f9adeaba76546f991f022ef1558fe6f

import json

import duckdb
import pytest

from clutch.box import Box
from clutch.index import neighbors
from tests.unit.test_index_build import Creator, Exec, rig, rows, run  # noqa: F401
from tests.unit.test_index_sources import put, record

BOX = "box-000582-ab12cd34"
DECISION = "tickets/decisions/declined-box-000002-306cb481.md"
ROADMAP = "docs/roadmap.md#row 94"


class TextExec(Exec):
    async def run(self, argv, **kwargs):
        value = kwargs["stdin_path"].read_text()
        self.calls.append((argv, kwargs, value))
        vector = [1, 0, 0] if "Duplicate" in value or value == "query" else [0.8, 0.6, 0] if "row item" in value else [0, 1, 0]
        return 0, json.dumps(vector), ""


async def query(rig, text="query", **kwargs):
    return await neighbors(rig.config, rig.root, text, fs=rig.fs, exec_=rig.exec, env={"X": "y"}, creator=rig.creator, **kwargs)


async def setup_index(rig):
    rig.config.index.embed = ["fake"]
    rig.exec = TextExec()
    put(
        rig,
        "docs/roadmap.md",
        "# Roadmap\n| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n|---|---|---|---|---|---|---|---|\n| 94 | `row` | x | feature | P1 | - | - | row item |\n",
    )
    put(rig, DECISION, record("declined-box-000002-306cb481", "Decision body"))
    box = Box(rig.config.state_dir / "box", rig.fs)
    actual, _ = box.enqueue(message_class="suggestion", origin="test", summary="Duplicate of row 94")
    assert await run(rig) == []
    conn = duckdb.connect(str(rig.root / "index.duckdb"))
    for table in ("files", "chunks", "embeddings"):
        conn.execute(f"UPDATE {table} SET path = ? WHERE path = ?", [f"box:{BOX}", f"box:{actual}"])
        if table != "files":
            conn.execute(f"UPDATE {table} SET selector = ? WHERE selector = ?", [f"box:{BOX}#summary", f"box:{actual}#summary"])
    conn.close()
    rig.exec.calls.clear()
    rig.creator.calls.clear()


@pytest.mark.asyncio
async def test_ranking_filters_ties_and_read_only(rig):
    await setup_index(rig)
    before = (rig.root / "index.duckdb").read_bytes()
    tables = {t: rows(rig, t) for t in ("files", "chunks", "embeddings", "touches", "calls")}
    statements = []

    class Connection:
        def __init__(self, path, **kwargs):
            self.conn = duckdb.connect(path, **kwargs)

        def execute(self, sql, *args):
            statements.append(sql)
            return self.conn.execute(sql, *args)

        def close(self):
            self.conn.close()

    result = await query(rig, connect=Connection)
    assert (result.outcome, result.mode, result.findings) == ("found", "embedding", ())
    assert [(h.kind, h.ref, h.selector) for h in result.hits] == [
        ("box", BOX, f"box:{BOX}#summary"),
        ("roadmap", "row 94", ROADMAP),
        ("decision", DECISION, DECISION + "#declined-box-000002-306cb481"),
    ]
    assert [h.score for h in result.hits] == pytest.approx([1, 0.8, 0])
    assert (rig.root / "index.duckdb").read_bytes() == before
    assert {t: rows(rig, t) for t in tables} == tables
    assert not any(s.upper().startswith(("INSERT", "DELETE", "CREATE", "DROP", "PRAGMA")) for s in statements)
    assert all(action != "create" for action, _ in rig.creator.calls)
    assert [h.ref for h in (await query(rig, limit=2)).hits] == [BOX, "row 94"]
    assert [h.ref for h in (await query(rig, kinds=("roadmap",))).hits] == ["row 94"]
    assert [h.ref for h in (await query(rig, kinds=("decision", "roadmap", "box"))).hits] == [BOX, "row 94", DECISION]
    assert [h.ref for h in (await query(rig, exclude=(BOX,), limit=2)).hits] == ["row 94", DECISION]
    assert (await query(rig, exclude=("unknown",))).hits == result.hits
    rig.exec = Exec([(0, "[0,0,1]", "")])
    tied = await query(rig)
    assert tied.outcome == "found" and len(tied.hits) == 3
    assert [h.score for h in tied.hits] == [0, 0, 0]
    assert [h.selector for h in tied.hits] == sorted([f"box:{BOX}#summary", ROADMAP, DECISION + "#declined-box-000002-306cb481"])
    rig.exec = Exec([(0, "[0,0,0]", "")])
    zero = await query(rig)
    assert (zero.outcome, zero.mode, zero.hits) == ("no_match", "embedding", ())
    rig.exec = Exec()
    assert (await query(rig, kinds=("box",), exclude=(BOX,))).outcome == "no_match"


@pytest.mark.asyncio
async def test_validation_and_order(rig):
    cases = [(None, {}, "text: not a string"), ("", {}, "text: blank"), ("  \n", {}, "text: blank"), ("x" * 8001, {}, "text: longer than 8000 characters")]
    cases += [("x", {"limit": x}, "limit: not an integer in 1..50") for x in (0, 51, True, 2.0, "3")]
    cases += [("x", {"kinds": x}, "kinds: not a non-empty collection of distinct members of box, roadmap, decision") for x in ("box", (), ("box", "box"), ("ticket",))]
    cases += [("x", {"exclude": x}, "exclude: not a collection of at most 50 non-empty strings") for x in ("box-1", tuple(str(i) for i in range(51)), ("",), (1,))]
    for text, kw, error in cases:
        result = await query(rig, text, connect=lambda *a, **k: pytest.fail("connected"), **kw)
        assert (result.outcome, result.mode, result.hits, result.findings) == ("invalid_input", "", (), (f"invalid_input: {error}",))
    assert not rig.exec.calls
    for kw, prefix in [({"text": "", "limit": 0}, "text"), ({"limit": 0, "kinds": ()}, "limit"), ({"kinds": (), "exclude": "x"}, "kinds")]:
        assert (await query(rig, **kw)).findings[0].startswith(f"invalid_input: {prefix}:")
    for kw in ({"text": "x" * 8000}, {"limit": 1}, {"limit": 50}):
        assert (await query(rig, **kw)).outcome == "no_index"


@pytest.mark.asyncio
async def test_missing_and_unreadable(rig):
    result = await query(rig)
    assert (result.outcome, result.mode, result.hits, result.findings) == ("no_index", "", (), ())
    assert not rig.exec.calls
    path = rig.root / "index.duckdb"
    path.write_text("invalid database")
    for connect in (lambda *a, **k: (_ for _ in ()).throw(ValueError("bad open")), duckdb.connect):
        result = await query(rig, connect=connect)
        assert result.outcome == "index_unreadable" and result.findings[0].startswith("index_unreadable: ")
    path.unlink()
    conn = duckdb.connect(str(path))
    conn.execute("CREATE TABLE files (path VARCHAR, kind VARCHAR)")
    conn.close()
    result = await query(rig)
    assert result.outcome == "index_unreadable" and result.findings[0].startswith("index_unreadable: ")


@pytest.mark.asyncio
async def test_fallbacks_and_exec_seam(rig):
    await setup_index(rig)
    for reply, reason in [((3, "", ""), "exit 3"), ((0, "oops", ""), "not json"), ((0, "[]", ""), "not a vector"), ((0, "[1,2]", ""), "length 2 != 3"), (TimeoutError(), "exec TimeoutError")]:
        rig.exec = Exec([reply])
        result = await query(rig, "  query  ")
        assert (result.outcome, result.mode, result.hits, result.findings) == ("fulltext_unavailable", "", (), (f"embed_failed: {reason}", "fts unavailable: index missing"))
        argv, call = rig.exec.calls[0]
        assert len(rig.exec.calls) == 1 and argv == ["fake"] and call["cwd"] == rig.root and call["env"] == {"X": "y"} and call["timeout"] == 60
        assert call["stdin_path"] in rig.fs.removed and not call["stdin_path"].exists()
    rig.exec = TextExec()
    await query(rig, "  query  ")
    assert len(rig.exec.calls) == 1 and rig.exec.calls[0][2] == "query"
    rig.creator = Creator({("load", "vss"): ["vss unavailable: x"]})
    result = await query(rig)
    assert (result.outcome, result.mode, result.hits, result.findings) == ("fulltext_unavailable", "", (), ("embed_failed: vss unavailable: x", "fts unavailable: index missing"))
    rig.creator = Creator({("load", "fts"): ["fts unavailable: y"]})
    rig.exec = Exec([(3, "", "")])
    result = await query(rig)
    assert (result.outcome, result.mode, result.hits, result.findings) == ("fulltext_unavailable", "", (), ("embed_failed: exit 3", "fts unavailable: y"))
    rig.creator = Creator()
    rig.config.index.embed = None
    rig.exec.calls.clear()
    result = await query(rig)
    assert (result.outcome, result.mode, result.hits, result.findings) == ("fulltext_unavailable", "", (), ("fts unavailable: index missing",))
    assert not rig.exec.calls
    rig.config.index.embed = ["fake"]
    conn = duckdb.connect(str(rig.root / "index.duckdb"))
    conn.execute("DROP TABLE embeddings")
    conn.close()
    rig.creator = Creator()
    result = await query(rig)
    assert (result.outcome, result.mode, result.hits, result.findings) == ("fulltext_unavailable", "", (), ("embed_failed: embeddings table missing", "fts unavailable: index missing"))
    rig.config.index.embed = None
    rig.exec.calls.clear()
    result = await query(rig)
    assert (result.outcome, result.mode, result.hits, result.findings) == ("fulltext_unavailable", "", (), ("fts unavailable: index missing",))
    assert not rig.exec.calls


@pytest.mark.asyncio
async def test_kind_filter_leaves_no_candidates(rig):
    box = Box(rig.config.state_dir / "box", rig.fs)
    box.enqueue(message_class="suggestion", origin="test", summary="A candidate message")
    rig.config.index.embed = ["fake"]
    assert await run(rig) == []
    result = await query(rig, kinds=("decision",))
    assert (result.outcome, result.mode, result.hits, result.findings) == ("no_match", "embedding", (), ())
