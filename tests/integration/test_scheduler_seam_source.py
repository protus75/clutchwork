from pathlib import Path


def test_scheduler_does_not_reconstruct_queue_seams():
    source = Path("clutch/scheduler.py").read_text()
    for forbidden in ("journal._fs", "journal._clock", "journal.dir"):
        assert forbidden not in source
