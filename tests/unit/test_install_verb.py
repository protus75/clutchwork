# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test install verb
# relates: [clutch/__main__.py, clutch/providers.py, clutch/seams.py]
# owner: engine
# verified: 69d790e1
# hash: c96b99ce84b6b311f71ee63ad5aa3088d869884ae340201cc8d28a1dadf7db9d
import asyncio
from pathlib import Path
from unittest.mock import Mock

from clutch import __main__ as cli
from clutch.providers import CliStatus, cli_status, installed_version, tool_env
from clutch.seams import ExecutableNotFound


class Exec:
    def __init__(self):
        self.calls = []
        self.pnpm = (0, "", "")

    async def run(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if argv[0] == "pnpm":
            if self.pnpm is None:
                raise ExecutableNotFound("pnpm")
            return self.pnpm
        if argv[0] == "qwen":
            raise ExecutableNotFound("qwen")
        return 0, {"claude": "2.1.322 (Claude Code)\n", "codex": "codex-cli 0.167.1\n", "agy": "0.49.0\n"}[argv[0]], ""


def test_tool_env_and_version():
    assert tool_env({"PATH": "/bin", "X": "1"}, Path("/repo")) == {"PATH": "/repo/node_modules/.bin:/bin", "X": "1"}
    assert tool_env({}, Path("/repo"))["PATH"] == "/repo/node_modules/.bin"
    assert installed_version("codex-cli 0.167.1\n", "") == "0.167.1"
    assert installed_version("", "2.1.322 (Claude Code)") == "2.1.322"
    assert installed_version("", "") is None


def test_status(monkeypatch):
    exec_ = Exec()
    monkeypatch.setattr(Path, "is_file", lambda self: False)

    def status(name):
        return asyncio.run(cli_status(name, exec_=exec_, env={"PATH": "/bin"}, cwd=Path("/repo")))

    assert status("claude") == CliStatus("claude", "@anthropic-ai/claude-code", "claude", "system", "2.1.322")
    assert exec_.calls[0][1]["env"]["PATH"] == "/repo/node_modules/.bin:/bin"
    monkeypatch.setattr(Path, "is_file", lambda self: self == Path("/repo/node_modules/.bin/claude"))
    assert status("claude").where == "project"
    assert status("qwen") == CliStatus("qwen", "@qwen-code/qwen-code", "qwen", "absent", None)


def test_install(monkeypatch, capsys):
    exec_ = Exec()
    monkeypatch.setattr(cli, "SubprocessExec", lambda: exec_)
    for name in ("load_config", "Lockfile", "Journal"):
        monkeypatch.setattr(cli, name, Mock(side_effect=AssertionError(name)))
    monkeypatch.setattr(Path, "is_file", lambda self: False)

    def main(*args):
        return cli.main(["provider", "install", *args], cwd=Path("/repo"), env={"PATH": "/bin"})

    assert main() == 0
    assert capsys.readouterr().out.splitlines() == [
        "claude: system 2.1.322, package @anthropic-ai/claude-code",
        "codex: system 0.167.1, package @openai/codex",
        "qwen: absent, package @qwen-code/qwen-code -- run: clutch provider install qwen",
        "ollama: not installed by clutch; follow clutch/docs/host-qwen.md",
        "antigravity: system 0.49.0, installed outside pnpm",
    ]
    assert all(call[0][0] != "pnpm" for call in exec_.calls)
    exec_.calls.clear()
    assert main("codex") == 0
    assert capsys.readouterr().out == "codex: system 0.167.1, package @openai/codex\n"
    argv, kwargs = exec_.calls[0]
    assert argv == ["pnpm", "add", "-D", "--allow-build=@openai/codex", "@openai/codex@latest"]
    assert kwargs == {"cwd": Path("/repo"), "env": {"PATH": "/repo/node_modules/.bin:/bin"}, "timeout": 600.0}
    exec_.calls.clear()
    assert main("codex", "llama") == 2
    assert "antigravity, claude, codex, qwen" in capsys.readouterr().err
    assert not exec_.calls
    exec_.pnpm = None
    assert main("codex") == 2
    assert "pnpm.io/installation" in capsys.readouterr().err
    exec_.pnpm = (1, "", "ERR_PNPM_FETCH_404 not found\n")
    assert main("codex") == 2
    assert "ERR_PNPM_FETCH_404" in capsys.readouterr().err


def test_install_refuses_broken_binary(monkeypatch, capsys):
    class BrokenExec(Exec):
        async def run(self, argv, **kwargs):
            if argv == ["claude", "--version"]:
                return 1, "", "Error: claude native binary not installed.\n"
            return await super().run(argv, **kwargs)

    monkeypatch.setattr(cli, "SubprocessExec", BrokenExec)
    monkeypatch.setattr(Path, "is_file", lambda self: False)
    assert cli.main(["provider", "install", "claude"], cwd=Path("/repo"), env={"PATH": "/bin"}) == 2
    assert "claude" in capsys.readouterr().err


def test_antigravity_install_refuses(monkeypatch, capsys):
    exec_ = Exec()
    monkeypatch.setattr(cli, "SubprocessExec", lambda: exec_)
    assert cli.main(["provider", "install", "antigravity"], cwd=Path("/repo"), env={"PATH": "/bin"}) == 2
    assert "follow clutch/docs/host-antigravity.md" in capsys.readouterr().err
    assert exec_.calls == []
