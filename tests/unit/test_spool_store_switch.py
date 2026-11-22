# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that Spool writes redacted, stem-validated captures into the EvidenceStore. Also checks that harvest picks error reasons and check logs and skips unreadable captures.
# relates: [clutch/config.py, clutch/driver.py, clutch/evidence/store.py, clutch/redact.py, clutch/runner.py, clutch/seams.py]
# owner: engine
# verified: 73ec5da9
# hash: 3e3d2ff80dbec41e9d1aeda3c3f9523b3f064eb55fdcf05cfe6f99431a75c6ab
import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import runner
from clutch.config import TrainingData
from clutch.driver import Spool
from clutch.evidence.store import EvidenceStore
from clutch.redact import Redactor
from clutch.seams import LocalFileSystem
from tests.git_fake import GitFake


def test_writer_stores_redacted_and_validated_captures(tmp_path):
    fs = LocalFileSystem()
    redactor = Redactor({"KEY": "s3cret"})
    spool = Spool(tmp_path, redactor, fs)
    store = EvidenceStore(tmp_path, fs, fs.read_bytes, fs.size, redactor.scrub)
    spool.write("work/1", 2, "review/call-01/output.txt", "a s3cret b")
    assert store.get_capture("work", 2, "run-1/review/call-01/output.txt") == b"a [REDACTED:KEY] b"
    spool.write("my-ticket", 0, "merge/host-01.txt", "x")
    assert store.get_capture("my-ticket", 0, "merge/host-01.txt") == b"x"
    spool.write("my-ticket", 0, "merge/host-01.txt", "second")
    assert store.get_capture("my-ticket", 0, "merge/host-01.txt") == b"second"
    assert not (tmp_path / "spools").exists()
    for stem in ("Bad Stem", "work/01"):
        with pytest.raises(ValueError):
            spool.write(stem, 1, "x", "t")
    assert store.captures("work", 1) == []


def test_harvest_filters_and_skips_unreadable(tmp_path, monkeypatch):
    fs = LocalFileSystem()
    redactor = Redactor({})
    spool = Spool(tmp_path / "state", redactor, fs)
    store = spool._store
    for stem, name, text in [
        ("ticket", "implement/call-02/error.txt", "later call"),
        ("ticket", "implement/call-01/error.txt", "earlier call"),
        ("ticket", "implement/call-01/prompt.md", "SECRET PROMPT"),
        ("ticket", "check/verify-01.txt", "verify log"),
        ("ticket/3", "review/call-01/error.txt", "SLOT LOG"),
        ("ticket", "check/broken.txt", "broken"),
        ("ticket", "check/denied.txt", "denied"),
    ]:
        spool.write(stem, 0, name, text)
    (store.root / "captures/ticket/0/check%2Fbroken.txt.json").write_text("bad json")
    original = fs.read_bytes

    def read(path):
        if path.name == "check%2Fdenied.txt.json":
            raise PermissionError(path)
        return original(path)

    monkeypatch.setattr(fs, "read_bytes", read)
    ctx = SimpleNamespace(
        config=SimpleNamespace(state_dir=tmp_path / "state", providers=[], training_data=TrainingData(enabled=True)),
        repo=tmp_path,
        worktree=lambda stem: tmp_path / "work",
        fs=fs,
        driver=SimpleNamespace(redactor=redactor, journal=SimpleNamespace(append=lambda *args, **kwargs: None)),
        git=GitFake(diff_stat="stat", diff="", rev_parse="sha"),
    )
    monkeypatch.setattr(runner, "lift_outbox", AsyncMock())

    async def run(attempt):
        await runner.harvest(ctx, "ticket", attempt=attempt, stage="check", terminal="gate_failed", findings=[], results=())

    asyncio.run(run(0))
    artifact = json.loads((tmp_path / "work/tickets/ticket/attempts/0/harvest.json").read_text())
    assert artifact["reason"] == "later call"
    assert "verify log" in artifact["stage_log_tail"]
    assert "SECRET PROMPT" not in artifact["stage_log_tail"] and "SLOT LOG" not in artifact["stage_log_tail"]
    attempt = store.read_attempt("ticket", 0, 0)
    assert set(attempt.check_outputs) == {"verify-01.txt"}
    assert store.get_blob(attempt.check_outputs["verify-01.txt"]) == b"verify log"
    asyncio.run(run(1))
    artifact = json.loads((tmp_path / "work/tickets/ticket/attempts/1/harvest.json").read_text())
    assert artifact["reason"] == "gate_failed" and artifact["stage_log_tail"] == ""
    assert store.read_attempt("ticket", 1, 1).check_outputs == {}
