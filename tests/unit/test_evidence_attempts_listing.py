# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test evidence attempts listing
# relates: [clutch/evidence/store.py, clutch/seams.py]
# owner: engine
# verified: 0a308920
# hash: 618064198dafd3a4484bca80faf9af75bbccb2e0105beb29acd2bfffeb4360dc
from clutch.evidence.store import EvidenceStore
from clutch.seams import LocalFileSystem


def test_listing(tmp_path):
    fs = LocalFileSystem()
    store = EvidenceStore(tmp_path, fs, fs.read_bytes, fs.size, lambda s: s)
    assert store.attempts() == []
    for stem, run, attempt in [("z", 10, 2), ("a", 2, 3), ("a", 1, 4)]:
        store.write_attempt(
            dict(
                schema="clutch.evidence.attempt/1.0",
                stem=stem,
                run_seq=run,
                attempt=attempt,
                base_sha="b",
                head_sha="h",
                diff_blob="d",
                check_outputs={},
                call_keys=[],
                outcome="x",
                reason=None,
                findings=[],
                engine_versions=[],
                spec_versions={},
            )
        )
    assert store.attempts() == [("a", 1, 4), ("a", 2, 3), ("z", 10, 2)]
