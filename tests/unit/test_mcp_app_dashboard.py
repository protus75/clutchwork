# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the MCP dashboard: the ui://clutch/dashboard.html resource protocol (list, read, wrong URI, missing or empty bundle) and the clutch_open_dashboard, clutch_app_snapshot and clutch_app_stats tools
# relates: [clutch/mcp.py]
# owner: clutch/mcp.py
# verified: 13fb8abf
# hash: d7050cd0fe98422e92bb23065f2290ee18ace74a576455e72e079284abbe13ee
import io
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from clutch import mcp


def test_resource_protocol(tmp_path):
    html = tmp_path / "dashboard.html"
    html.write_text("<main>dashboard</main>")
    requests = [
        {"method": "initialize"},
        {"method": "resources/list"},
        {"method": "resources/read", "params": {"uri": mcp.DASHBOARD_URI}},
        {"method": "resources/read", "params": {"uri": "ui://wrong"}},
    ]

    def run(requests):
        out = io.StringIO()
        mcp.serve_stdio(
            stdin=io.StringIO("\n".join(json.dumps({"jsonrpc": "2.0", "id": i, **r}) for i, r in enumerate(requests))),
            stdout=out,
            ui_state_path=tmp_path / "ui-state.json",
            default_cwd=tmp_path,
            ui_html_path=html,
        )
        return [json.loads(line) for line in out.getvalue().splitlines()]

    replies = run(requests)
    # Wrong: resources capability absent or supports change notifications.
    assert replies[0]["result"]["capabilities"]["resources"] == {"listChanged": False}
    # Wrong: resource advertises the wrong URI, media type, or border preference.
    assert replies[1]["result"]["resources"] == [
        {"uri": "ui://clutch/dashboard.html", "name": "ClutchWork dashboard", "mimeType": "text/html;profile=mcp-app", "_meta": {"ui": {"prefersBorder": False}}}
    ]
    # Wrong: return another file or omit the app media type.
    assert replies[2]["result"]["contents"] == [{"uri": "ui://clutch/dashboard.html", "mimeType": "text/html;profile=mcp-app", "text": "<main>dashboard</main>"}]
    # Wrong: accept an unrelated URI.
    assert replies[3]["error"]["code"] == -32602
    for content in (None, ""):
        if content is None:
            html.unlink()
        else:
            html.write_text(content)
        error = run(requests[2:3])[0]["error"]
        # Wrong: missing or empty bundle produces an internal error.
        assert error["data"]["code"] == "dashboard_unavailable" and error["code"] == -32000
        assert error["data"]["paved_road"] == "build the dashboard UI bundle before opening the dashboard (see docs/how-clutch-works.md)"


def test_dashboard_tools(tmp_path, monkeypatch):
    server = mcp.ClutchMCPServer(last_repo_path=tmp_path / "last-repo", ui_state_path=tmp_path / "ui-state.json", default_cwd=tmp_path, clock=lambda: datetime(2026, 1, 2, tzinfo=UTC))
    catalog = {t["name"]: t for t in server.dispatch("tools/list", {})["tools"]}
    # Wrong: expose app data to the model or omit host entrypoints.
    assert len(catalog) == 28
    assert catalog["clutch_open_dashboard"]["_meta"] == {
        "ui": {"resourceUri": "ui://clutch/dashboard.html", "visibility": ["model", "app"]},
        "com.google.antigravity/ui": {"entrypoints": [{"type": "aux_pane", "title": "ClutchWork"}, {"type": "global", "title": "ClutchWork"}]},
    }
    for name in ("clutch_app_snapshot", "clutch_app_stats", "clutch_app_ui_state", "clutch_app_config"):
        assert catalog[name]["_meta"] == {"ui": {"visibility": ["app"]}}

    def call(name, **args):
        return server.dispatch("tools/call", {"name": name, "arguments": args})

    empty = call("clutch_open_dashboard")
    # Wrong: global dashboard fails when there is no checkout.
    assert empty["structuredContent"] == {
        "repo": None,
        "tab": "tickets",
        "ready": False,
        "version": mcp.version("clutchwork"),
        "message": "Supply a ClutchWork checkout path to load the dashboard.",
    } and not empty.get("isError")
    assert call("clutch_open_dashboard", repo=str(tmp_path / "missing"))["structuredContent"]["code"] == "invalid_repo"
    (tmp_path / "tickets").mkdir()
    cfg = SimpleNamespace(state_dir=tmp_path, snapshot_merged_limit=17)
    checkout = SimpleNamespace(repo=tmp_path, config=cfg, fs=SimpleNamespace(read_bytes=None, size=None), journal=SimpleNamespace(read=lambda: ["history"]))
    monkeypatch.setattr(server, "checkout", lambda repo: (checkout, "context"))
    snapshot = {
        "counts": {"queued": 4},
        "engine": True,
        "runningStem": "sample",
        "blockedCount": 2,
        "boxCounts": {"pending": 3},
        "rows": ["large"],
        "box": ["large"],
        "steps": ["large"],
        "help": {"large": 1},
    }
    observe = Mock(return_value=snapshot)
    monkeypatch.setattr(mcp.observe, "snapshot", observe)
    result = call("clutch_open_dashboard")["structuredContent"]
    # Wrong: use defaults instead of snapshot values, or embed the large payload.
    assert result == {
        "repo": str(tmp_path),
        "tab": "tickets",
        "ready": True,
        "counts": {"queued": 4},
        "engine": True,
        "runningStem": "sample",
        "blockedCount": 2,
        "pendingBox": 3,
        "version": mcp.version("clutchwork"),
    }
    observe.assert_called_once_with("context", merged_limit=17)
    assert call("clutch_app_snapshot", all_merged=True)["structuredContent"] == snapshot
    observe.assert_called_with("context", merged_limit=None)
    collect = AsyncMock(return_value={"distinct": 8})
    tree = Mock(return_value=["distinct tree"])
    monkeypatch.setattr(mcp.stats, "collect_stats", collect)
    monkeypatch.setattr(mcp.stats, "stats_tree", tree)
    assert call("clutch_app_stats", window="2d", tree=True)["structuredContent"] == {"window": "2d", "tree": ["distinct tree"]}
    collect.assert_awaited_once_with(checkout, ["history"], server.clock(), "2d")
    tree.assert_called_once_with({"distinct": 8})
    assert call("clutch_app_stats", window="invalid")["structuredContent"]["code"] == "invalid_window"
