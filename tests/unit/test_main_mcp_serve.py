# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test that the `clutch mcp serve` verb starts the stdio MCP server before loading config, passes --config and cwd through, and exits 0 on KeyboardInterrupt.
# relates: [clutch/__main__.py, clutch/mcp.py]
# owner: engine
# verified: d3def5f4
# hash: f4604cc3e1894fa7e694cbc0ec0dc3f8b0289cce0ec168ad8d76d6056b8abc86
from pathlib import Path

from clutch import __main__ as entry
from clutch import mcp


def test_serve_before_config(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(mcp, "serve_stdio", lambda **kw: calls.append(kw))
    monkeypatch.setattr(entry, "load_config", lambda *a, **k: (_ for _ in ()).throw(AssertionError("loaded config")))
    assert entry._parser().parse_args(["mcp", "serve"]).mcp_verb == "serve"
    cfg = tmp_path / "other.yaml"
    assert entry.main(["--config", str(cfg), "mcp", "serve"], cwd=tmp_path, env={}) == 0
    assert calls[0]["config_path"] == cfg and calls[0]["default_cwd"] == tmp_path
    monkeypatch.setattr(mcp, "serve_stdio", lambda **kw: (_ for _ in ()).throw(KeyboardInterrupt()))
    assert entry.main(["mcp", "serve"], cwd=tmp_path, env={}) == 0
