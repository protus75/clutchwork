"""Schema-valid evidence fixtures shared by harvest and envelope tests."""

from clutch.evidence.store import EvidenceStore
from clutch.seams import LocalFileSystem


def seed_end(state_dir, key, stdout, wall_end):
    fs = LocalFileSystem()
    store = EvidenceStore(state_dir, fs, fs.read_bytes, fs.size, lambda text: text)
    store.write_record(
        key,
        "end",
        {
            "schema": "clutch.evidence.call/1.0",
            "id": key,
            "exit": {"status": "ok", "code": 0, "signal": None, "failure_class": None},
            "clock": {"wall_end": wall_end, "mono_end_ns": 17, "wall_ms": 3},
            "rusage": None,
            "raw": {
                "stdout": store.put_blob(stdout.encode()),
                "stderr": store.put_blob(b""),
                "stdout_times": store.put_blob(b"[]"),
                "lines": len(stdout.splitlines()),
                "non_json_lines": len(stdout.splitlines()),
            },
            "repo": None,
            "model": {"served": None, "served_source": "none"},
            "native_ids": {"session_id": None, "thread_id": None},
            "parsed": {"text_chars": len(stdout), "input_tokens": None, "output_tokens": None, "usd": None},
        },
    )
    return store
