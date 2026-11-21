# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test runner attempt manifest
# relates: [clutch/config.py, clutch/evidence/store.py, clutch/redact.py, clutch/runner.py, clutch/seams.py, tests/unit/test_evidence_schema.py]
# owner: engine
# verified: e3a6f154
# hash: 7f2e2bc8e3e343bfe596b86ae1b0b7ae81f933024c584ff0838bb250d8fb898f
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import runner
from clutch.config import TrainingData
from clutch.evidence.store import EvidenceStore
from clutch.redact import Redactor
from clutch.seams import LocalFileSystem
from tests.spool_captures import write_capture
from tests.unit.test_evidence_schema import start


@pytest.mark.parametrize("terminal", ["gate_failed", "premise_failed", "rejected", "abandoned"])
def test_manifest_harvest(tmp_path, monkeypatch, terminal):
    fs = LocalFileSystem()
    config = SimpleNamespace(state_dir=tmp_path / "state", providers=[], training_data=TrainingData(enabled=True, exclude=["secrét*"]))
    diff = 'diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n+visible\ndiff --git a/.env.local b/.env.local\n+hidden\ndiff --git "a/secr\\303\\251t.key" "b/secr\\303\\251t.key"\n+private\n'
    journal = SimpleNamespace(append=lambda *a, **kw: None)
    ctx = SimpleNamespace(
        config=config,
        repo=tmp_path,
        worktree=lambda stem: tmp_path / "work",
        fs=fs,
        driver=SimpleNamespace(redactor=Redactor({}), journal=journal),
        git=SimpleNamespace(diff_stat=AsyncMock(return_value="stat"), diff=AsyncMock(return_value=diff), rev_parse=AsyncMock(side_effect=lambda repo, ref: {"main": "base", "sample": "head"}[ref])),
    )
    monkeypatch.setattr(runner, "lift_outbox", AsyncMock())

    async def run(attempt):
        await runner.harvest(ctx, "sample", attempt=attempt, stage="check", terminal=terminal, findings=[], results=())

    store = EvidenceStore(config.state_dir, fs, fs.read_bytes, fs.size, lambda s: s)
    for run_seq in (0, 1):
        store.write_record(f"llm/sample/{run_seq}/implement/0/0", "start", start())
    write_capture(config.state_dir, "sample", 1, "check/output.txt", b"check failure")
    asyncio.run(run(1))
    asyncio.run(run(2))
    store = EvidenceStore(config.state_dir, fs, fs.read_bytes, fs.size, lambda s: s)
    first = store.read_attempt("sample", 1, 1)
    second = store.read_attempt("sample", 2, 2)
    assert first.outcome == terminal
    assert first.call_keys == ["llm/sample/1/implement/0/0"]
    assert second.call_keys == []
    assert first.engine_versions == ["v"]
    assert first.spec_versions == {"s": "1"}
    assert store.get_blob(first.check_outputs["output.txt"]) == b"check failure"
    assert (first.base_sha, first.head_sha) == ("base", "head")
    assert first.diff_blob == second.diff_blob
    stored = store.get_blob(first.diff_blob).decode()
    assert stored == "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n+visible\n"
    assert len(list((store.root / "attempts/sample/1").glob("*.json"))) == 1


def test_disabled_and_failure_preserve_harvest(tmp_path, monkeypatch):
    fs = LocalFileSystem()
    config = SimpleNamespace(state_dir=tmp_path / "state", providers=[], training_data=TrainingData())
    signals = []
    ctx = SimpleNamespace(
        config=config,
        repo=tmp_path,
        worktree=lambda stem: tmp_path / "work",
        fs=fs,
        driver=SimpleNamespace(redactor=Redactor({}), journal=SimpleNamespace(append=lambda *a, **kw: signals.append(a))),
        git=SimpleNamespace(diff_stat=AsyncMock(return_value="stat"), diff=AsyncMock(side_effect=ValueError("failed"))),
    )
    lift = AsyncMock()
    monkeypatch.setattr(runner, "lift_outbox", lift)

    def run():
        asyncio.run(runner.harvest(ctx, "sample", attempt=4, stage=None, terminal="abandoned", findings=[], results=()))

    run()
    assert not (config.state_dir / "evidence/attempts").exists()
    config.training_data = TrainingData(enabled=True)
    run()
    assert (tmp_path / "work/tickets/sample/attempts/4/harvest.json").is_file()
    assert lift.await_count == 2
    assert len(signals) == 1
