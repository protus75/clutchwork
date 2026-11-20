import json
from urllib.parse import quote

import pytest

from clutch.observe import live_call


def record(evidence, key, provider="claude", model="opus", surface="implement", start="2026-01-01T00:00:01+00:00"):
    directory = evidence / "calls" / quote(key, safe="")
    directory.mkdir(parents=True)
    (directory / "start.json").write_text(json.dumps({"provider": {"name": provider}, "model": {"requested": model}, "surface": surface, "clock": {"wall_start": start}}))
    return directory


@pytest.mark.parametrize(("provider", "model"), [("claude", "opus"), ("codex", "gpt")])
def test_open_record(tmp_path, provider, model):
    record(tmp_path, "llm/t/1/implement/0/0", provider, model)
    assert live_call(tmp_path, "t", "implement", "") == f"{provider} {model}"


def test_finished_record_is_not_live(tmp_path):
    directory = record(tmp_path, "llm/t/1/implement/0/0")
    (directory / "end.json").write_text("{}")
    assert live_call(tmp_path, "t", "implement", "") == ""


def test_latest_matching_record(tmp_path):
    record(tmp_path, "llm/t/1/implement/0/0", model="older", start="2026-01-01T00:00:01+00:00")
    record(tmp_path, "llm/t/1/implement/0/1", model="newer", start="2026-01-01T00:00:02+00:00")
    record(tmp_path, "llm/other/1/implement/0/0", model="wrong-stem", start="2026-01-01T00:00:03+00:00")
    record(tmp_path, "llm/t/1/review/0/0", model="wrong-surface", surface="review", start="2026-01-01T00:00:04+00:00")
    assert live_call(tmp_path, "t", "implement", "") == "claude newer"


def test_stage_start_filters_old_calls(tmp_path):
    record(tmp_path, "llm/t/1/implement/0/0")
    assert live_call(tmp_path, "t", "implement", "2026-01-01T00:00:02+00:00") == ""
    assert live_call(tmp_path, "t", "implement", "") == "claude opus"


def test_bad_record_is_skipped(tmp_path):
    record(tmp_path, "llm/t/1/implement/0/0")
    broken = record(tmp_path, "llm/t/1/implement/0/1")
    (broken / "start.json").write_text('{"clock":')
    assert live_call(tmp_path, "t", "implement", "") == "claude opus"


def test_missing_evidence(tmp_path):
    assert live_call(tmp_path / "evidence", "t", "implement", "") == ""
