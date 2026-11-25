# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the clutch_index_query MCP tool: its input schema and validation, read-only lock-free routing to index.query with filtered secrets, how hits are serialized, and refusal codes with their paved-road remedies.
# relates: [clutch/index.py, clutch/mcp.py]
# owner: engine
# verified: 7926699a
# hash: 3ea94d22b5a5a5b8b57871d4a73a18eda0ef4cf6a8d4aa4252e9eab120fd9fca
import fcntl
import json
from types import SimpleNamespace

import pytest

from clutch import index, mcp


def setup_server(tmp_path, monkeypatch, *, creator=None, connect=None):
    cfg = SimpleNamespace(state_dir=tmp_path, providers=[SimpleNamespace(auth="SECRET")], release=SimpleNamespace(pypi_token="TOKEN"), index=SimpleNamespace(embed=False))
    fs = SimpleNamespace(read_bytes=lambda _: b"", size=lambda _: 1)
    checkout = SimpleNamespace(config=cfg, fs=fs, repo=tmp_path, exec_=object())
    server = mcp.ClutchMCPServer(default_cwd=tmp_path, env={"SECRET": "hidden", "TOKEN": "hidden2", "KEEP": "yes"}, creator=creator, connect=connect)
    monkeypatch.setattr(server, "checkout", lambda repo: (checkout, None))
    return server, checkout


def call(server, **arguments):
    return server.dispatch("tools/call", {"name": "clutch_index_query", "arguments": arguments})


def test_schema_and_validation(tmp_path):
    server = mcp.ClutchMCPServer(default_cwd=tmp_path)
    tool = next(t for t in server.dispatch("tools/list", {})["tools"] if t["name"] == "clutch_index_query")
    schema = tool["inputSchema"]
    # Wrong: hide from models, allow extra arguments, or require optional parameters.
    assert tool["_meta"]["ui"]["visibility"] == ["model", "app"] and schema["additionalProperties"] is False
    assert schema["required"] == ["text"] and schema["properties"]["limit"]["default"] == 10
    assert schema["properties"]["repo"]["default"] is None
    for args in ({}, {"text": "query", "unknown": 1}):
        with pytest.raises(mcp.InvalidParams):
            call(server, **args)
    # Wrong: accept a path that is not a checkout.
    assert call(server, text="query", repo=str(tmp_path / "missing"))["structuredContent"]["code"] == "invalid_repo"


def test_query_routes_and_serializes_without_locks(tmp_path, monkeypatch):
    calls = []

    class Connection:
        def execute(self, sql, *args):
            if "information_schema.schemata" in sql:
                return SimpleNamespace(fetchone=lambda: (1,))
            if "match_bm25" in sql:
                return SimpleNamespace(fetchall=lambda: [("src/a.py", "code", "src/a.py#part", "purpose", '["src/b.py"]', "engine", 0.75)])
            return self

        def close(self):
            calls.append("closed")

    def connect(path, *, read_only):
        calls.append((path, read_only))
        return Connection()

    creator = SimpleNamespace(load=lambda conn, kind: [])
    server, checkout = setup_server(tmp_path, monkeypatch, creator=creator, connect=connect)
    real_query = index.query
    seen = []

    async def query(*args, **kwargs):
        seen.append((args, kwargs))
        return await real_query(*args, **kwargs)

    monkeypatch.setattr(index, "query", query)
    with (tmp_path / "clutch.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = call(server, text="needle", limit=3)
    # Wrong: drop or alter hit fields, use a writer connection, or take the held lock.
    expected = {
        "outcome": "found",
        "mode": "fulltext",
        "findings": [],
        "hits": [{"path": "src/a.py", "kind": "code", "selector": "src/a.py#part", "purpose": "purpose", "relates": ["src/b.py"], "owner": "engine", "score": 0.75}],
    }
    assert not result.get("isError") and result["structuredContent"] == expected
    assert json.loads(result["content"][0]["text"]) == expected
    assert calls == [(str(tmp_path / "index.duckdb"), True), "closed"]
    args, kwargs = seen[0]
    # Wrong: pass the wrong repo, executor, creator, limit, or unfiltered provider secrets.
    assert args == (checkout.config, tmp_path, "needle")
    assert kwargs == {"fs": checkout.fs, "exec_": checkout.exec_, "env": {"KEEP": "yes"}, "creator": creator, "limit": 3, "connect": connect}

    async def no_match(*args, **kwargs):
        return index.QueryResult("no_match", "fulltext", findings=("fallback",))

    monkeypatch.setattr(index, "query", no_match)
    result = call(server, text="absent")
    # Wrong: report no matches as an error or lose the mode and findings.
    assert not result.get("isError") and result["structuredContent"] == {"outcome": "no_match", "mode": "fulltext", "hits": [], "findings": ["fallback"]}


@pytest.mark.parametrize(
    ("outcome", "road"),
    [
        ("invalid_input", "provide non-blank text and a limit from 1 to 50"),
        ("no_index", "run clutch index build"),
        ("index_unreadable", "retry after refresh or run clutch index build"),
        ("fulltext_unavailable", "run clutch index build with full-text search available"),
    ],
)
def test_refusals(tmp_path, monkeypatch, outcome, road):
    server, _ = setup_server(tmp_path, monkeypatch)

    async def query(*args, **kwargs):
        return index.QueryResult(outcome, findings=("specific failure",))

    monkeypatch.setattr(index, "query", query)
    result = call(server, text="query")
    # Wrong: return a successful response or discard the specific diagnostic and remedy.
    assert result["isError"] is True
    assert result["structuredContent"] == {"code": outcome, "message": "specific failure", "paved_road": road}


def test_invalid_input_from_index(tmp_path, monkeypatch):
    server, _ = setup_server(tmp_path, monkeypatch)
    for args in ({"text": " "}, {"text": "query", "limit": 51}):
        result = call(server, **args)
        # Wrong: treat invalid inputs as successful or replace the index diagnostic.
        assert result["isError"] and result["structuredContent"]["code"] == "invalid_input"
        assert result["structuredContent"]["message"].startswith("invalid_input:")


def test_refusal_without_findings(tmp_path, monkeypatch):
    server, _ = setup_server(tmp_path, monkeypatch)

    async def query(*args, **kwargs):
        return index.QueryResult("no_index")

    monkeypatch.setattr(index, "query", query)
    # Wrong: require a finding when the index is absent.
    assert call(server, text="query")["structuredContent"] == {"code": "no_index", "message": "no_index", "paved_road": "run clutch index build"}
