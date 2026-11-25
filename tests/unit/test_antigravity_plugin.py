"""Antigravity installation, command dispatch, and drift checks."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the Antigravity plugin and workspace skill install, default paths, doctor drift findings, and the `clutch host antigravity` CLI dispatch.
# relates: [clutch/__main__.py, clutch/antigravity.py, clutch/doctor.py, tests/fakes.py]
# owner: engine
# verified: 5e56ddef
# hash: 6606b1eeb47683da725289d69abe0bc55c038f75bac9ddff49a04e02c0ab6fa2

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import yaml

from clutch import __main__ as entry
from clutch import antigravity as ag
from clutch import doctor
from tests.fakes import FakeClock, FakeExec, FakeFileSystem


def test_bundle_and_skills(tmp_path):
    fs = FakeFileSystem()
    target = tmp_path / "plugin"
    paths = ag.install_plugin(plugin_dir=target, fs=fs, executable="/venv/python", logo_bytes=b"logo", version_str="1.2")
    assert paths == sorted(fs.files)
    manifest = json.loads(fs.files[target / "plugin.json"])
    assert manifest == {
        "name": "clutchwork",
        "displayName": "ClutchWork",
        "description": "Supervise ClutchWork tickets and engines.",
        "version": "1.2",
        "author": "ClutchWork",
        "homepage": "https://github.com/protus75/clutchwork",
        "repository": "https://github.com/protus75/clutchwork",
        "logo": "assets/logo.png",
        "suggestedPrompts": ["Open the ClutchWork dashboard", "Supervise the Clutch queue (drain-loop)", "Run docs/roadmap.md unattended with serve"],
    }
    assert json.loads(fs.files[target / "mcp_config.json"]) == {"mcpServers": {"clutchwork": {"command": "/venv/python", "args": ["-m", "clutch", "mcp", "serve"]}}}
    assert fs.files[target / "assets/logo.png"] == b"logo"
    assert len(paths) == 6
    for name, kind in [("clutch-drain-loop", "drain-loop"), ("clutch-plan-drain", "plan-ticket-drain"), ("clutch-plan-serve", "plan-ticket-serve")]:
        text = fs.files[target / "skills" / name / "SKILL.md"].decode()
        assert text.startswith("---\n")
        front = yaml.safe_load(text.split("---", 2)[1])
        assert front["name"] == name and front["description"]
        assert len(text.splitlines()) < 40 and "/loop" not in text
        assert f'kind: "{kind}"' in text and "clutch_prompt" in text
        assert "clutch_wait_event" in text and "clutch_open_dashboard" in text
        assert ("invoke_subagent" in text) == (name != "clutch-drain-loop")
    assert not any(p.name in {"CLAUDE.md", "AGENTS.md", "config.json"} for p in paths)
    workspace = FakeFileSystem()
    assert ag.install_workspace_skills(repo=tmp_path, fs=workspace) == sorted(tmp_path / ".agents/skills" / name / "SKILL.md" for name in ag.SKILLS)
    assert len(workspace.files) == 3


def test_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert ag.default_plugin_dir() == tmp_path / ".gemini/config/plugins/clutchwork"
    assert ag.default_plugin_dir({}) is None
    assert ag.default_plugin_dir({"HOME": "  "}) is None
    assert ag.mcp_config()["mcpServers"]["clutchwork"]["command"] == entry.sys.executable
    assert ag.plugin_manifest()["version"]


def test_doctor_finding(tmp_path, monkeypatch):
    fs = FakeFileSystem()
    plugin = tmp_path / "plugin"

    def exists(p):
        return p == plugin

    good = ag.mcp_config("/python")
    path = plugin / "mcp_config.json"
    assert ag.doctor_finding(None, fs=fs, dir_exists=exists) is None
    assert ag.doctor_finding(tmp_path, fs=fs, dir_exists=exists) is None
    assert ag.doctor_finding(plugin, fs=fs, dir_exists=exists)
    for data in [
        b"{",
        b"[]",
        b"{}",
        json.dumps({"mcpServers": {"clutchwork": {"command": 7, "args": list(ag.MCP_ARGS)}}}).encode(),
        json.dumps({"mcpServers": {"other": {}}}).encode(),
        json.dumps({"mcpServers": {"clutchwork": {"command": " ", "args": list(ag.MCP_ARGS)}}}).encode(),
        json.dumps({"mcpServers": {"clutchwork": {"command": "/python", "args": []}}}).encode(),
    ]:
        fs.write(path, data)
        assert "clutch host antigravity" in ag.doctor_finding(plugin, fs=fs, dir_exists=exists, executable_exists=lambda _: True)
    fs.write(path, json.dumps(good).encode())
    assert ag.doctor_finding(plugin, fs=fs, dir_exists=exists, executable_exists=lambda _: False)
    assert ag.doctor_finding(plugin, fs=fs, dir_exists=exists, executable_exists=lambda cmd: cmd == "/python") is None
    monkeypatch.setattr(ag.shutil, "which", lambda cmd: "/bin/tool" if cmd == "tool" else None)
    assert ag._executable_exists("tool") and not ag._executable_exists("missing")
    assert not ag._executable_exists(str(tmp_path / "missing"))
    monkeypatch.setattr(Path, "is_file", lambda _: True)
    monkeypatch.setattr(ag.os, "access", lambda *_: True)
    assert ag._executable_exists("/bin/python")


@pytest.mark.asyncio
async def test_doctor_rows(tmp_path, monkeypatch):
    monkeypatch.setattr(doctor, "load_config", lambda *a, **k: (_ for _ in ()).throw(ValueError("missing")))
    plugin = tmp_path / ".gemini/config/plugins/clutchwork"
    fs = FakeFileSystem()
    monkeypatch.setattr(ag, "LocalFileSystem", lambda: fs)
    monkeypatch.setattr(Path, "is_dir", lambda p: p in fs.directories)
    monkeypatch.setattr(ag, "_executable_exists", lambda cmd: cmd == "/python")

    async def rows(env):
        return await doctor.check(repo=tmp_path, config_path=None, env=env, exec_=FakeExec(), clock=FakeClock(), sleep=AsyncMock(), in_venv=True)

    assert not [r for r in await rows({}) if r.name == "antigravity"]
    assert not [r for r in await rows({"HOME": str(tmp_path)}) if r.name == "antigravity"]
    fs.write(plugin / "mcp_config.json", json.dumps(ag.mcp_config("/python")).encode())
    assert not [r for r in await rows({"HOME": str(tmp_path)}) if r.name == "antigravity"]
    fs.write(plugin / "mcp_config.json", b"bad")
    result = [r for r in await rows({"HOME": str(tmp_path)}) if r.name == "antigravity"]
    assert len(result) == 1 and result[0].passed and result[0].warn
    assert "WARN antigravity:" in doctor.render(result) and "clutch host antigravity" in result[0].detail


def test_cli(tmp_path, monkeypatch, capsys):
    fs = FakeFileSystem()
    monkeypatch.setattr(entry, "LocalFileSystem", lambda: fs)
    fs.write(ag.DEFAULT_LOGO_PATH, b"logo")
    assert entry.main(["host", "antigravity"], cwd=tmp_path, env={"HOME": str(tmp_path)}) == 0
    assert "customization://clutchwork" in capsys.readouterr().out
    assert tmp_path / ".gemini/config/plugins/clutchwork/plugin.json" in fs.files
    assert entry.main(["host", "antigravity", "--plugin-dir", str(tmp_path / "custom")], cwd=tmp_path, env={}) == 0
    assert tmp_path / "custom/plugin.json" in fs.files
    assert entry.main(["host", "antigravity", "--workspace"], cwd=tmp_path, env={}) == 0
    assert tmp_path / ".agents/skills/clutch-drain-loop/SKILL.md" in fs.files
    assert entry.main(["host", "antigravity", "--workspace", "--plugin-dir", "x"], cwd=tmp_path, env={}) == 2
    assert entry.main(["host", "antigravity"], cwd=tmp_path, env={}) == 2
    assert entry.main(["host", "antigravity"], cwd=tmp_path, env={"HOME": " "}) == 2
