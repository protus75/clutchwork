# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test evidence attempt manifest
# relates: [clutch/evidence/store.py, clutch/seams.py]
# owner: engine
# verified: 0a308920
# hash: fcccafa341ee28a6a01b4a45def0996fb4bc6956cfffb1115004ce3367a844df
import json

import pytest
from pydantic import ValidationError

from clutch.evidence.store import SKIP, EvidenceStore
from clutch.seams import LocalFileSystem


def test_attempt_versions_and_strict_writer(tmp_path):
    fs = LocalFileSystem()
    store = EvidenceStore(tmp_path, fs, fs.read_bytes, fs.size, lambda s: s)
    data = dict(
        schema="clutch.evidence.attempt/1.0",
        stem="sample",
        run_seq=2,
        attempt=3,
        base_sha="base",
        head_sha="head",
        diff_blob="blob",
        check_outputs={"check": "output"},
        call_keys=["key"],
        outcome="rejected",
        reason="reason",
        findings=[],
        engine_versions=["v"],
        spec_versions={"spec": "v2"},
    )
    store.write_attempt(data)
    record = store.read_attempt("sample", 2, 3)
    assert record.model_dump(by_alias=True) == data
    with pytest.raises(ValidationError):
        store.write_attempt({**data, "extra": True})
    with pytest.raises(ValidationError):
        store.write_attempt({**data, "attempt": "3"})
    path = store.root / "attempts/sample/2/3.json"
    path.write_text(json.dumps({**data, "schema": "clutch.evidence.attempt/1.7", "extra": "future"}))
    assert store.read_attempt("sample", 2, 3) == record
    path.write_text(json.dumps({**data, "schema": "clutch.evidence.attempt/2.0"}))
    assert store.read_attempt("sample", 2, 3) is SKIP
