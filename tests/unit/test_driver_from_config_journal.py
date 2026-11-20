# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test driver from config journal
# relates: [clutch/config.py, clutch/driver.py, clutch/journal.py, clutch/llm.py]
# owner: engine
# verified: 0a308920
# hash: 74f50941c12885bb94fa2ecb22f6260abfdfc2bd75e2be71bde323431ca11d82
from datetime import UTC, datetime

import pytest

from clutch.config import load_config_text
from clutch.driver import Driver
from clutch.journal import Journal
from clutch.llm import FakeLLM


def test_from_config_requires_and_uses_caller_journal(tmp_path):
    config = load_config_text(
        """
schema_version: 1
state_dir: state
providers:
  - name: claude
    kind: cli
    package: test-cli
    auth: KEY
    models_by_tier: {low: haiku, medium: sonnet, high: opus, max: opus}
    limits: {concurrency: 1, est_cost_per_call_usd: 0.25}
routing:
  - {tier: medium, surface: implement, candidates: [{provider: claude, model: sonnet}]}
review: {}
merge: {}
engine_plane_safety_inventory: [specs/]
""",
        path=tmp_path / "config.yaml",
        cwd=tmp_path,
    )

    def clock():
        return datetime(2026, 10, 5, tzinfo=UTC)

    journal = Journal(tmp_path / "other", clock)
    kwargs = dict(llm=FakeLLM([]), env={}, clock=clock, sleep=None)
    driver = Driver.from_config(config, journal=journal, **kwargs)
    assert driver.journal is journal
    with pytest.raises(TypeError):
        Driver.from_config(config, **kwargs)
