# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test scheduler seam source
# relates: []
# owner: engine
# verified: 96e46658
# hash: d03c3412f5dec3f05418e3394d2896b119f4524a14563c8f3f2d4f1a6721bf15
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_scheduler_does_not_reconstruct_queue_seams():
    source = (ROOT / "clutch/scheduler.py").read_text()
    for forbidden in ("journal._fs", "journal._clock", "journal.dir"):
        assert forbidden not in source
