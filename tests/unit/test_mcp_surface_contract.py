# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the MCP server's surface: tool visibility, the host prompt, stdio pings while a wait is running, triage and retro calls that only submit work and fail when the lock is held, and doctor acceptance of both plugin config forms.
# relates: [clutch/antigravity.py, clutch/lockfile.py, clutch/mcp.py, clutch/runner.py, tests/fakes.py]
# owner: engine
# verified: 7926699a
# hash: 723d1f1102e09b6873c722f1816fc87ad50c364ab195c6c5560f316303e323bd
import io
import json
import queue
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import antigravity, mcp, runner
from clutch.lockfile import LockHeld
from tests.fakes import FakeFileSystem
from tests.git_fake import GitFake


def test_visibility_and_host(monkeypatch, tmp_path):
    server = mcp.ClutchMCPServer(default_cwd=tmp_path)
    tools = {t["name"]: t for t in server.dispatch("tools/list", {})["tools"]}
    for name, spec in mcp.TOOLS.items():
        expected = ["app"] if name.startswith("clutch_app_") else ["model"] if name == "clutch_wait_event" else ["model", "app"]
        assert tools[name]["_meta"]["ui"]["visibility"] == expected == list(spec.visibility)
    assert tools["clutch_open_dashboard"]["_meta"]["ui"]["resourceUri"] == mcp.DASHBOARD_URI
    assert len(tools["clutch_open_dashboard"]["_meta"]["com.google.antigravity/ui"]["entrypoints"]) == 2
    host = server.dispatch("prompts/list", {})["prompts"][-1]
    assert host == {"name": "host", "description": mcp.HOST_PROMPT_DESCRIPTION, "arguments": [{"name": "repo", "required": False}, {"name": "name", "required": False}]}
    monkeypatch.setattr(server, "checkout", lambda repo: ("checkout", "ctx"))
    calls = []
    monkeypatch.setattr(server, "prompt", lambda *a, **kw: (calls.append((a, kw)) or "host text", None))
    assert server.dispatch("prompts/get", {"name": "host", "arguments": {"name": "chosen"}})["messages"][0]["content"]["text"] == "host text"
    assert calls == [(("checkout", "ctx", "host", []), {"name": "chosen"})]
    for args in ({"extra": "x"}, {"name": 7}):
        with pytest.raises(mcp.InvalidParams):
            server.dispatch("prompts/get", {"name": "host", "arguments": args})


def test_stdio_wait_does_not_block_ping(monkeypatch, tmp_path):
    entered, release = threading.Event(), threading.Event()
    lines, replies = queue.Queue(), queue.Queue()

    class Input:
        def __iter__(self):
            while (line := lines.get()) is not None:
                yield line

    class Output:
        def write(self, text):
            replies.put(json.loads(text))

        def flush(self):
            pass

    checkout = SimpleNamespace(config=SimpleNamespace(state_dir=tmp_path), fs=SimpleNamespace(read_bytes=None, size=None))
    monkeypatch.setattr(mcp.ClutchMCPServer, "checkout", lambda self, repo: (checkout, None))

    def wait(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return "cursor", ["event"], False

    monkeypatch.setattr(mcp.events, "wait_once", wait)
    thread = threading.Thread(target=mcp.serve_stdio, kwargs={"stdin": Input(), "stdout": Output(), "default_cwd": tmp_path})
    thread.start()
    try:
        lines.put(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "clutch_wait_event"}}))
        assert entered.wait(5)
        lines.put(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"}))
        assert replies.get(timeout=5) == {"jsonrpc": "2.0", "id": 2, "result": {}}
        lines.put(json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "clutch_app_config", "arguments": {"action": "set", "updates": 7}}}))
        assert replies.get(timeout=5)["result"]["structuredContent"]["code"] == "invalid_config"
        release.set()
        assert replies.get(timeout=5)["result"]["structuredContent"]["events"] == ["event"]
    finally:
        release.set()
        lines.put(None)
        thread.join(5)
    assert not thread.is_alive()


@pytest.mark.parametrize("tool,verb", [("clutch_box_triage", "triage"), ("clutch_engine_retro", "retro")])
@pytest.mark.parametrize("holder", ["serve", "drain", "release", None])
def test_submit_only(monkeypatch, tmp_path, tool, verb, holder):
    @asynccontextmanager
    async def lock(*args, **kwargs):
        if holder:
            raise LockHeld(Path("lock"), {"verb": holder})
        yield

    async def submit(checkout, exc, verb, **kwargs):
        runner._require_engine(exc)
        return SimpleNamespace(request_id="request-42")

    checkout = SimpleNamespace(config=SimpleNamespace(state_dir=tmp_path), fs=SimpleNamespace(read_bytes=None, size=None), repo=tmp_path, git=GitFake(describe="instance"), clock=lambda: None)
    server = mcp.ClutchMCPServer(default_cwd=tmp_path)
    monkeypatch.setattr(server, "checkout", lambda repo: (checkout, None))
    monkeypatch.setattr(runner, "_locked", lock)
    target = AsyncMock(side_effect=submit)
    monkeypatch.setattr(runner, "submit_engine", target)
    result = server.dispatch("tools/call", {"name": tool, "arguments": {"ids": ["box-a"]} if verb == "triage" else {}})
    if holder in ("serve", "drain"):
        assert result["structuredContent"] == {"submitted": True, "request_id": "request-42"}
        assert target.await_args.args[2] == verb
        assert target.await_args.kwargs == ({"ids": ["box-a"]} if verb == "triage" else {})
    else:
        assert result["isError"] and result["structuredContent"]["code"] == ("lock_held" if holder else "engine_not_running")


def test_doctor_accepts_both_configs(tmp_path):
    fs = FakeFileSystem()
    plugin = tmp_path / "plugin"
    ag = antigravity
    ag.install_plugin(plugin_dir=plugin, fs=fs, executable="/python", logo_bytes=b"logo", version_str="1")

    def check():
        return ag.doctor_finding(plugin, fs=fs, dir_exists=lambda _: True, executable_exists=lambda _: True)

    assert check() is None
    fs.write(plugin / "mcp_config.json", ag.portable_bundle_files(version_str="1", logo_bytes=b"logo")["mcp_config.json"])
    assert check() is None
    assert ag.doctor_finding(plugin, fs=fs, dir_exists=lambda _: True, executable_exists=lambda _: False)
    fs.write(plugin / "mcp_config.json", json.dumps({"mcpServers": {"clutchwork": {"command": "uvx", "args": ["wrong"]}}}).encode())
    assert check()
