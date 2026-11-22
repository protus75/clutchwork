"""Pin the shared builder against the four original fixture texts."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Pins build_config output to the four original fixture config texts and checks that overrides load and amend_config keeps earlier edits.
# relates: [clutch/config.py, tests/config_fixture.py, tests/harness/shakeout/bench.py, tests/integration/test_cli.py, tests/integration/test_providers.py]
# owner: engine
# verified: 6f94fa01
# hash: d0301a8ae33532ed5769987d22b38245ce1a1b1a3a3a38d0db0586bf935e69ac

import pytest
import yaml

from clutch.config import load_config
from tests.config_fixture import amend_config, build_config
from tests.harness.shakeout.bench import _CONFIG as BENCH_CONFIG
from tests.integration.test_cli import CONFIG as CLI_CONFIG
from tests.integration.test_providers import CONFIG as PROVIDERS_CONFIG
from tests.integration.test_stages import CONFIG as STAGES_CONFIG

CLI_TEXT = """schema_version: 1
state_dir: .clutch/state
providers:
  - name: claude
    kind: cli
    package: test-cli
    models_by_tier: {low: m, medium: m, high: m, max: m}
    limits: {concurrency: 1}
routing:
  - {tier: medium, surface: implement, candidates: [{provider: claude}]}
review: {}
merge: {}
engine_plane_safety_inventory: [config.yaml]
"""

STAGES_TEXT = """schema_version: 1
state_dir: .clutch/state
providers:
  - name: fake
    kind: cli
    package: test-cli
    auth: FAKE_KEY
    models_by_tier: {low: m, medium: m, high: m, max: m}
    limits: {concurrency: 1, est_cost_per_call_usd: 0.5}
routing:
  - {tier: medium, surface: implement, candidates: [{provider: fake}]}
  - {tier: medium, surface: review, candidates: [{provider: fake}]}
review: {}
merge: {}
engine_plane_safety_inventory: [config.yaml]
"""

PROVIDERS_TEXT = """schema_version: 1
state_dir: state
providers:
  - name: claude
    kind: cli
    package: test-cli
    auth: CLAUDE_KEY
    models_by_tier: {low: c-low, medium: c-med, high: c-high, max: c-max}
    limits: {concurrency: 1}
  - name: codex
    kind: cli
    package: test-cli
    auth: CODEX_KEY
    models_by_tier: {low: x-low, medium: x-med, high: x-high, max: x-max}
    limits: {concurrency: 1, est_cost_per_call_usd: 1.5}
routing:
  - {tier: medium, surface: implement, candidates: [{provider: codex}, {provider: claude}]}
  - {tier: high, surface: implement, candidates: [{provider: claude}]}
  - {tier: medium, surface: review, candidates: [{provider: claude, model: c-max}, {provider: codex}]}
  - {tier: low, surface: review, candidates: [{provider: codex}]}
review: {}
merge: {}
engine_plane_safety_inventory: []
"""

BENCH_TEXT = """schema_version: 1
state_dir: .clutch/state
providers:
  - name: fake
    kind: cli
    package: test-cli
    models_by_tier: {low: fake, medium: fake, high: fake, max: fake}
    limits: {concurrency: 1, est_cost_per_call_usd: 0.0}
routing:
  - {tier: medium, surface: implement, candidates: [{provider: fake}]}
  - {tier: medium, surface: review, candidates: [{provider: fake}]}
review: {}
merge: {}
engine_plane_safety_inventory: [config.yaml]
"""


@pytest.mark.parametrize("actual,expected", [(CLI_CONFIG, CLI_TEXT), (STAGES_CONFIG, STAGES_TEXT), (PROVIDERS_CONFIG, PROVIDERS_TEXT), (BENCH_CONFIG, BENCH_TEXT)])
def test_original_texts(actual, expected):
    # Rendering with different indentation, ordering or flow spacing breaks string consumers.
    assert actual == expected


def test_default_config(tmp_path):
    text = build_config()
    (tmp_path / "config.yaml").write_text(text)
    config = load_config(None, cwd=tmp_path)
    # A builder emitting a different valid provider would otherwise go unnoticed.
    assert (text, [provider.name for provider in config.providers]) == (CLI_TEXT, ["claude"])


def test_overrides_load(tmp_path):
    text = build_config(
        state_dir="custom-state",
        providers=[{"name": "custom", "auth": "CUSTOM_KEY", "models": {"low": "a", "medium": "b", "high": "c", "max": "d"}, "limits": {"concurrency": 3, "est_cost_per_call_usd": 2.5}}],
        routing=[{"tier": "high", "surface": "review", "candidates": [{"provider": "custom", "model": "explicit"}]}],
        inventory=("custom.yaml", "policy.md"),
    )
    (tmp_path / "config.yaml").write_text(text)
    config = load_config(None, cwd=tmp_path)
    # Ignoring any override produces a different loaded field, rather than a matching default.
    assert (
        config.state_dir,
        config.providers[0].name,
        config.providers[0].auth,
        config.providers[0].models_by_tier.model_dump(),
        config.providers[0].limits.concurrency,
        config.providers[0].limits.est_cost_per_call_usd,
        config.routing[0].model_dump(exclude_none=True),
        config.engine_plane_safety_inventory,
    ) == (
        tmp_path / "custom-state",
        "custom",
        "CUSTOM_KEY",
        {"low": "a", "medium": "b", "high": "c", "max": "d"},
        3,
        2.5,
        {"tier": "high", "surface": "review", "candidates": [{"provider": "custom", "model": "explicit"}]},
        ["custom.yaml", "policy.md"],
    )


def test_amend_config_preserves_and_accumulates(tmp_path):
    path = tmp_path / "config.yaml"
    original = yaml.safe_load(build_config())
    original["notify"] = ["old-notifier"]
    path.write_text(yaml.safe_dump(original))
    review = {"gate_severity": {"scope_fence": "soft"}}
    amend_config(tmp_path, review=review, notify=None)
    expected = {**original, "review": review}
    del expected["notify"]
    # Replacing the mapping, retaining notify, or ignoring review each changes this mapping.
    assert yaml.safe_load(path.read_text()) == expected
    amend_config(tmp_path, scheduler={"max_unmerged": 7}, absent=None)
    # Rebuilding from defaults loses the first edit; writing absent=null adds an unwanted key.
    assert yaml.safe_load(path.read_text()) == {**expected, "scheduler": {"max_unmerged": 7}}
