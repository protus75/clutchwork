# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that the MCP server's recent-repos list in the UI state file is kept in most-recent-first order and capped, that other state keys are preserved, that removed or invalid repos are dropped, that clients cannot overwrite the list through ui_state set, and that a missing, corrupt or unwritable state file is handled.
# relates: [clutch/mcp.py, tests/config_helpers.py]
# owner: engine
# verified: 0f36a321
# hash: dd39feed83e5fe1d96a3928b46314f3771b83a23cae654c90e41d2fc6fb859e0
import json

from clutch import mcp
from tests.config_helpers import VALID


def test_recent_repos(tmp_path):
    roots = [tmp_path / str(i) for i in range(12)]
    for root in roots:
        (root / "tickets").mkdir(parents=True)
        (root / "config.yaml").write_text(VALID)
    path = tmp_path / "state.json"
    path.write_text(json.dumps({"other": "kept", "recentRepos": [str(tmp_path / "missing"), str(tmp_path)]}))
    server = mcp.ClutchMCPServer(default_cwd=tmp_path, last_repo_path=tmp_path / "last", ui_state_path=path, env={})
    for root in roots:
        server.checkout(str(root))
    server.checkout(str(roots[3]))
    recent = json.loads(path.read_text())["recentRepos"]
    assert recent == [str(roots[3]), *[str(r) for r in reversed(roots[4:])], str(roots[2])]
    assert json.loads(path.read_text())["other"] == "kept"
    (roots[5] / "tickets").rmdir()
    result = server.call_tool("clutch_app_ui_state", mcp.UiState(action="get"))[0]
    assert str(roots[5]) not in result["recentRepos"]
    server.call_tool("clutch_app_ui_state", mcp.UiState(action="set", state={"refreshSeconds": 42, "recentRepos": []}))
    assert json.loads(path.read_text())["recentRepos"] == result["recentRepos"]
    isolated = mcp.ClutchMCPServer(default_cwd=tmp_path, last_repo_path=tmp_path / "last2", ui_state_path=tmp_path / "other.json", env={})
    assert isolated.call_tool("clutch_app_ui_state", mcp.UiState(action="get"))[0]["recentRepos"] == []
    isolated.ui_state_path.write_text("broken json")
    assert isolated.call_tool("clutch_app_ui_state", mcp.UiState(action="get"))[0]["recentRepos"] == []
    isolated.ui_state_path = tmp_path
    isolated.checkout(str(roots[0]))
    assert isolated.call_tool("clutch_app_ui_state", mcp.UiState(action="get"))[0]["recentRepos"] == []
