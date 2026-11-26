# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for MCP auto project switching: the hook-repo handler records the active repo from workspace and cwd data, the server resolves the live default repo from client roots, the remembered path, or cwd, and the Antigravity plugin installs and verifies the hooks.json config.
# relates: [clutch/__main__.py, clutch/antigravity.py, clutch/mcp.py, tests/fakes.py]
# owner: engine
# verified: c07897c9
# hash: cb93b9c3b649bbc287c944a63ff484244ac5eefb71ddf59c95cbcf681e75e240
import io
import json
from pathlib import Path

from clutch import __main__ as entry
from clutch import antigravity as ag
from clutch import mcp
from tests.fakes import FakeFileSystem


def test_hook_selection_and_failures(tmp_path):
    first, second, other = (tmp_path / n for n in ("first", "second", "other"))
    for root in (first, second):
        (root / "tickets").mkdir(parents=True)
    other.mkdir()
    path = tmp_path / "remembered"
    fs = FakeFileSystem()

    def run(data):
        return mcp.record_active_repo_from_hook(io.StringIO(data), last_repo_path=path, fs=fs)

    assert run(json.dumps({"workspacePaths": [str(other), str(first), str(second)], "cwd": str(second)})) == {}
    assert fs.files[path] == f"{first.resolve()}\n".encode()
    path.write_text(str(first) + "\n")
    fs.files.clear()
    assert run(json.dumps({"workspacePaths": [str(first)]})) == {}
    assert path not in fs.files
    assert run(json.dumps({"workspacePaths": [str(other)], "cwd": str(second)})) == {}
    assert fs.files[path] == f"{second.resolve()}\n".encode()
    fs.files.clear()
    for data in ("", "{", "[]", json.dumps({"cwd": str(other)})):
        assert run(data) == {}
    assert not fs.files

    class Broken:
        def write(self, *args):
            raise OSError("denied")

    assert mcp.record_active_repo_from_hook(io.StringIO(json.dumps({"cwd": str(second)})), last_repo_path=path, fs=Broken()) == {}
    assert mcp.default_last_repo_path({"XDG_CONFIG_HOME": str(tmp_path)}) == tmp_path / "clutch/last-repo"


def test_live_repo_resolution(tmp_path):
    roots = [tmp_path / n for n in ("cwd", "one", "two", "client")]
    for root in roots:
        (root / "tickets").mkdir(parents=True)
    path = tmp_path / "last"
    server = mcp.ClutchMCPServer(default_cwd=roots[0], last_repo_path=path, env={})
    assert server.default_repo() == roots[0]
    path.write_text(str(roots[1]))
    assert server.default_repo() == roots[1]
    path.write_text(str(roots[2]))
    assert server.default_repo() == roots[2]
    server.roots = [roots[3]]
    assert server.default_repo() == roots[3]
    server.roots = []
    path.write_text(str(tmp_path / "missing"))
    assert server.default_repo() == roots[0]


def test_cli_and_hooks(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(entry.sys, "stdin", io.StringIO("{"))
    monkeypatch.setattr(entry, "load_config", lambda *a, **k: (_ for _ in ()).throw(AssertionError("config loaded")))
    assert entry.main(["mcp", "hook-repo"], cwd=tmp_path, env={}) == 0
    assert capsys.readouterr().out == "{}\n"
    fs = FakeFileSystem()
    plugin = tmp_path / "plugin"
    ag.install_plugin(plugin_dir=plugin, fs=fs, executable="/path with space/python", logo_bytes=b"logo", version_str="1")
    hooks = json.loads(fs.files[plugin / "hooks.json"])
    for event in ("SessionStart", "PreInvocation"):
        assert hooks[ag.HOOK_NAME][event] == [{"type": "command", "command": "'/path with space/python' -m clutch mcp hook-repo", "timeout": 5}]
    assert json.loads(ag.portable_bundle_files(version_str="1", logo_bytes=b"x")["hooks.json"]) == ag.portable_hooks_config()
    assert not ag.verify_plugin(plugin, fs=fs, dir_exists=lambda _: True, executable_exists=lambda _: True)
    for data in (b"", b"{", b"{}", json.dumps({ag.HOOK_NAME: {"SessionStart": [], "PreInvocation": []}}).encode()):
        fs.files[plugin / "hooks.json"] = data
        assert "hooks.json is missing or invalid" in ag.verify_plugin(plugin, fs=fs, dir_exists=lambda _: True, executable_exists=lambda _: True)
    del fs.files[plugin / "hooks.json"]
    assert "hooks.json is missing or invalid" in ag.verify_plugin(plugin, fs=fs, dir_exists=lambda _: True, executable_exists=lambda _: True)
