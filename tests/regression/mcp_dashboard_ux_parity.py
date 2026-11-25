# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Regression check that the dashboard's merged color is #B180D7 and the MCP server opens the dashboard on the repo resolved through the roots protocol
# relates: [clutch/mcp.py]
# owner: clutch/mcp.py
# verified: 4256d272
# hash: aede02204cce2f75ffd21212321b7f0765e5e85e9e8994dcc729ceadbcdc820c
import io
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from clutch.mcp import serve_stdio

root = Path(__file__).resolve().parents[2]
if not all(p.exists() for p in (root / "clutch/mcp.py", root / "clutch/ui/dashboard.css", root / "tickets", root / "config.yaml")):
    print("missing prerequisites", file=sys.stderr)
    print(json.dumps({"regression_result": "error"}))
    sys.exit(2)
css = (root / "clutch/ui/dashboard.css").read_text()
scratch = root / ".clutch/scratch"
scratch.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(dir=scratch) as tmp:
    requests = [
        {"id": 1, "method": "initialize", "params": {"capabilities": {"roots": {}}}},
        {"method": "notifications/initialized"},
        {"id": "roots-1", "result": {"roots": [{"uri": root.as_uri()}]}},
        {"id": 2, "method": "tools/call", "params": {"name": "clutch_open_dashboard", "arguments": {}}},
    ]
    out = io.StringIO()
    with patch("clutch.mcp.observe.snapshot", return_value={"counts": {}, "engine": False, "runningStem": None, "blockedCount": 0, "boxCounts": {"pending": 0}}):
        serve_stdio(stdin=io.StringIO("\n".join(json.dumps({"jsonrpc": "2.0", **r}) for r in requests)), stdout=out, default_cwd=tmp, env={"XDG_CONFIG_HOME": str(Path(tmp) / "xdg")})
    replies = [json.loads(line) for line in out.getvalue().splitlines()]
    result = next((r.get("result", {}).get("structuredContent", {}) for r in replies if r.get("id") == 2), {})
    passed = (
        "--vscode-clutchwork-merged: #B180D7" in css
        and "--vscode-clutchwork-merged: var(--color-text-success" not in css
        and any(r.get("method") == "roots/list" and r.get("id") == "roots-1" for r in replies)
        and not any(r.get("error", {}).get("code") == -32600 for r in replies)
        and result.get("ready") is True
        and result.get("repo") == str(root)
    )
print(json.dumps({"regression_result": "pass" if passed else "defect"}))
sys.exit(0 if passed else 1)
