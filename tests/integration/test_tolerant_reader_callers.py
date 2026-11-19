from pathlib import Path
from types import SimpleNamespace

from clutch import observe
from clutch.specs import load_spec

ROOT = Path(__file__).resolve().parents[2]


def test_capability_spec_reads(tmp_path):
    ctx = SimpleNamespace(root=tmp_path)
    resolve = load_spec((ROOT / "clutch/specs/resolve.md").read_text()).meta
    review = load_spec((ROOT / "clutch/specs/requisition_review.md").read_text()).meta
    assert observe.capability(ctx, [], "missing", "resolve") == f"{resolve.tier}/{resolve.effort}"
    assert observe.capability(ctx, [], "missing", "requisition_review") == f"medium/{review.effort}"


def test_no_hand_readers():
    for name in ("observe.py", "retro.py", "__main__.py"):
        source = (ROOT / "clutch" / name).read_text()
        for forbidden in ("yaml.safe_load", '"## Depends on"', "expected: (", 'split("---"'):
            assert forbidden not in source, (name, forbidden)
