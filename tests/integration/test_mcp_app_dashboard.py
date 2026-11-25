"""Build and exercise the MCP dashboard bundle with its real resource endpoint."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Builds the single-file MCP dashboard bundle with dev.build_ui_bundle. It reads the bundle back through the ClutchMCPServer ui://clutch/dashboard.html resource, checks the MIME type, size, inlined assets and embedded lifecycle SVG, then runs the node dashboard harness against it.
# relates: [clutch/mcp.py, dev.py]
# owner: engine
# verified: 4d961688
# hash: d7b66c37ae1100821cdb86ff2c0289a6ec79563ca6585002c61793e8ad22ecf0

import json
import subprocess
from pathlib import Path

import dev
from clutch.mcp import ClutchMCPServer
from clutch.observe import STEP_KINDS

ROOT = Path(__file__).resolve().parents[2]


def test_dashboard_bundle(tmp_path):
    out = dev.build_ui_bundle(root=ROOT, out=tmp_path / "dashboard.html")
    item = ClutchMCPServer(ui_html_path=out).dispatch("resources/read", {"uri": "ui://clutch/dashboard.html"})["contents"][0]
    html = item["text"]
    assert item["mimeType"] == "text/html;profile=mcp-app"
    assert 0 < len(html.encode()) < 10 * 1024 * 1024
    assert "<script src=" not in html and '<link rel="stylesheet" href=' not in html
    assert (ROOT / "vscode-clutchwork/media/ticket-lifecycle.svg").read_text() in html
    subprocess.run(["node", str(ROOT / "tests/mcp_app_dashboard.js"), str(out), json.dumps(list(STEP_KINDS))], check=True, timeout=20)
