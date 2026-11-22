# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests that the claude adapter passes a --name session label built from surface and ticket, and that codex gets none
# relates: [clutch/config.py, clutch/llm.py, clutch/providers.py, clutch/redact.py, tests/fakes.py]
# owner: clutch/providers.py
# verified: f444aaa8
# hash: 2e296cabceef05cb2784b4944c56da0bc9e1cc482b140976df8832fea5f09dea
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from clutch.config import Limits, ModelsByTier, Provider
from clutch.llm import LLMRequest
from clutch.providers import ClaudeAdapter, CodexAdapter, Parsed
from clutch.redact import Redactor
from tests.fakes import FakeFileSystem


class RecordingExec:
    def __init__(self):
        self.calls = []

    async def run(self, argv, **kwargs):
        self.calls.append(list(argv))
        return 0, "", ""


def invoke(adapter_class, surface, ticket):
    provider = Provider(
        name=adapter_class.binary, kind="cli", package="pkg", models_by_tier=ModelsByTier(low="a", medium="b", high="c", max="d"), limits=Limits(concurrency=1, est_cost_per_call_usd=1)
    )
    process = RecordingExec()
    config = SimpleNamespace(state_dir=Path("/state"), providers=[provider], release=SimpleNamespace(pypi_token="TOKEN"))
    adapter = adapter_class(provider, config=config, exec_=process, fs=FakeFileSystem(), redactor=Redactor({}), env={}, cwd=Path("/repo"), timeout=120)
    adapter.parse = Mock(return_value=Parsed("ok", None, None, 1))
    request = LLMRequest(surface=surface, rendered="prompt", tier="medium", effort="low", ticket=ticket, worktree=Path("/worktree"), budget_usd=2)
    asyncio.run(adapter.invoke(request, "model"))
    return process.calls[0]


@pytest.mark.parametrize(
    ("surface", "ticket", "expected"),
    [
        ("implement", "abc", "Clutch Implement abc"),
        ("requisition_review", "abc", "Clutch Requisition Review abc"),
        ("retro", None, "Clutch Retro"),
    ],
)
def test_claude_name(surface, ticket, expected):
    assert invoke(ClaudeAdapter, surface, ticket)[-2:] == ["--name", expected]


def test_codex_has_no_name():
    assert "--name" not in invoke(CodexAdapter, "implement", "abc")
