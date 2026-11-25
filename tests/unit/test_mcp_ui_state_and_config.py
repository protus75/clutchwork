# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests that the MCP server's clutch_app_ui_state tool gets and sets dashboard state, falling back to defaults when the state file is invalid or unreadable, and that its clutch_app_config tool reads and updates config.yaml but leaves the file unchanged when an update is invalid.
# relates: [clutch/mcp.py, tests/config_helpers.py]
# owner: engine
# verified: 64212fe8
# hash: 8b0b9badf281e0ed86b54dab414eef788bd02864029de3d280cb83fbb8d62ee5
import json

import yaml

from clutch import mcp
from tests.config_helpers import VALID


def test_state_and_config(tmp_path):
    path = tmp_path / "state.json"
    server = mcp.ClutchMCPServer(default_cwd=tmp_path, last_repo_path=tmp_path / "last", ui_state_path=path)

    def call(name, **args):
        return server.dispatch("tools/call", {"name": "clutch_app_" + name, "arguments": args})

    assert call("ui_state", action="get")["structuredContent"]["saved"] == []
    assert call("ui_state", action="get")["structuredContent"]["refreshSeconds"] == 15
    path.write_text("invalid")
    assert call("ui_state", action="get")["structuredContent"]["playAction"] == "drain"
    assert call("ui_state", action="get")["structuredContent"]["saved"] == []
    call("ui_state", action="set", state={"refreshSeconds": 31})
    assert json.loads(path.read_text())["refreshSeconds"] == 31
    assert call("ui_state", action="get")["structuredContent"]["refreshSeconds"] == 31
    assert "box" in call("ui_state", action="get")["structuredContent"]["saved"]
    server.ui_state_path = tmp_path
    assert call("ui_state", action="get")["structuredContent"]["refreshSeconds"] == 15
    assert not call("ui_state", action="set", state={"playAction": "serve"}).get("isError")
    (tmp_path / "tickets").mkdir()
    config = tmp_path / "config.yaml"
    config.write_text(VALID)
    assert call("config", action="get")["structuredContent"]["scheduler"]["parallel"]["max_runs"] == 2
    result = call("config", action="set", updates={"scheduler": {"parallel": {"max_runs": 3}}})
    assert result["structuredContent"]["scheduler"]["parallel"]["max_runs"] == 3
    written = yaml.safe_load(config.read_text())
    original = yaml.safe_load(VALID)
    assert {k: v for k, v in written.items() if k != "scheduler"} == {k: v for k, v in original.items() if k != "scheduler"}  # Reject dropping unrelated config.
    assert {k: v for k, v in written.get("scheduler", {}).items() if k != "parallel"} == original.get("scheduler", {})
    before = config.read_text()
    for updates in (
        {"scheduler": {"parallel": {"max_runs": 0}}},
        {"retro": {"unknown": True}},
        {"retro": {"enabled": True, "merges": {"enabled": False}, "settled": {"enabled": False}, "spikes": {"enabled": False}}},
    ):
        assert call("config", action="set", updates=updates)["isError"]
        assert config.read_text() == before
