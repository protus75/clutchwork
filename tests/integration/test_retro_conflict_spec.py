from pathlib import Path

from clutch.specs import lint_spec, load_spec


def test_retro_spec_names_conflict_shape():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/retro.md").read_text()
    assert lint_spec(text) == []
    spec = load_spec(text)
    assert spec.meta.version != "1.5"
    for word in ("conflict_paths", "conflict_action", "strategy", "split", "mechanical"):
        assert word in spec.body
