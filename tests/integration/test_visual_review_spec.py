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
