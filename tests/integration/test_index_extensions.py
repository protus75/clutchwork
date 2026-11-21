"""Persistent extension lifecycle and index seam restrictions."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Persistent extension lifecycle and index seam restrictions
# relates: [clutch/index.py, tests/unit/test_index_build.py]
# owner: engine
# verified: 1ce1e32c
# hash: e7541a6d358faffd66bd0c615d44097369ef81cab2998b66fd68898463ca888d

import ast
from pathlib import Path

import duckdb
import pytest

from clutch.index import default_creator
from tests.unit.test_index_build import Exec, rig, rows, run


class RealCreator:
    def __init__(self):
        self.calls = []

    def load(self, conn, kind):
        self.calls.append(("load", kind))
        return default_creator.load(conn, kind)

    def create(self, conn, kind):
        self.calls.append(("create", kind))
        return default_creator.create(conn, kind)


def nearest(rig):
    conn = duckdb.connect(str(rig.root / "index.duckdb"))
    try:
        conn.execute("LOAD vss")
        return conn.execute("SELECT selector FROM embeddings ORDER BY array_distance(vec, [1,2,3]::FLOAT[3]) LIMIT 1").fetchone()
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_real_extensions_reopened(rig):
    rig.config.index.embed = ["fake"]
    rig.creator = RealCreator()
    result = await run(rig)
    if any("unavailable:" in finding for finding in result):
        pytest.skip("vss/fts extensions unavailable offline")
    assert result == [] and nearest(rig)
    rig.fs.write(rig.root / "a.md", b"# Second\nnew")
    assert await run(rig) == [] and nearest(rig)
    rig.fs.write(rig.root / "a.md", b"# Third\nnewer")
    assert await run(rig) == [] and nearest(rig)
    assert [r[1] for r in rows(rig, "embeddings") if r[0] == "a.md"] == ["a.md#Third"]
    rig.fs.write(rig.root / "a.md", b"# Fourth\nfailed")
    rig.exec = Exec([(2, "", "")])
    assert await run(rig) == ["embed_failed: a.md#Fourth: exit 2"]
    assert rig.creator.calls[-1] == ("create", "fts")
    with pytest.raises(duckdb.Error):
        rows(rig, "embeddings")


def test_index_source_uses_seams():
    source = (Path(__file__).resolve().parents[2] / "clutch/index.py").read_text()
    tree = ast.parse(source)
    assert "sqlite" not in source.lower()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all(alias.name.split(".")[0] not in {"os", "subprocess", "time", "datetime"} for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in {"os", "subprocess", "time", "datetime"}
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            assert node.value.id not in {"os", "subprocess", "time"}
            assert not (node.value.id == "datetime" and node.attr == "now")
        if isinstance(node, ast.Call):
            func = node.func
            assert not (isinstance(func, ast.Name) and func.id == "open")
            if isinstance(func, ast.Attribute):
                assert func.attr not in {"read_text", "read_bytes", "write_text", "write_bytes", "unlink"} or (isinstance(func.value, ast.Name) and func.value.id == "fs")
                assert not (isinstance(func.value, ast.Name) and func.value.id in {"os", "subprocess", "time", "duckdb"})
                assert not (isinstance(func.value, ast.Name) and func.value.id == "datetime" and func.attr == "now")
