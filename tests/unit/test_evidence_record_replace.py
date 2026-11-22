# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that EvidenceStore.write_record refuses to overwrite an existing record unless replace=True is passed, and that a replaced start record carries the new native_ids
# relates: [clutch/evidence/store.py, clutch/seams.py, tests/unit/test_evidence_schema.py]
# owner: clutch/evidence/store.py
# verified: 19880b1d
# hash: 238a7ca6bf1537f80e6a77f9a8bb900922366d1642373d92b2dfcd8839088aff
import pytest

from clutch.evidence.store import EvidenceStore
from clutch.seams import LocalFileSystem
from tests.unit.test_evidence_schema import start


def test_replace_is_opt_in(tmp_path):
    fs = LocalFileSystem()
    store = EvidenceStore(tmp_path, fs, fs.read_bytes, fs.size, lambda s: s)
    data = start()
    store.write_record("key", "start", data)
    data["native_ids"] = {"session_id": "new", "thread_id": None}
    with pytest.raises(FileExistsError):
        store.write_record("key", "start", data)
    assert store.read_record("key", "start").native_ids is None
    store.write_record("key", "start", data, replace=True)
    assert store.read_record("key", "start").native_ids.session_id == "new"
