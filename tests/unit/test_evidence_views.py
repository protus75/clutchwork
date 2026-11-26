"""Pure views built from inline streams and an in-memory evidence store."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Evidence views from streams and an in-memory store
# relates: [clutch/evidence/claude.py, clutch/evidence/codex.py, clutch/evidence/schema.py, clutch/evidence/store.py, clutch/evidence/views.py, tests/fakes.py]
# owner: engine
# verified: 69d790e1
# hash: 421ff20c88ebbe30ffc0c681847afb556c58444f424a33074f8b5b648192ece4

import json

import pytest

from clutch.evidence import claude, codex, views
from clutch.evidence.schema import Start
from clutch.evidence.store import SKIP, EvidenceStore
from tests.fakes import FakeFileSystem

CODEX = (
    b'{"type":"thread.started","thread_id":"thread-a"}\n'
    b'{"type":"item.completed","item":{"type":"agent_message","text":"reply"}}\n'
    b'{"type":"turn.completed","usage":{"input_tokens":13,"output_tokens":5}}\n'
    b'{"type":"future.event"}\n'
)
CLAUDE = b'{"type":"system","subtype":"init"}\n{"type":"assistant","message":{"content":[{"type":"text","text":"hello"}]}}\n'


def start_record(provider="codex", version="1.2"):
    return Start.model_validate(
        {
            "schema": "clutch.evidence.call/1.0",
            "id": "llm/test/1/implement/0/1",
            "group": "test",
            "stem": "test",
            "run_seq": 1,
            "attempt": 0,
            "surface": "implement",
            "call": 1,
            "engine": {"version": "1", "spec": "implement.md", "spec_version": "1"},
            "route": {"tier": "medium", "effort": "medium", "candidates": [provider], "chosen": provider, "reason": "first", "config_sha": "config"},
            "provider": {"name": provider, "adapter": "TestAdapter", "kind": "cli", "package": "test", "cli_version": version, "billing": "subscription"},
            "model": {"requested": "m"},
            "process": {"argv": ["test"], "env_names": [], "cwd": "/test", "timeout_s": 30, "writes": False, "isolated": False, "conduct_file": None},
            "repo": None,
            "prompt": {"blob": "sha256:" + "a" * 64, "chars": 3, "bytes": 3},
            "clock": {"wall_start": "2026-01-01", "mono_start_ns": 10},
        }
    )


def memory_store(tmp_path):
    fs = FakeFileSystem()
    return EvidenceStore(tmp_path, fs, fs.read_bytes, fs.size, lambda text: text)


def stored_view(store, provider, stdout, version="1.2"):
    start = start_record(provider, version)
    store.write_record(start.id, "start", start.model_dump(by_alias=True))
    ref = store.put_blob(stdout)
    times = [7_000_000 + i * 2_000_000 for i in range(len(stdout.splitlines()))]
    return views.build_view(store.read_record(start.id, "start"), store.get_blob(ref), times, store.put_blob)


def test_codex_view(tmp_path):
    store = memory_store(tmp_path)
    view = stored_view(store, "codex", CODEX)
    expected = [event.model_dump(by_alias=True) for event in codex.normalize(CODEX, [7_000_000, 9_000_000, 11_000_000, 13_000_000], store.put_blob)]
    # Rules out empty views, lost arrival times, missing aliases or a wrong normalizer/verification flag.
    assert view == {"schema": "clutch.evidence.events/1.0", "normalizer": codex.NORMALIZER_ID, "unverified": False, "events": expected}
    assert len(view["events"]) == 4


@pytest.mark.parametrize("provider,unverified", [("qwen", True), ("claude", False)])
def test_claude_verification(tmp_path, provider, unverified):
    view = stored_view(memory_store(tmp_path), provider, CLAUDE)
    # Rules out treating qwen as verified or selecting a provider-specific id for it.
    assert (view["normalizer"], view["unverified"]) == (claude.NORMALIZER_ID, unverified)


def test_selection():
    # Rules out dropping Gemini support or routing an unsupported provider to Claude.
    assert (views.normalizer("antigravity").NORMALIZER_ID, views.normalizer("other")) == ("antigravity-stream/1", None)


def test_coverage(tmp_path):
    store = memory_store(tmp_path)
    view = stored_view(store, "codex", CODEX)
    other = stored_view(memory_store(tmp_path / "claude"), "claude", CLAUDE)
    rows, skipped = views.coverage([(start_record(), [view]), (start_record("codex", "2.0"), []), (start_record("claude"), [other]), (SKIP, [])], 2)
    # Rules out counting unknown events as known, merging providers/versions, dropping zero-event groups, or omitting skipped records.
    assert (rows, skipped) == (
        [
            {"provider": "claude", "cli_version": "1.2", "known_pct": 100.0, "unknown": []},
            {"provider": "codex", "cli_version": "1.2", "known_pct": 75.0, "unknown": [("future.event", 1)]},
            {"provider": "codex", "cli_version": "2.0", "known_pct": 0.0, "unknown": []},
        ],
        3,
    )
    # Distinct counts and an alphabetically earlier loser rule out lexical ordering instead of frequency.
    ranked, _ = views.coverage([(start_record(version=None), [{"events": [{"kind": "unknown", "native_type": name} for name in ["a", "z", "z"]]}])])
    assert ranked == [{"provider": "codex", "cli_version": None, "known_pct": 0.0, "unknown": [("z", 2), ("a", 1)]}]


def test_show_lines(tmp_path):
    store = memory_store(tmp_path)
    view = stored_view(store, "codex", CODEX)
    lines = views.show_lines(start_record(), None, [view])
    # Rules out omitted envelopes, normalized headers, fields or event lines.
    assert lines == [
        "start.json: " + json.dumps(start_record().model_dump(by_alias=True), indent=2),
        "end.json: missing",
        "normalized/codex-stream/1 unverified=False",
        "0 7 session_start thread.started",
        "1 9 message item.completed",
        "2 11 usage turn.completed",
        "3 13 unknown future.event",
    ]
    # Rules out trying to dump an unsupported envelope as a model.
    assert views.show_lines(SKIP, SKIP, []) == ["start.json: skipped (unknown major version)", "end.json: skipped (unknown major version)"]
