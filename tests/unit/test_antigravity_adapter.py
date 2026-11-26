# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for AntigravityAdapter: agy argv per mode, adapter registry, model listing parsing and errors, and package-less config suggestion.
# relates: [clutch/config.py, clutch/providers.py]
# owner: clutch/providers.py
# verified: 69d790e1
# hash: 506a87c0f4d1f81ef4751d800f8b87e7a7be569006916c7c4191b29db3aab8db
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from clutch import providers
from clutch.config import Limits, ModelsByTier, Provider, load_config_text
from clutch.providers import AntigravityAdapter, CliStatus, ModelListing


def provider(name="antigravity", auth=None, estimate=0.5, base_url=None):
    return Provider(
        name=name,
        kind="cli",
        package=None if name == "antigravity" else "pkg",
        auth=auth,
        base_url=base_url,
        models_by_tier=ModelsByTier(low="a", medium="b", high="c", max="d"),
        limits=Limits(concurrency=1, est_cost_per_call_usd=estimate),
    )


def adapter():
    p = provider()
    return AntigravityAdapter(p, config=SimpleNamespace(providers=[p]), exec_=Mock(), fs=Mock(), redactor=SimpleNamespace(scrub=lambda x: x), env={}, cwd=Path("/repo"), timeout=120)


def test_argv_and_registry():
    a = adapter()
    prefix = ["agy", "--output-format", "stream-json", "--input-format", "text", "--model", "model-a", "--mode"]
    assert a.argv("model-a", "low", False) == prefix + ["plan"]
    assert a.argv("model-a", "low", True) == prefix + ["auto", "--dangerously-skip-permissions"]
    assert providers.ADAPTERS["antigravity"] is AntigravityAdapter and "gemini" not in providers.ADAPTERS
    assert (a.PACKAGE, a.binary, a.AUTH_ENV, a.reports_cost) == (None, "agy", None, False)


def test_models_and_config():
    class Exec:
        response = (0, "working\rmodel-a description\nspin\rmodel-b\n", "")

        async def run(self, argv, **kwargs):
            assert argv == ["agy", "models"]
            return self.response

    e = Exec()

    def listing():
        return asyncio.run(AntigravityAdapter.list_models(exec_=e, env={}, cwd=Path("/repo")))

    assert listing().models == {"model-a": "model-a", "model-b": "model-b"}
    e.response = (1, "", "spin\rnot signed in\n")
    assert listing().problems == ("agy models: not signed in",)
    e.response = (0, "\n", "")
    assert listing().problems == ("agy models: no models listed",)
    text = providers.suggest_config([CliStatus("antigravity", None, "agy", "system", "1.0.0")], {"antigravity": ModelListing({"a": "a"}, ())})
    assert "package:" not in text
    assert load_config_text(text, path=Path("/repo/config.yaml"), cwd=Path("/repo")).providers[0].name == "antigravity"
    with pytest.raises(ValueError, match="declares no `package`"):
        provider("codex").model_copy(update={"package": None}).__class__(name="codex", kind="cli", models_by_tier=provider().models_by_tier, limits=provider().limits)
