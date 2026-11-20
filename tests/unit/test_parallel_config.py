# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test parallel config
# relates: [clutch/config.py, clutch/doctor.py]
# owner: engine
# verified: 9a610809
# hash: 41f9e6a0f537fceb11b4f3a34652c924eea45bb1e3ad326359f97491467e34be
import asyncio
from datetime import datetime, timezone

import pytest
import yaml

from clutch import doctor
from clutch.config import ConfigError, load_config


def write_config(tmp_path, parallel=None, *, concurrency=1, route=True):
    raw = {
        "schema_version": 1,
        "state_dir": ".state",
        "providers": [
            {"name": "other", "kind": "cli", "package": "other", "models_by_tier": dict.fromkeys(("low", "medium", "high", "max"), "m"), "limits": {"concurrency": 9}},
            {"name": "target", "kind": "cli", "package": "target", "models_by_tier": dict.fromkeys(("low", "medium", "high", "max"), "m"), "limits": {"concurrency": concurrency}},
        ],
        "routing": [
            {"tier": "low", "surface": "implement", "candidates": [{"provider": "other"}]},
            {"tier": "medium", "surface": "implement" if route else "review", "candidates": [{"provider": "target"}, {"provider": "other"}]},
        ],
        "review": {},
        "merge": {},
        "engine_plane_safety_inventory": [],
    }
    if parallel is not None:
        raw["scheduler"] = {"parallel": parallel}
    (tmp_path / "config.yaml").write_text(yaml.safe_dump(raw))
    return load_config(None, cwd=tmp_path)


def test_defaults_and_values(tmp_path):
    default = write_config(tmp_path).scheduler.parallel
    assert (default.enabled, default.max_runs, default.shared_paths) == (False, 2, [])
    configured = write_config(tmp_path, {"enabled": True, "max_runs": 3, "shared_paths": ["docs/how-clutch-works.md"]}).scheduler.parallel
    assert (configured.enabled, configured.max_runs, configured.shared_paths) == (True, 3, ["docs/how-clutch-works.md"])


@pytest.mark.parametrize(("block", "key"), [({"max_runs": 0}, "max_runs"), ({"bogus": 1}, "bogus"), ({"shared_paths": ["/abs/path"]}, "shared_paths")])
def test_invalid(tmp_path, block, key):
    with pytest.raises(ConfigError) as exc:
        write_config(tmp_path, block)
    assert key in exc.value.key


class Exec:
    async def run(self, argv, **kwargs):
        return 0, "git version fixture", ""


def checks(tmp_path, monkeypatch):
    async def current(*args):
        return []

    monkeypatch.setattr(doctor, "stale_core", current)
    return asyncio.run(doctor.check(repo=tmp_path, config_path=None, env={}, exec_=Exec(), clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc), sleep=asyncio.sleep, in_venv=True))


def test_doctor_mismatch(tmp_path, monkeypatch):
    write_config(tmp_path, {"enabled": True, "max_runs": 3})
    results = checks(tmp_path, monkeypatch)
    row = results[-1]
    assert row.name == "parallel" and not row.passed
    assert all(word in row.detail for word in ("max_runs", "3", "target", "concurrency", "1", "lower", "raise"))
    assert doctor.render(results).startswith("doctor: failed\n")


@pytest.mark.parametrize(
    ("parallel", "concurrency", "route"), [({"enabled": True, "max_runs": 2}, 2, True), ({"enabled": False, "max_runs": 5}, 1, True), ({"enabled": True, "max_runs": 5}, 1, False)]
)
def test_doctor_no_row(tmp_path, monkeypatch, parallel, concurrency, route):
    write_config(tmp_path, parallel, concurrency=concurrency, route=route)
    assert all(row.name != "parallel" for row in checks(tmp_path, monkeypatch))


def test_doctor_invalid_config_has_no_parallel_row(tmp_path, monkeypatch):
    (tmp_path / "config.yaml").write_text("schema_version: 1\n")
    assert all(row.name != "parallel" for row in checks(tmp_path, monkeypatch))
