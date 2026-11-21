from pathlib import Path

from clutch.specs import load_spec, render


def test_meta_spec():
    spec = load_spec((Path(__file__).resolve().parents[2] / "clutch/specs/meta.md").read_text())
    assert spec.meta.llm_surface == "meta"
    assert spec.inputs == ("files", "retry_findings")
    text = render(spec, {"files": "file payload", "retry_findings": "retry payload"})
    assert "file payload" in text and "retry payload" in text
