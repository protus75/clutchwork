"""Evidence retention and warnings at the shared size boundary."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that provider calls never prune evidence automatically and that the size warning appears in view status and host doctor only above evidence.warn_gb
# relates: [clutch/__main__.py, clutch/doctor.py, clutch/evidence/store.py, clutch/seams.py, tests/cli_helpers.py, tests/evidence_records.py]
# owner: clutch/evidence/store.py
# verified: 2036efdf
# hash: 54172028b2c1d31480b11bd57ed8d79732923585661701864bffcd66bc49dec7

import asyncio
from unittest.mock import AsyncMock

from clutch import __main__ as cli
from clutch import doctor
from clutch.evidence.store import EvidenceStore, size_warning
from clutch.seams import LocalFileSystem
from tests.cli_helpers import CONFIG
from tests.evidence_records import seed_end
from tests.unit.test_evidence_envelope import Rig


def test_provider_preserves_old_blob(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    old = seed_end(rig.cfg.state_dir, "old", "old reply", "2020-01-01T00:00:00Z")
    ref = old.read_record("old", "end").raw.stdout
    monkeypatch.setattr(rig.fs, "size", lambda path: 21 * 10**9)
    asyncio.run(rig.call())
    # Rules out automatic pruning of an old eligible reply.
    assert old.get_blob(ref) == b"old reply"


def test_size_warning_doctor_and_status(tmp_path, monkeypatch, capsys):
    (tmp_path / "config.yaml").write_text(CONFIG)
    fs = LocalFileSystem()
    store = EvidenceStore(tmp_path / ".clutch/state", fs, fs.read_bytes, fs.size, lambda x: x)
    store.put_blob(b"seed")
    monkeypatch.setattr(cli, "_status", AsyncMock(return_value="projection"))
    monkeypatch.setattr(cli, "render", lambda projection: projection + "\n")
    size = [20 * 10**9]
    monkeypatch.setattr(LocalFileSystem, "size", lambda self, path: size[0])
    store.size = fs.size
    assert size_warning(store, 20) is None  # Rules out warning at the boundary.
    size[0] -= 1
    assert size_warning(store, 20) is None  # Rules out warning below the threshold.
    assert cli.main(["view", "status"], cwd=tmp_path) == 0
    assert not any(x.startswith("evidence:") for x in capsys.readouterr().out.splitlines())
    size[0] += 2
    message = size_warning(store, 20)
    assert all(part in message for part in ("20000000001", "20 GB", "evidence.warn_gb", "clutch training export --out", "clutch evidence prune --to-gb"))
    assert cli.main(["view", "status"], cwd=tmp_path) == 0
    assert [x for x in capsys.readouterr().out.splitlines() if x.startswith("evidence:")] == [f"evidence: {message}"]
    monkeypatch.setattr(doctor.Git, "_run", AsyncMock(return_value="git test"))
    monkeypatch.setattr(doctor, "stale_core", AsyncMock(return_value=[]))
    results = asyncio.run(doctor.check(repo=tmp_path, config_path=None, env={}, exec_=None, clock=lambda: None, sleep=None, in_venv=True))
    output = doctor.render(results)
    assert output.startswith("doctor: ok\n")
    assert f"WARN evidence: {message}\n" in output
    size[0] -= 2
    results = asyncio.run(doctor.check(repo=tmp_path, config_path=None, env={}, exec_=None, clock=lambda: None, sleep=None, in_venv=True))
    assert not any(row.name == "evidence" for row in results)
