import asyncio
import json
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import policy, visual
from clutch.journal import Journal
from eval import visual_harness as harness


def case(tmp_path, label="accept"):
    data = harness.CaseData(
        mode="command",
        visual_criteria=["shape", "color"],
        inputs=[],
        candidate="image.png",
        panel={"provider": "panel", "model": "p"},
        label={"verdict": label, "rows": {"shape": "pass", "color": "fail"}},
    )
    return harness.Case(tmp_path, data)


def reply(verdict="accept", rows=None):
    return visual.Reply(verdict=verdict, reason="observed", rows=rows if rows is not None else [visual.Row(id="shape", verdict="pass", observation="observed")])


def test_threshold_count_and_omitted_row(tmp_path):
    item = case(tmp_path)
    results = [(item, reply())] * 17 + [(item, reply("reject"))] * 3
    result = harness.agreement(results)
    assert result == {"case_count": 20, "overall": 0.85, "rows": {"shape": 1.0, "color": 0.0}, "verdict": "GO"}
    results[16] = (item, reply("reject"))
    assert harness.agreement(results)["overall"] == 0.8
    assert harness.agreement(results)["verdict"] == "NO_GO"
    assert harness.agreement([(item, reply())] * 19)["verdict"] == "NO_GO"
    assert harness.agreement([(item, reply())] * 20)["verdict"] == "GO"


def test_loader_refuses_invalid_cases(tmp_path):
    first = tmp_path / "a"
    first.mkdir()
    (first / "image.png").write_bytes(b"image")
    data = case(first).data.model_dump(mode="json")
    (first / "case.json").write_text(json.dumps(data))
    assert len(harness.load_cases(tmp_path, "judge")) == 1
    for change in ({"candidate": "missing.png"}, {"label": {"verdict": "maybe", "rows": data["label"]["rows"]}}, {"panel": {"provider": "judge", "model": "different"}}):
        second = tmp_path / "b"
        second.mkdir(exist_ok=True)
        (second / "image.png").write_bytes(b"image")
        (second / "case.json").write_text(json.dumps({**data, **change}))
        with pytest.raises(ValueError, match="case b"):
            harness.load_cases(tmp_path, "judge")


def test_identity_tracks_model_and_major(tmp_path, monkeypatch):
    spec = tmp_path / "review_visual.md"
    spec.write_text(
        '---\nllm_surface: review_visual\ntier: medium\neffort: medium\nversion: "1.0"\n---\n## Role\nrole\n## Task\ntask\n## Inputs\ninputs\n## Output format\noutput\n## On-failure\nfailure\n'
    )
    monkeypatch.setattr(policy, "resolve", lambda config, tier, surface, kind: SimpleNamespace(provider=SimpleNamespace(name="judge"), model=config))
    original = policy.visual_identity("model-a", tmp_path)
    assert original == policy.visual_identity("model-a", tmp_path)
    assert original != policy.visual_identity("model-b", tmp_path)
    spec.write_text(spec.read_text().replace('"1.0"', '"2.0"'))
    assert original != policy.visual_identity("model-a", tmp_path)


def test_run_writes_real_signal_and_report(tmp_path, monkeypatch):
    spec = tmp_path / "review_visual.md"
    spec.write_text(
        '---\nllm_surface: review_visual\ntier: medium\neffort: medium\nversion: "1.0"\n---\n## Role\nrole\n## Task\ntask\n## Inputs\ninputs\n## Output format\noutput\n## On-failure\nfailure\n'
    )
    identity = {"review_visual": {"rows": {"medium": {"provider": "judge", "model": "model"}}, "spec_major": 1}}
    monkeypatch.setattr(harness, "visual_identity", lambda *_: identity)
    monkeypatch.setattr(harness, "_judge", AsyncMock(return_value=reply()))
    journal = Journal(tmp_path / "state", lambda: datetime(2026, 1, 1, tzinfo=UTC))
    report_path = tmp_path / "eval" / "visual_report.json"
    config = SimpleNamespace(graphics=SimpleNamespace(judge_samples=1))
    report = asyncio.run(harness.run_baseline(config=config, driver=None, journal=journal, cases=[case(tmp_path)] * 20, report_path=report_path, specs_dir=tmp_path))
    assert report["verdict"] == "GO"
    assert json.loads(report_path.read_text()) == report
    assert [event.body for event in journal.read()] == [{"signal": "visual_baseline", "verdict": "GO", "identity": identity, "overall": 1.0, "case_count": 20}]
