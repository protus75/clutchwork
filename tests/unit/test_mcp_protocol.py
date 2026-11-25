# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test of the MCP stdio JSON-RPC loop: parse and invalid-request errors, initialize server info and capabilities, ping, notifications, and unknown-method and invalid-params error codes.
# relates: [clutch/mcp.py]
# owner: clutch/mcp.py
# verified: d3def5f4
# hash: 9b0c3b88d28709a4b05f6b1e9dd0a4a88235a2ecf8965280fe5c4f7df84ff5dd
import io
import json
from importlib.metadata import version

from clutch.mcp import serve_stdio


def test_protocol_loop(tmp_path):
    requests = [
        " ",
        "{",
        "[]",
        '{"jsonrpc":"1.0","id":1,"method":"ping"}',
        '{"jsonrpc":"2.0","method":"notifications/initialized"}',
        '{"jsonrpc":"2.0","id":2,"method":"initialize","params":{}}',
        '{"jsonrpc":"2.0","id":3,"method":"ping"}',
        '{"jsonrpc":"2.0","id":4,"method":"unknown"}',
        '{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"absent"}}',
        '{"jsonrpc":"2.0","id":6,"method":"tools/call","params":{"name":"clutch_snapshot","arguments":{"bad":1}}}',
        '{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":[]}}',
    ]
    output = io.StringIO()
    serve_stdio(stdin=io.StringIO("\n".join(requests)), stdout=output, default_cwd=tmp_path)
    replies = [json.loads(line) for line in output.getvalue().splitlines()]
    assert [r.get("error", {}).get("code") for r in replies[:3]] == [-32700, -32600, -32600]
    assert replies[3]["result"]["serverInfo"]["version"] == version("clutchwork")
    assert set(replies[3]["result"]["capabilities"]) == {"tools", "prompts"}
    assert replies[4]["result"] == {}
    assert [r["error"]["code"] for r in replies[5:]] == [-32601, -32602, -32602, -32602]
