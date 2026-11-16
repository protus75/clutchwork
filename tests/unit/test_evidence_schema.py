import pytest
from pydantic import ValidationError

from clutch.evidence.schema import Event, Start, json_schema
from clutch.evidence.store import SKIP, EvidenceStore
from clutch.seams import LocalFileSystem


def start():
    return {
        "schema": "clutch.evidence.call/1.0",
        "id": "llm/a",
        "group": "a",
        "stem": None,
        "run_seq": 1,
        "attempt": 0,
        "surface": "implement",
        "call": 1,
        "engine": {"version": "v", "spec": "s", "spec_version": "1"},
        "route": {"tier": "medium", "effort": "high", "candidates": ["codex"], "chosen": "codex", "reason": "first", "config_sha": "sha"},
        "provider": {"name": "codex", "adapter": "CodexAdapter", "kind": "cli", "package": None, "cli_version": None, "billing": "local"},
        "model": {"requested": "model"},
        "process": {"argv": [], "env_names": [], "cwd": "/tmp", "timeout_s": 1, "writes": True, "isolated": True, "conduct_file": None},
        "repo": None,
        "prompt": {"blob": "sha256:abc", "chars": 2, "bytes": 2},
        "clock": {"wall_start": "now", "mono_start_ns": 1},
    }


def test_strict_writer_tolerant_reader(tmp_path):
    fs = LocalFileSystem()
    store = EvidenceStore(tmp_path, fs, lambda p: p.read_bytes(), lambda p: p.stat().st_size, lambda s: s)
    data = start()
    data["future"] = 17
    data["route"]["future"] = 42
    with pytest.raises(ValidationError):
        store.write_record("key", "start", data)
    path = store._record_path("key", "start")
    import json

    fs.publish(path, json.dumps(data).encode())
    record = store.read_record("key", "start")
    assert isinstance(record, Start)
    assert record.route.chosen == "codex"
    assert not hasattr(record.route, "future")
    data["schema"] = "clutch.evidence.call/2.0"
    fs.write(path, json.dumps(data).encode())
    assert store.read_record("key", "start") is SKIP


def test_schema_and_event():
    schema = json_schema("start")
    assert {"id", "route", "prompt"} <= schema["properties"].keys()
    assert schema["additionalProperties"] is False
    assert schema == json_schema("start")
    data = {"schema": "clutch.evidence.events/1.0", "seq": 7, "t_ms": 42, "kind": "unknown", "native_type": "custom", "native": {}}
    assert Event.model_validate(data).kind == "unknown"
    data["kind"] = "thought"
    with pytest.raises(ValidationError):
        Event.model_validate(data)


def test_writer_and_optional_nested_reader(tmp_path):
    fs = LocalFileSystem()
    store = EvidenceStore(tmp_path, fs, lambda p: p.read_bytes(), lambda p: p.stat().st_size, lambda s: s)
    data = start()
    data["repo"] = {"main_sha": "main", "base_sha": "base", "tree_before": "tree"}
    store.write_record("llm/a", "start", data)
    assert store.read_record("llm/a", "start").repo.tree_before == "tree"
    with pytest.raises(FileExistsError):
        store.write_record("llm/a", "start", data)
    with pytest.raises(ValueError):
        store.write_record("llm/a", "event", data)
    with pytest.raises(ValueError):
        store.read_record("llm/a", "event")
