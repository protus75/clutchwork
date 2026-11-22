"""The operator prune command uses the existing store and writer lock."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that `evidence prune --to-gb` deletes the oldest eligible blobs to the target, keeps records, refuses a negative target and refuses while the writer lock is held
# relates: [clutch/__main__.py, clutch/lockfile.py, clutch/seams.py, tests/cli_helpers.py, tests/evidence_records.py]
# owner: clutch/__main__.py
# verified: 2036efdf
# hash: 01fe22bebc34363d92c59409dce82eb485f55e4403d9ec07f1ab1261c24bc85e

from unittest.mock import AsyncMock

from clutch import __main__ as cli
from clutch.lockfile import Lockfile
from clutch.seams import LocalFileSystem
from tests.cli_helpers import CONFIG
from tests.evidence_records import seed_end


def test_prune_command(tmp_path, monkeypatch, capsys):
    (tmp_path / "config.yaml").write_text(CONFIG)
    state = tmp_path / ".clutch/state"
    store = seed_end(state, "older", "old distinct reply", "2020-01-01T00:00:00Z")
    seed_end(state, "newer", "new distinct reply", "2021-01-01T00:00:00Z")
    old = store.read_record("older", "end").raw.stdout
    new = store.read_record("newer", "end").raw.stdout
    records = sorted((store.root / "calls").rglob("*.json"))
    monkeypatch.setattr(LocalFileSystem, "size", lambda self, path: 400_000_000)
    monkeypatch.setattr(cli.Git, "describe", AsyncMock(return_value="test"))
    assert cli.main(["evidence", "prune", "--to-gb", "1"], cwd=tmp_path) == 0
    assert "1600000000 bytes before, 800000000 bytes after" in capsys.readouterr().out
    assert not store._blob_path(old).exists() and store._blob_path(new).exists()
    assert all(p.exists() for p in records)
    assert cli.main(["evidence", "prune", "--to-gb", "1"], cwd=tmp_path) == 0
    assert store._blob_path(new).exists()
    assert cli.main(["evidence", "prune", "--to-gb", "-1"], cwd=tmp_path) == 2
    assert "nonnegative" in capsys.readouterr().err
    lock = Lockfile(state, verb="test", instance_id="test", clock=cli._clock)
    lock.acquire()
    try:
        assert cli.main(["evidence", "prune", "--to-gb", "1"], cwd=tmp_path) == 2
    finally:
        lock.release()
