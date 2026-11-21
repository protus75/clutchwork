# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Repository provider routing by tier and surface
# relates: [clutch/config.py, clutch/providers.py]
# owner: engine
# verified: 530e3e82
# hash: fc0ba48e6ef23d3e1c1358634a68605af597d5ffd9cf86f960b0aa7145bb6b39
from pathlib import Path

import pytest

from clutch.config import load_config
from clutch.providers import resolve


@pytest.mark.parametrize(
    ("tier", "surface", "provider", "model"),
    [
        ("low", "requisition_review", "claude", "claude-sonnet-5-5"),
        ("medium", "requisition_review", "claude", "claude-sonnet-5-5"),
        ("high", "requisition_review", "claude", "claude-opus-5-5"),
        ("max", "requisition_review", "claude", "claude-opus-5-5"),
        ("low", "review", "claude", "claude-opus-5-5"),
        ("medium", "review", "claude", "claude-opus-5-5"),
        ("high", "review", "claude", "claude-opus-5-5"),
        ("max", "review", "claude", "claude-opus-5-5"),
        ("low", "implement", "codex", "gpt-6-luna"),
        ("medium", "implement", "codex", "gpt-6.1-terra"),
        ("high", "implement", "codex", "gpt-6.1-sol"),
        ("max", "implement", "codex", "gpt-6-astra"),
    ],
)
def test_repository_routes(tier, surface, provider, model):
    root = Path(__file__).resolve().parents[2]
    served = resolve(load_config(root / "config.yaml", cwd=root), tier, surface)
    assert (served.provider.name, served.model) == (provider, model)
