# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test retro conflict spec
# relates: [clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: 96e46658
# hash: 7f1e3d9efe93d4b9329ca54f694bacf6447c0739507662d1a475fc3f46b81ca1
from pathlib import Path

from clutch.specs import lint_spec, load_spec


def test_retro_spec_names_conflict_shape():
    text = (Path(__file__).resolve().parents[2] / "clutch/specs/retro.md").read_text()
    assert lint_spec(text) == []
    spec = load_spec(text)
    assert spec.meta.version != "1.5"
    for word in ("conflict_paths", "conflict_action", "strategy", "split", "mechanical"):
        assert word in spec.body
