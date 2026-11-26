# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the `clutch config update` verb and the claude, codex and qwen adapter model listings it uses to report served models and stale config model names
# relates: [clutch/__main__.py, clutch/config.py, clutch/providers.py, clutch/seams.py]
# owner: clutch/__main__.py
# verified: 69d790e1
# hash: 806a0eae3922eb6615d5525a259f6c984bea26a467f25cf79fc39b2bec75282b
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from clutch import __main__ as cli
from clutch.config import Limits, ModelsByTier, Provider
from clutch.providers import CLAUDE_ALIASES, PROBE_PROMPT, ClaudeAdapter, CliAdapter, CodexAdapter, ModelListing, QwenAdapter
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


def listing(adapter, exec_):
    return asyncio.run(adapter.list_models(exec_=exec_, env={"PATH": "/bin"}, cwd=Path("/repo")))


def test_claude_listing():
    exec_ = Exec()
    result = listing(ClaudeAdapter, exec_)
    assert result.models == {f: f"claude-{f}-5-5" for f in CLAUDE_ALIASES[:3]}
    assert len(result.problems) == 1 and result.problems[0].startswith("fable: ")
    for (argv, kwargs), alias in zip(exec_.calls, CLAUDE_ALIASES, strict=True):
        assert argv == [
            "claude",
            "-p",
            PROBE_PROMPT,
            "--output-format",
            "stream-json",
            "--verbose",
            "--model",
            alias,
            "--tools",
            "Read",
            "--permission-mode",
            "dontAsk",
            "--name",
            f"Clutch Preflight {alias}",
        ]
        assert kwargs["env"]["PATH"].startswith("/repo/node_modules/.bin")
        assert kwargs["cwd"] == Path("/repo") and kwargs["timeout"] == 120
    exec_.responses["sonnet"] = (1, "", "boom\n")
    result = listing(ClaudeAdapter, exec_)
    assert "sonnet" not in result.models and "sonnet: no terminal result event (rc 1)" in result.problems
    with pytest.raises(NotImplementedError):
        listing(CliAdapter, exec_)


def test_codex_listing():
    exec_ = Exec()
    result = listing(CodexAdapter, exec_)
    assert list(result.models.items()) == [("gpt-6.1-sol", "gpt-6.1-sol"), ("gpt-6-astra", "gpt-6-astra")]
    assert not result.problems and exec_.calls[0][0] == ["codex", "debug", "models"]
    exec_.responses["codex"] = (1, "", "error: not logged in\n")
    assert "not logged in" in listing(CodexAdapter, exec_).problems[0]
    exec_.responses["codex"] = (0, "not json", "")
    assert listing(CodexAdapter, exec_).problems


def test_qwen_listing():
    exec_ = Exec()
    assert listing(QwenAdapter, exec_).models == {"qwen3-coder:30b": "qwen3-coder:30b", "llama3.2:latest": "llama3.2:latest"}
    assert exec_.calls[0][0] == ["ollama", "list"]
    exec_.responses["ollama"] = ExecutableNotFound("ollama")
    assert "host-qwen.md" in listing(QwenAdapter, exec_).problems[0]
    exec_.responses["ollama"] = (1, "", "Error: could not connect to ollama app\n")
    assert "could not connect" in listing(QwenAdapter, exec_).problems[0]


def test_verb(monkeypatch, capsys):
    def provider(name, values):
        return Provider(
            name=name, kind="cli", package="pkg", models_by_tier=ModelsByTier(**dict(zip(("low", "medium", "high", "max"), values, strict=True))), limits=Limits(concurrency=1, est_cost_per_call_usd=1)
        )

    claude = provider("claude", ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-4", "claude-opus-5-4"])
    codex = provider("codex", ["gpt-6-astra"] * 4)
    config = SimpleNamespace(
        release=SimpleNamespace(pypi_token="UV_PUBLISH_TOKEN"), providers=[claude, codex], routing=[SimpleNamespace(candidates=[SimpleNamespace(provider="claude", model="claude-opus-5-4")])]
    )
    exec_ = Exec()
    monkeypatch.setattr(cli, "load_config", lambda *a, **k: config)
    monkeypatch.setattr(cli, "Lockfile", Mock(side_effect=AssertionError("lock")))
    monkeypatch.setattr(cli, "Journal", Mock(side_effect=AssertionError("journal")))
    monkeypatch.setattr(cli, "SubprocessExec", lambda: exec_)

    def run():
        return cli.main(["config", "update"], cwd=Path("/repo"), env={"PATH": "/bin"})

    assert run() == 1
    out = capsys.readouterr().out
    for line in (
        "serves: haiku=claude-haiku-5-5 sonnet=claude-sonnet-5-5 opus=claude-opus-5-5",
        "problem: fable:",
        "models_by_tier.low: claude-haiku-5-5 current",
        "models_by_tier.high: claude-opus-5-4 -> claude-opus-5-5 (latest opus)",
        "routing[0].candidates[0].model: claude-opus-5-4 -> claude-opus-5-5 (latest opus)",
        "serves: gpt-6.1-sol gpt-6-astra",
        "models_by_tier.low: gpt-6-astra current",
    ):
        assert line in out
    claude.models_by_tier = ModelsByTier(low="claude-opus-5-5", medium="claude-opus-5-5", high="claude-opus-5-5", max="claude-opus-5-5")
    config.routing = []
    assert run() == 0
    capsys.readouterr()
    codex.models_by_tier.low = "gpt-4.1"
    codex.models_by_tier.medium = "OPERATOR-SETS-THIS"
    assert run() == 1
    out = capsys.readouterr().out
    assert "gpt-4.1 not served; pick a served name" in out
    assert "OPERATOR-SETS-THIS is the placeholder; pick a served name" in out
    config.providers = [provider("llama", ["x"] * 4)]
    assert run() == 1
    assert "llama: no shipped cli adapter; name one of antigravity, claude, codex, qwen" in capsys.readouterr().out
    config.providers = [codex]
    exec_.responses["codex"] = (1, "", "error: not logged in\n")
    assert run() == 1
    assert "serves: nothing listed\n  problem: codex debug models: error: not logged in\n  models_by_tier.low: gpt-4.1 unverified; no models listed (see problem above)" in capsys.readouterr().out
    config.providers = [claude]
    exec_.responses["haiku"] = ExecutableNotFound("claude")
    assert run() == 2
    assert "run: clutch provider install claude" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("models", "problems", "name", "expected"),
    [
        ({}, ("listing failed",), "missing", "unverified; no models listed (see problem above)"),
        ({"served": "served"}, ("listing failed",), "missing", "not served; pick a served name"),
        ({}, ("listing failed",), "OPERATOR-SETS-THIS", "is the placeholder; pick a served name"),
        ({}, (), "missing", "not served; pick a served name"),
    ],
)
def test_verb_listing_status(monkeypatch, capsys, models, problems, name, expected):
    provider = Provider(
        name="codex",
        kind="cli",
        package="pkg",
        models_by_tier=ModelsByTier(low=name, medium=name, high=name, max=name),
        limits=Limits(concurrency=1, est_cost_per_call_usd=1),
    )
    config = SimpleNamespace(release=SimpleNamespace(pypi_token="TOKEN"), providers=[provider], routing=[])

    async def list_models(**kwargs):
        return ModelListing(models=models, problems=problems)

    monkeypatch.setattr(cli, "load_config", lambda *a, **k: config)
    monkeypatch.setattr(CodexAdapter, "list_models", list_models)
    assert cli.main(["config", "update"], cwd=Path("/repo"), env={"PATH": "/bin"}) == 1
    out = capsys.readouterr().out
    for tier in ("low", "medium", "high", "max"):
        assert f"models_by_tier.{tier}: {name} {expected}" in out
    if not models and problems:
        assert "not served" not in out
