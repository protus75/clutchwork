# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test of the MCP stdio JSON-RPC loop: parse and invalid-request errors, initialize server info and capabilities, ping, notifications, and unknown-method and invalid-params error codes.
# relates: [clutch/mcp.py]
# owner: clutch/mcp.py
# verified: 66bcb385
# hash: 58e4888f2dcff364d0b6edb99f72eecc76092d59f7abb3238b179c9be7ca87d9
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
    assert set(replies[3]["result"]["capabilities"]) == {"tools", "prompts", "resources"}
    assert replies[4]["result"] == {}
    assert [r["error"]["code"] for r in replies[5:]] == [-32601, -32602, -32602, -32602]
