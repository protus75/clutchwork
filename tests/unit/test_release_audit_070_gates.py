"""Checks for the release's nonblocking installation probes."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the release's nonblocking install probes: `clutch mcp serve --check` dashboard validation and `clutch host antigravity --verify` plugin verification, including CLI exit codes.
# relates: [clutch/__main__.py, clutch/antigravity.py, clutch/mcp.py, clutch/runner.py, tests/fakes.py]
# owner: engine
# verified: 628fcc0e
# hash: 18d3083c7a11d504349871085d9343c61146b3c7bcc74b497aa46b06640dae5d

import json

import pytest

from clutch import __main__ as entry
from clutch import antigravity as ag
from clutch import mcp, runner
from tests.fakes import FakeFileSystem


class Server:
    def __init__(self):
        self.tools = [{"name": "clutch_open_dashboard"}]
        self.contents = [{"uri": mcp.DASHBOARD_URI, "mimeType": mcp.MCP_APP_MIME, "text": "html"}]

    def dispatch(self, method, params):
        if method == "tools/list":
            return {"tools": self.tools}
        assert params == {"uri": mcp.DASHBOARD_URI}
        return {"contents": self.contents}


def test_server_check():
    # Wrong tool, URI, MIME or empty content must not pass as a dashboard.
    server = Server()
    assert mcp.check_server(server)["contents"] == server.contents
    server.tools = [{"name": "other"}]
    with pytest.raises(runner.Refusal):
        mcp.check_server(server)
    server.tools = [{"name": "clutch_open_dashboard"}]
    for field, bad in [("uri", "other"), ("mimeType", "text/plain"), ("text", "")]:
        old = server.contents[0][field]
        server.contents[0][field] = bad
        with pytest.raises(runner.Refusal):
            mcp.check_server(server)
        server.contents[0][field] = old


def test_server_domain_error():
    class BrokenServer:
        def dispatch(self, method, params):
            raise mcp.DomainError("unavailable")

    with pytest.raises(runner.Refusal):
        mcp.check_server(BrokenServer())


def test_mcp_cli(tmp_path, monkeypatch, capsys):
    # A missing or empty bundle and an omitted tool must refuse without stdio.
    path = tmp_path / "dashboard.html"
    monkeypatch.setattr(mcp, "DEFAULT_DASHBOARD_HTML", path)
    monkeypatch.setattr(mcp, "serve_stdio", lambda **kwargs: (_ for _ in ()).throw(AssertionError("read stdin")))
    assert entry.main(["mcp", "serve", "--check"], cwd=tmp_path, env={}) == 2
    assert "dashboard_unavailable" in capsys.readouterr().err
    path.write_text("")
    assert entry.main(["mcp", "serve", "--check"], cwd=tmp_path, env={}) == 2
    path.write_text("<html>dashboard</html>")
    assert entry.main(["mcp", "serve", "--check"], cwd=tmp_path, env={}) == 0
    monkeypatch.delitem(mcp.TOOLS, "clutch_open_dashboard")
    assert entry.main(["mcp", "serve", "--check"], cwd=tmp_path, env={}) == 2


def test_plugin_verification(tmp_path):
    # Each installed file and each manifest field must affect the verdict.
    fs = FakeFileSystem()
    target = tmp_path / "plugin"
    ag.install_plugin(plugin_dir=target, fs=fs, executable="python", logo_bytes=b"logo", version_str="1")

    def check():
        return ag.verify_plugin(target, fs=fs, dir_exists=lambda p: p in fs.directories, executable_exists=lambda c: c == "python")

    assert check() == []
    for path in list(fs.files):
        original = fs.files.pop(path)
        assert check(), str(path)
        fs.files[path] = b""
        assert check(), str(path)
        fs.files[path] = original
    for field, value in [("name", "other"), ("version", ""), ("logo", "other"), ("suggestedPrompts", [])]:
        path = target / "plugin.json"
        original = fs.files[path]
        manifest = json.loads(original)
        manifest[field] = value
        fs.files[path] = json.dumps(manifest).encode()
        assert check(), field
        fs.files[path] = original
    fs.files[target / "mcp_config.json"] = b"{}"
    assert check()


def test_plugin_cli(tmp_path, monkeypatch):
    # Verification failure and incompatible workspace mode must propagate to exit 2.
    fs = FakeFileSystem()
    fs.write(ag.DEFAULT_LOGO_PATH, b"logo")
    monkeypatch.setattr(entry, "LocalFileSystem", lambda: fs)
    monkeypatch.setattr(ag.Path, "is_dir", lambda p: p in fs.directories)
    monkeypatch.setattr(ag, "_executable_exists", lambda _: True)
    args = ["host", "antigravity", "--plugin-dir", str(tmp_path / "plugin"), "--verify"]
    assert entry.main(args, cwd=tmp_path, env={}) == 0
    monkeypatch.setattr(ag, "verify_plugin", lambda *a, **kw: ["broken plugin"])
    assert entry.main(args, cwd=tmp_path, env={}) == 2
    assert entry.main(["host", "antigravity", "--workspace", "--verify"], cwd=tmp_path, env={}) == 2
