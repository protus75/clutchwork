"""GO-grade entry contract, closed reports and operator-only verdict production."""

import asyncio
import json
from dataclasses import asdict

import pytest
from pydantic import ValidationError

from clutch.artifacts import GraphPanel, ReviewBaselineReport
from clutch.journal import EventType
from clutch.llm import FakeLLM, LLMResult
from clutch.seams import LocalFileSystem
from eval import harness
from tests.integration.test_eval_harness import CODEX, NOW, corpus_results, report_fixture


def test_record_go_requires_complete_floors_identity_and_operator_judgment(tmp_path, monkeypatch):
    report, cfg, journal = report_fixture(tmp_path)
    out = tmp_path / "operator-report.json"
    fs = LocalFileSystem()

    panel = GraphPanel(member=CODEX, approve=True, reason="sound graph")

    def record(candidate=report, config=cfg):
        return harness.record_go(candidate, config=config, journal=journal, out=out, fs=fs, panel=panel)

    assert report.scores.catch_rate == 0.85 and report.scores.clean_false_snag == 0.15
    candidates = [
        report_fixture(tmp_path, corpus_results(49, 20, 49, 0))[0],
        report_fixture(tmp_path, corpus_results(60, 14, 60, 0))[0],
        report_fixture(tmp_path, graph=False)[0],
        report_fixture(tmp_path, corpus_results(catches=50))[0],
        report_fixture(tmp_path, corpus_results(false_snags=4))[0],
    ]
    for candidate in candidates:
        before = journal.read()
        with pytest.raises(harness.FixtureError):
            record(candidate)
        assert journal.read() == before and not out.exists()
    for surface in ("review", "author"):
        raw = report.model_dump()
        raw["verdict_signal"]["body"]["identity"][surface]["rows"]["low"]["model"] = "drifted"
        drift = ReviewBaselineReport.model_validate(raw)
        before = journal.read()
        with pytest.raises(harness.FixtureError, match="drifted"):
            record(drift)
        assert journal.read() == before and not out.exists()
    raw = report.model_dump()
    raw["verdict_signal"]["body"]["identity"]["author"]["spec_major"] += 1
    before = journal.read()
    with pytest.raises(harness.FixtureError, match="drifted"):
        record(ReviewBaselineReport.model_validate(raw))
    # Revalidation defeats unvalidated model_copy updates before any append/write.
    with pytest.raises(ValidationError):
        record(report.model_copy(update={"complete": False}))
    assert journal.read() == before and not out.exists()
    measured = tmp_path / "measured.json"
    harness.write_report(measured, report, fs=fs)
    before = measured.read_bytes()
    fixtures = {p: p.read_bytes() for p in harness.FIXTURES.glob("*/*") if p.is_file()}

    class ReadyLLM(FakeLLM):
        async def preflight(self):
            return []

    llm = ReadyLLM([LLMResult(json.dumps({"approve": False, "reason": "bad graph"}), None, None, "codex", "x-high", 0.0)])
    monkeypatch.setattr(harness, "ProviderLLM", lambda *args, **kwargs: llm)
    with pytest.raises(harness.FixtureError, match="panel"):
        asyncio.run(harness._run(cfg, {"PATH": "/usr/bin:/bin"}, lambda: NOW, out=out, go_report=measured))
    assert not any(e.type == EventType.SIGNAL and e.body.get("verdict") == "GO" for e in journal.read())
    assert not out.exists() and measured.read_bytes() == before
    assert fixtures == {p: p.read_bytes() for p in fixtures}
    recorded = record()
    assert recorded.verdict_signal.body.verdict == "GO"
    assert recorded.verdict_signal.model_dump() == asdict(journal.read()[-1])
    assert recorded.verdict_signal.body.identity.model_dump() == harness.baseline_identity(cfg)
    assert ReviewBaselineReport.model_validate_json(out.read_bytes()) == recorded


def test_review_baseline_report_closed_schema(tmp_path):
    report, _, _ = report_fixture(tmp_path)
    assert set(report.model_dump()) == {"schema_version", "complete", "cap_usd", "spent_usd", "results", "scores", "author_graph", "graph_panel", "verdict_signal"}
    mutations = [
        lambda r: r.update(extra=True),
        lambda r: r.update(schema_version=2),
        lambda r: r.update(schema_version=True),
        lambda r: r.update(spent_usd=float("inf")),
        lambda r: r.update(spent_usd=-1.0),
        lambda r: r["results"].append(r["results"][0]),
        lambda r: r["results"][0].update(outcome="unknown"),
        lambda r: r["results"][0].update(verdict="lgtm"),
        lambda r: r["results"][0].update(verdict=None),
        lambda r: r["results"][0]["expected"].update(extra=True),
        lambda r: r["scores"].update(planted=1),
        lambda r: r["scores"].update(extra=True),
        lambda r: r["verdict_signal"].update(type="effect_completion"),
        lambda r: r["verdict_signal"].update(v=True),
        lambda r: r["verdict_signal"].update(ts="yesterday"),
        lambda r: r["verdict_signal"]["body"].update(extra=True),
        lambda r: r["verdict_signal"]["body"]["scores"].update(catch_rate=1.0),
        lambda r: r["verdict_signal"]["body"]["identity"].update(extra=True),
        lambda r: r["verdict_signal"]["body"]["identity"]["review"]["rows"].pop("low"),
        lambda r: r["verdict_signal"]["body"]["fixture_authors"][0].update(provider="invented"),
        lambda r: r["author_graph"]["tickets"][0].update(extra=True),
    ]
    for mutate in mutations:
        raw = report.model_dump()
        mutate(raw)
        with pytest.raises(ValidationError):
            ReviewBaselineReport.model_validate(raw)
    partial, _, _ = report_fixture(tmp_path, corpus_results(18, 4, 18, 0))
    raw = partial.model_dump()
    raw["verdict_signal"]["body"]["verdict"] = "GO"
    with pytest.raises(ValidationError, match="GO"):
        ReviewBaselineReport.model_validate(raw)
