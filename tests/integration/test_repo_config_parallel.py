# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test repo config parallel
# relates: [clutch/config.py]
# owner: clutch/config.py
# verified: 96e46658
# hash: d5620681bf631fecd224c5e19fc8139f74004fda9d40ba536e8a8b7013588963
from pathlib import Path

from clutch.config import load_config


def test_repo_parallel_config():
    repo = Path(__file__).resolve().parents[2]
    config = load_config(repo / "config.yaml", cwd=repo)
    parallel = config.scheduler.parallel
    assert parallel.enabled is True
    assert parallel.max_runs == 2
    assert parallel.shared_paths == ["docs/how-clutch-works.md"]

    route = next(r for r in config.routing if r.tier == config.routing_default_tier and r.surface == "implement")
    provider = next(p for p in config.providers if p.name == route.candidates[0].provider)
    assert provider.limits.concurrency >= parallel.max_runs
