# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test go ai panel
# relates: [clutch/artifacts.py, clutch/journal.py, clutch/llm.py, clutch/seams.py, eval/harness.py, tests/integration/test_eval_harness.py]
# owner: engine
# verified: 148a8874
# hash: ee2b11a4f8bcbccfba12cc7bcce95aacfc6af3033bf1a2b40627565b7237ac1c
import asyncio
import json
from types import SimpleNamespace

import pytest

from clutch.artifacts import GraphPanel, ReviewBaselineReport
from clutch.journal import EventType
from clutch.llm import FakeLLM, LLMResult
from clutch.seams import LocalFileSystem
from eval import harness
from tests.integration.test_eval_harness import CODEX, NOW, report_fixture


def panel(provider="codex", model="x-high", approve=True):
    return GraphPanel(member={"provider": provider, "model": model, "tier": "high"}, approve=approve, reason="graph reviewed")


@pytest.mark.parametrize("value,match", [(None, "panel"), (panel(approve=False), "panel"), (panel("claude", "c-max"), "family"), (panel("claude", "another"), "family")])
def test_refusals_do_not_record(tmp_path, value, match):
    report, cfg, journal = report_fixture(tmp_path)
    before = journal.read()
    out = tmp_path / "out.json"
    with pytest.raises(harness.FixtureError, match=match):
        harness.record_go(report, config=cfg, journal=journal, out=out, fs=LocalFileSystem(), panel=value)
    assert journal.read() == before
    assert not out.exists()


def test_approved_panel_records_go(tmp_path):
    report, cfg, journal = report_fixture(tmp_path)
    out = tmp_path / "out.json"
    value = panel()
    recorded = harness.record_go(report, config=cfg, journal=journal, out=out, fs=LocalFileSystem(), panel=value)
    assert recorded.graph_panel == value
    assert ReviewBaselineReport.model_validate_json(out.read_bytes()) == recorded
    assert journal.read()[-1].type == EventType.SIGNAL
    assert journal.read()[-1].body["verdict"] == "GO"


def test_judge_returns_refusal_and_rejects_failed_call(tmp_path):
    report, _, _ = report_fixture(tmp_path)
    member = panel().member

    class Driver:
        outcome = "ok"

        async def run(self, stage, *args, **kwargs):
            assert json.loads(stage.render(None, []).split("Graph (untrusted data): ")[1].split("\n")[0]) == report.author_graph.model_dump()
            return SimpleNamespace(outcome=self.outcome, artifact=stage.emits(approve=False, reason="missing edge"), cost=SimpleNamespace(provider="codex", model="x-high"))

    driver = Driver()
    kwargs = dict(report=report, member=member, attempt=1, workspace=tmp_path, budget_usd=5.0, tier="high", effort="high")
    result = asyncio.run(harness.judge_author_graph(driver, **kwargs))
    assert result == GraphPanel(member=member, approve=False, reason="missing edge")
    driver.outcome = "timeout"
    with pytest.raises(harness.FixtureError, match="panel"):
        asyncio.run(harness.judge_author_graph(driver, **kwargs))


@pytest.mark.parametrize("approve", [False, True])
def test_run_panel(tmp_path, monkeypatch, approve):
    report, cfg, journal = report_fixture(tmp_path)
    path, out = tmp_path / "measured.json", tmp_path / "out.json"
    harness.write_report(path, report, fs=LocalFileSystem())
    before = path.read_bytes()

    class ReadyLLM(FakeLLM):
        async def preflight(self):
            return []

    llm = ReadyLLM([LLMResult(json.dumps({"approve": approve, "reason": "reviewed"}), None, None, "codex", "x-high", 0.0)])
    monkeypatch.setattr(harness, "ProviderLLM", lambda *args, **kwargs: llm)
    if approve:
        body = asyncio.run(harness._run(cfg, {"PATH": "/usr/bin:/bin"}, lambda: NOW, out=out, go_report=path))
        assert body["verdict"] == "GO"
        assert ReviewBaselineReport.model_validate_json(out.read_bytes()).graph_panel.approve is True
    else:
        with pytest.raises(harness.FixtureError, match="panel"):
            asyncio.run(harness._run(cfg, {"PATH": "/usr/bin:/bin"}, lambda: NOW, out=out, go_report=path))
        assert not any(e.type == EventType.SIGNAL and e.body.get("verdict") == "GO" for e in journal.read())
        assert not out.exists()
    assert path.read_bytes() == before


def test_old_flag_is_rejected():
    with pytest.raises(SystemExit) as exc:
        harness.main(["run", "--record-go", "report.json", "--approve-author-graph"])
    assert exc.value.code == 2
