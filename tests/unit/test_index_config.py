# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Index configuration defaults and validation
# relates: [clutch/config.py]
# owner: clutch/config.py
# verified: 75d75946
# hash: 1720f662748d96f2c928e7abbf0820d38de066397ef97829c0599c30452a4e3f
from pathlib import Path

import pytest
from pydantic import ValidationError

from clutch.config import Config, ConfigError, Index, load_config


def test_index_defaults_and_argv():
    assert Config.model_fields["index"].default == Index()
    assert Index().embed is None
    assert Index(embed=["x"]).embed == ["x"]
    for invalid in ("x", []):
        with pytest.raises(ValidationError):
            Index(embed=invalid)


def test_loader_rejects_null_and_defaults_omitted(tmp_path: Path):
    path = tmp_path / "config.yaml"
    base = """schema_version: 1
state_dir: .clutch
providers:
  - name: p
    kind: cli
    package: p
    models_by_tier: {low: a, medium: b, high: c, max: d}
    limits: {concurrency: 1}
routing:
  - tier: medium
    surface: review
    candidates: [{provider: p}]
review: {}
merge: {}
engine_plane_safety_inventory: []
"""
    path.write_text(base + "index: {embed: null}\n")
    with pytest.raises(ConfigError, match="null"):
        load_config(path, cwd=tmp_path)
    path.write_text(base)
    assert load_config(path, cwd=tmp_path).index.embed is None
