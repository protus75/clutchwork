# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that observe reads capability defaults from the prompt spec metadata, and that observe, retro and __main__ contain no hand-written YAML or ticket-section readers.
# relates: [clutch/observe.py, clutch/specs/__init__.py]
# owner: clutch/specs/__init__.py
# verified: d32c32ad
# hash: dfd4ad6938715b5205dbb018c4900dcd0b0023c6ac9b1b3f726009ad6f25f0ef
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import observe
from clutch.specs import load_spec

pytestmark = pytest.mark.disk_io_skip

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
