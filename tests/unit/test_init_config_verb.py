# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test init config verb
# relates: [clutch/__main__.py, clutch/config.py, clutch/providers.py, clutch/seams.py]
# owner: engine
# verified: 69d790e1
# hash: 634662c104e98209bbc24246214932034209209dc212910f6af59709db3a3b5a
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from clutch import __main__ as cli
from clutch.config import ConfigError, load_config_text
from clutch.providers import CliStatus, ModelListing, suggest_config
from clutch.seams import ExecutableNotFound


class Exec:
    def __init__(self):
        self.calls = []
        self.responses = {}

    async def run(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        key = argv[argv.index("--model") + 1] if "--model" in argv else argv[0]
        if key in self.responses:
            response = self.responses[key]
            if isinstance(response, Exception):
                raise response
            return response
        if argv[0] == "claude":
            events = [{"type": "system", "subtype": "init", "model": f"claude-{key}-5-5"}, {"type": "result", "subtype": "error_during_execution" if key == "fable" else "success", "result": "ok"}]
            return 0, "\n".join(map(json.dumps, events)), ""
        if argv[0] == "codex":
            return (
                0,
                json.dumps(
                    {
                        "models": [
                            {"slug": "gpt-6-astra", "visibility": "list", "priority": 2},
                            {"slug": "gpt-reserve", "visibility": "hide", "priority": 5},
                            {"slug": "gpt-6.1-sol", "visibility": "list", "priority": 1},
                        ]
                    }
                ),
                "",
            )
        return 0, "NAME ID SIZE MODIFIED\nqwen3-coder:30b abc 18 GB\nllama3.2:latest def 2 GB\n", ""


def status(name, where):
    return CliStatus(name, "unused", name, where, None)


def test_suggestions():
    statuses = [status("claude", "project"), status("codex", "system"), status("qwen", "absent")]
    listings = {
        "claude": ModelListing({"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}, ("fable: error_during_execution",)),
        "codex": ModelListing({"gpt-6.1-sol": "gpt-6.1-sol", "gpt-6-astra": "gpt-6-astra"}, ()),
    }
    text = suggest_config(statuses, listings)
    assert "models_by_tier: {low: claude-haiku-5-5, medium: claude-sonnet-5-5, high: claude-opus-5-5, max: OPERATOR-SETS-THIS}" in text
    assert "    # fable: error_during_execution" in text
    assert "    package: '@openai/codex'" in text
    assert "models_by_tier: {low: gpt-6.1-sol, medium: gpt-6.1-sol, high: gpt-6.1-sol, max: gpt-6.1-sol}  # served: gpt-6.1-sol gpt-6-astra" in text
    assert "est_cost_per_call_usd: 0.25" in text and "name: qwen" not in text
    assert sum(line.endswith("candidates: [{provider: claude}, {provider: codex}]}") for line in text.splitlines()) == 8
    config = load_config_text(text, path=Path("/repo/config.yaml"), cwd=Path("/repo"))
    assert len(config.routing) == 8 and config.providers[0].package == "@anthropic-ai/claude-code"
    qwen = [status("qwen", "system")]
    text = suggest_config(qwen, {"qwen": ModelListing({}, ("unavailable",))})
    assert "base_url: http://localhost:11434/v1" in text and "est_cost_per_call_usd: 0}" in text
    assert "models_by_tier: {low: OPERATOR-SETS-THIS, medium: OPERATOR-SETS-THIS, high: OPERATOR-SETS-THIS, max: OPERATOR-SETS-THIS}" in text
    assert text.count("candidates: [{provider: qwen}]") == 8
    load_config_text(text, path=Path("/repo/config.yaml"), cwd=Path("/repo"))
    text = suggest_config(qwen, {"qwen": ModelListing({"qwen3-coder:30b": "qwen3-coder:30b", "llama3.2:latest": "llama3.2:latest"}, ())})
    assert "models_by_tier: {low: qwen3-coder:30b, medium: qwen3-coder:30b, high: qwen3-coder:30b, max: qwen3-coder:30b}  # served: qwen3-coder:30b llama3.2:latest" in text
    load_config_text(text, path=Path("/repo/config.yaml"), cwd=Path("/repo"))
    text = suggest_config([status("claude", "system")], {"claude": ModelListing({}, ("fable: error_during_execution: line one\nline two",))})
    assert "    # fable: error_during_execution: line one line two" in text
    assert not any(line.startswith("line two") for line in text.splitlines())
    load_config_text(text, path=Path("/repo/config.yaml"), cwd=Path("/repo"))
    with pytest.raises(ValueError, match="no provider CLI found"):
        suggest_config([], {})


def test_verb(monkeypatch, capsys):
    exec_ = Exec()

    class VersionExec:
        async def run(self, argv, **kwargs):
            if argv[-1] == "--version":
                exec_.calls.append((argv, kwargs))
                if argv[0] == "qwen" or absent[0]:
                    raise ExecutableNotFound(argv[0])
                return 0, "1.2.3", ""
            return await exec_.run(argv, **kwargs)

    absent = [False]
    fs = Mock()
    monkeypatch.setattr(cli, "SubprocessExec", VersionExec)
    monkeypatch.setattr(cli, "LocalFileSystem", lambda: fs)
    monkeypatch.setattr(cli, "load_config", Mock(side_effect=AssertionError("config")))
    monkeypatch.setattr(cli, "Lockfile", Mock(side_effect=AssertionError("lock")))
    monkeypatch.setattr(cli, "Journal", Mock(side_effect=AssertionError("journal")))
    monkeypatch.setattr(Path, "is_file", lambda self: False)
    calls = []

    def validate(text, *, path, cwd):
        assert capsys.readouterr().out == ""
        calls.append((text, path, cwd))
        return load_config_text(text, path=path, cwd=cwd)

    monkeypatch.setattr(cli, "load_config_text", validate)

    def run(*args):
        return cli.main(["config", "init", *args], cwd=Path("/repo"), env={"PATH": "/bin"})

    assert run() == 0
    text = capsys.readouterr().out
    assert calls == [(text, Path("/repo/config.yaml"), Path("/repo"))]
    fs.publish.assert_not_called()
    assert not any(argv[0] == "pnpm" for argv, _ in exec_.calls)
    calls.clear()
    assert run("--write") == 0
    text = capsys.readouterr().out
    assert calls == [(text, Path("/repo/config.yaml"), Path("/repo"))]
    fs.publish.assert_called_once_with(Path("/repo/config.yaml"), text.encode())
    fs.publish.side_effect = FileExistsError
    assert run("--write") == 2
    assert "config.yaml already exists" in capsys.readouterr().err
    absent[0] = True
    assert run() == 2
    assert "run: clutch provider install claude|codex|qwen" in capsys.readouterr().err
    absent[0] = False
    fs.publish.reset_mock()
    monkeypatch.setattr(cli, "load_config_text", Mock(side_effect=ConfigError(Path("/repo/config.yaml"), None, "bad")))
    assert run("--write") == 2
    assert capsys.readouterr().out == ""
    fs.publish.assert_not_called()
