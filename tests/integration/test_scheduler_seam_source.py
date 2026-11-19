from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_scheduler_does_not_reconstruct_queue_seams():
    source = (ROOT / "clutch/scheduler.py").read_text()
    for forbidden in ("journal._fs", "journal._clock", "journal.dir"):
        assert forbidden not in source
