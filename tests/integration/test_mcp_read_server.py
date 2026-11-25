# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Integration test that the MCP server's prompt catalog matches the shipped clutch/specs/ask templates and that prompts/get renders the same text as ask.render with placeholders substituted.
# relates: [clutch/ask.py, clutch/mcp.py]
# owner: engine
# verified: d3def5f4
# hash: 6d1424114444fae805c2a39b183eb53b4571df8e9611012a3ef12502361ce996
from pathlib import Path
from types import SimpleNamespace

from clutch import ask, mcp


def test_real_prompt_catalog_and_render(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[2]
    server = mcp.ClutchMCPServer(default_cwd=tmp_path)
    names = {p["name"] for p in server.dispatch("prompts/list", {})["prompts"]}
    assert names == {p.stem for p in (root / "clutch/specs/ask").glob("*.md")}
    cfg = SimpleNamespace(state_dir=tmp_path / "state", ask_notes=None)
    checkout = SimpleNamespace(config=cfg, repo=tmp_path)
    monkeypatch.setattr(server, "checkout", lambda repo: (checkout, None))
    for kind, arguments in [("drain-loop", {}), ("author", {"stem": "example"})]:
        result = server.dispatch("prompts/get", {"name": kind, "arguments": arguments})
        text = result["messages"][0]["content"]["text"]
        assert text == ask.render(kind, arguments.get("stem", ""), cfg, tmp_path)
        assert "${state_dir}" not in text and "${stem}" not in text
