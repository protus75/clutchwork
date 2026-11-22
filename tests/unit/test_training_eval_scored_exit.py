"""The eval command refuses reports with no parsed verdicts."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit test that `clutch training eval` exits 2 with a recovery message when no held-out review record gets a parsed verdict, exits 0 otherwise, and always prints the agreement report
# relates: [clutch/__main__.py, clutch/config.py, clutch/evidence/store.py, clutch/llm.py, clutch/training.py, tests/git_fake.py]
# owner: engine
# verified: 9aa0931a
# hash: 0b4b3bb1e47c909af4efbd42873327912202a1990b80f89f369901c9d0f0ada5

import json
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import pytest

from clutch import __main__ as entry
from clutch import training
from clutch.config import TrainingData
from clutch.llm import FakeLLM
from tests.git_fake import GitFake


@pytest.mark.parametrize(
    "records,reply,code,report",
    [
        ([], None, 2, "total: 0, agree: 0, disagree: 0, unparsed: 0, agreement: 0.00%"),
        (["negative"], "invalid", 2, "total: 1, agree: 0, disagree: 0, unparsed: 1, agreement: 0.00%"),
        (["negative"], '{"verdict":"snag"}', 0, "total: 1, agree: 1, disagree: 0, unparsed: 0, agreement: 100.00%"),
        (["negative"], '{"verdict":"approve"}', 0, "total: 1, agree: 0, disagree: 1, unparsed: 0, agreement: 0.00%"),
    ],
)
def test_scored_exit(tmp_path, monkeypatch, capsys, records, reply, code, report):
    from clutch.evidence import store as evidence

    config = NS(state_dir=tmp_path / "state", training_data=TrainingData(enabled=True), providers=[], release=NS(pypi_token="TOKEN"), drain=NS(max_ticket_minutes=10), circuit_breaker=NS())
    monkeypatch.setattr(entry, "load_config", lambda *args, **kwargs: config)
    monkeypatch.setattr(entry, "Git", lambda *args, **kwargs: GitFake())
    monkeypatch.setattr(evidence, "EvidenceStore", lambda *args: object())
    session = NS(close=AsyncMock())
    monkeypatch.setattr(entry, "build_control", lambda checkout: NS(providers=session))
    llm = FakeLLM([reply] if reply else [])
    llm.preflight = AsyncMock(return_value=[])
    monkeypatch.setattr(entry, "ProviderLLM", lambda *args, **kwargs: llm)

    async def render(*args, **kwargs):
        lines = [json.dumps({"label": label, "messages": [{"content": "held-out prompt"}]}) for label in records]
        return {"review.jsonl": "\n".join(lines)}, {}

    monkeypatch.setattr(training, "render", render)
    holdout = tmp_path / "holdout.txt"
    holdout.write_text("held-stem\n")
    result = entry.main(["training", "eval", "--route", "medium/review", "--holdout", str(holdout)], cwd=tmp_path, env={})
    output = capsys.readouterr()
    # Rejects accepting an empty or unparsed evaluation, or refusing a parsed disagreement.
    assert result == code
    # Rejects dropping or altering the report, including on refusal.
    assert output.out == report + "\n"
    # Rejects a silent refusal, missing recovery instructions, or a diagnostic on success.
    assert output.err == ("clutch training: no held-out review record was scored -- run training export with --kinds review and --holdout PCT, then pass its holdout.txt\n" if code == 2 else "")
