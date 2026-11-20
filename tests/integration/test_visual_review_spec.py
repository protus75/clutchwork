# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test visual review spec
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 96e46658
# hash: 8f23a16138335d32298f508816921d4fc29a7c0f59af5385826105627d67f393
from pathlib import Path

import pytest

from clutch.specs import SpecError, load_spec


def test_spec_lints():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/review_visual.md").read_text()
    spec = load_spec(text)
    assert spec.meta.llm_surface == "review_visual"
    assert spec.meta.version == "1.0"
    with pytest.raises(SpecError):
        load_spec(text.replace("llm_surface: review_visual", "llm_surface: nonexistent"))
