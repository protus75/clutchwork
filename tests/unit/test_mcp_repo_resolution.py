# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for how the MCP server resolves its repo: client roots protocol, then cwd, then saved last repo, plus checkout refusal
# relates: [clutch/mcp.py, clutch/runner.py, tests/config_helpers.py]
# owner: clutch/mcp.py
# verified: 4256d272
# hash: c195e157ec897fcd77992b1eb55474fbc836a727fde9b2fae69e85889791aa6a
import io
import json

import pytest

from clutch import mcp, runner
from tests.config_helpers import VALID


def test_roots_protocol(tmp_path, monkeypatch):
    seen = []
    original = mcp.ClutchMCPServer.dispatch

    def dispatch(server, method, params):
        if method == "ping":
            seen.append(server.roots[:])
        return original(server, method, params)

    monkeypatch.setattr(mcp.ClutchMCPServer, "dispatch", dispatch)
    root = tmp_path / "my repo"
    requests = [
        {"id": 1, "method": "initialize", "params": {"capabilities": {"roots": {}}}},
        {"method": "notifications/initialized"},
        {"id": "roots-1", "result": {"roots": [{"uri": root.as_uri()}, {"uri": "https://example.com/repo"}]}},
        {"id": 2, "method": "ping"},
        {"method": "notifications/roots/list_changed"},
    ]
    out = io.StringIO()
    mcp.serve_stdio(stdin=io.StringIO("\n".join(json.dumps({"jsonrpc": "2.0", **r}) for r in requests)), stdout=out, default_cwd=tmp_path, last_repo_path=tmp_path / "last")
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    assert [r.get("id") for r in replies] == [1, "roots-1", 2, "roots-2"]
    assert seen == [[root]]
    out = io.StringIO()
    mcp.serve_stdio(stdin=io.StringIO('{"jsonrpc":"2.0","id":1,"method":"initialize"}\n{"jsonrpc":"2.0","method":"notifications/initialized"}'), stdout=out, default_cwd=tmp_path)
    assert len(out.getvalue().splitlines()) == 1


def test_resolution_and_persistence(tmp_path):
    roots = [tmp_path / name for name in ("root", "cwd", "last")]
    for root in roots:
        (root / "tickets").mkdir(parents=True)
        (root / "config.yaml").write_text(VALID)
    path = tmp_path / "last-repo"
    server = mcp.ClutchMCPServer(default_cwd=roots[1], last_repo_path=path, env={})
    server.checkout(str(roots[2]))
    assert path.read_text() == str(roots[2])
    server.roots = [roots[0]]
    assert server.default_repo() == roots[0]
    server.roots = []
    assert server.default_repo() == roots[1]
    server.cwd = tmp_path / "missing"
    server.last_repo = None
    assert server.default_repo() == roots[2]
    path.unlink()
    server.last_repo = None
    assert server.call_tool("clutch_open_dashboard", mcp.Dashboard())[0]["ready"] is False
    with pytest.raises(runner.Refusal, match="checkout"):
        server.checkout(None)
    server.last_repo_path = tmp_path
    server.cwd = roots[1]
    assert server.checkout(None)[0].repo == roots[1]
