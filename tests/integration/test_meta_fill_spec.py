# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Metadata fill spec inputs and rendering
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 75d75946
# hash: 1ff080b1dee35fdb21c8aeee2c50a5e9f6ef875bdd4a5b3a5cdbe35ae8ab13b7
from pathlib import Path

from clutch.specs import load_spec, render


def test_meta_spec():
    spec = load_spec((Path(__file__).resolve().parents[2] / "clutch/specs/meta.md").read_text())
    assert spec.meta.llm_surface == "meta"
    assert spec.inputs == ("files", "retry_findings")
    text = render(spec, {"files": "file payload", "retry_findings": "retry payload"})
    assert "file payload" in text and "retry payload" in text
