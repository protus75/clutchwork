"""Review replay and its read-only handler contract, with scripted model calls."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests training eval: scoring review replay against labels, counting unparsed replies, selecting stems, and checking the CLI handler's gates and read-only contract.
# relates: [clutch/__main__.py, clutch/config.py, clutch/evidence/store.py, clutch/journal.py, clutch/llm.py, clutch/redact.py, clutch/timers.py]
# owner: engine
# verified: cb71e4f8
# hash: fe6938f4e308395a2b5e80522328623a446f4271fe9b2dd7b077409b7dfb22e8

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import pytest

from clutch import __main__ as entry
from clutch import training
from clutch.config import TrainingData
from clutch.journal import Journal
from clutch.llm import FakeLLM, LLMRequest
from clutch.redact import Redactor
from clutch.timers import Timers
from tests.fakes import FakeClock
from tests.git_fake import GitFake


class Store:
    def attempts(self):
        return [(stem, 1, 1) for stem in ("a", "b")]

    def call_keys(self, prefix):
        return [f"llm/{stem}/1/review/1/1" for stem in ("a", "b")]

    def read_attempt(self, stem, run, attempt):
        return NS(call_keys=[f"llm/{stem}/1/review/1/1"], outcome="snag", findings=[{"code": "logic"}])

    def read_record(self, key, kind):
        return NS(
            run_seq="1",
            attempt=1,
            call=1,
            surface="review",
            clock=NS(wall_start="2026-11-20T00:00:00Z"),
            prompt=NS(blob=key),
            engine=NS(version="v", spec="review", spec_version="1"),
        )

    def get_blob(self, key):
        return f"review prompt for {key.split('/')[1]}".encode()


def record(label, prompt="held-out prompt"):
    return {"label": label, "messages": [{"role": "user", "content": prompt}, {"role": "assistant", "content": "recorded answer, never replayed"}]}


def test_score_and_requests():
    llm = FakeLLM(['{"verdict":"snag"}', '{"verdict":"approve"}', '{"verdict":"approve"}'])
    records = [record("negative", "first"), record("neutral", "second"), record("negative", "third")]
    counts = asyncio.run(training.evaluate(records, llm, "high"))
    # Rules out counting every parsed response as agreement, reversing labels, or excluding disagreements from the denominator.
    assert counts == dict(total=3, agree=2, disagree=1, unparsed=0, agreement=2 / 3)
    # Rules out replaying the target answer, wrong routing/effort, durable ticket association, or skipped/duplicate calls.
    assert llm.requests == [LLMRequest(surface="review", rendered=prompt, tier="high", effort="medium", ticket=None, worktree=None) for prompt in ("first", "second", "third")]


@pytest.mark.parametrize("reply", ["not json", '{"verdict":"maybe"}', "{}", "[]", '{"verdict":["snag"]}'])
def test_unparsed(reply):
    # Neutral labels catch the wrong implementation that treats every non-snag, including invalid replies, as agreement.
    counts = asyncio.run(training.evaluate([record("neutral")], FakeLLM([reply]), "medium"))
    assert counts == dict(total=1, agree=0, disagree=0, unparsed=1, agreement=0.0)


@pytest.mark.parametrize("reply,label", [('```json\n{"verdict":"snag"}\n```', "negative"), ('{"verdict":"rma"}', "neutral"), ('{"verdict":"snag"}', "neutral")])
def test_review_verdicts(reply, label):
    counts = asyncio.run(training.evaluate([record(label)], FakeLLM([reply]), "low"))
    agrees = label == "negative" or '"rma"' in reply
    # Rules out raw JSON parsing of fenced replies, excluding rma, or treating snag as agreement regardless of label.
    assert counts == dict(total=1, agree=int(agrees), disagree=int(not agrees), unparsed=0, agreement=float(agrees))


def test_render_selection():
    def render(**kwargs):
        files, _ = asyncio.run(training.render(Store(), GitFake(), Path("/repo"), Redactor({}), TrainingData(enabled=True), lambda path: b"", kinds=("review",), **kwargs))
        return [json.loads(line)["stem"] for line in files["review.jsonl"].splitlines()]

    # b has the same valid review manifest as a: only the requested stem selection can exclude it.
    assert (render(only={"a"}, holdout=100), render(), render(only=set())) == (["a"], ["a", "b"], [])


def test_empty_report():
    counts = asyncio.run(training.evaluate([], FakeLLM([]), "max"))
    # Rules out division by zero and omitted/misreported empty counts.
    assert training.report_eval(counts) == "total: 0, agree: 0, disagree: 0, unparsed: 0, agreement: 0.00%"


@pytest.mark.parametrize("enabled,holdout,problems,exit_code", [(False, b"a\n", [], 2), (True, None, [], 2), (True, b"\xff", [], 2), (True, b"a\n", ["probe failed"], 2), (True, b"a\n", [], 0)])
def test_handler(tmp_path, monkeypatch, capsys, enabled, holdout, problems, exit_code):
    from clutch.evidence import store as evidence

    clock = FakeClock()
    config = NS(
        state_dir=tmp_path / "state",
        training_data=TrainingData(enabled=enabled),
        providers=[],
        release=NS(pypi_token="TOKEN"),
        drain=NS(max_ticket_minutes=10),
        circuit_breaker=NS(),
    )
    monkeypatch.setattr(entry, "load_config", lambda *args, **kwargs: config)
    monkeypatch.setattr(entry, "Git", lambda *args, **kwargs: GitFake())
    monkeypatch.setattr(evidence, "EvidenceStore", lambda *args: Store())
    llm = FakeLLM(['{"verdict":"snag"}'])
    llm.preflight = AsyncMock(return_value=problems)
    sessions = []

    def model(*args, **kwargs):
        sessions.append(kwargs["session"])
        sessions[-1].close = AsyncMock(wraps=sessions[-1].close)
        return llm

    monkeypatch.setattr(entry, "ProviderLLM", model)
    path = tmp_path / "holdout.txt"
    if holdout is not None:
        path.write_bytes(holdout)
    # An expired timer makes accidental use of _preflighted_llm observably mutate the real journal.
    journal = Journal(config.state_dir, clock)
    Timers(journal=journal, clock=clock, sleep=asyncio.sleep).arm("eval-regression", clock(), ticket=None)
    blob = config.state_dir / "evidence" / "blobs" / "sentinel"
    blob.parent.mkdir(parents=True)
    blob.write_bytes(b"existing evidence\x00\xff")

    def snapshot():
        return {str(p.relative_to(config.state_dir)): p.read_bytes() for p in config.state_dir.rglob("*") if p.is_file()}

    before = snapshot()
    code = entry.main(["training", "eval", "--route", "medium/review", "--holdout", str(path)], cwd=tmp_path, env={}, clock=clock)
    output = capsys.readouterr()
    # Rules out accepting disabled/unreadable input or failing a valid eval.
    assert code == exit_code
    # Rules out calling the model before the enable/read/preflight gates, or evaluating b despite the holdout.
    assert llm.requests == ([LLMRequest(surface="review", rendered="review prompt for a", tier="medium", effort="medium", ticket=None, worktree=None)] if exit_code == 0 else [])
    # Rules out timer firing and any evidence/journal/log writes, including added or removed files.
    assert snapshot() == before
    if enabled and holdout == b"a\n":
        # Rules out skipping preflight or leaking the provider session on either exit path.
        assert (llm.preflight.await_count, sessions[0].close.await_count) == (1, 1)
    if exit_code == 0:
        # Rules out suppressing or duplicating the report, or emitting diagnostics on success.
        assert (output.out, output.err) == ("total: 1, agree: 1, disagree: 0, unparsed: 0, agreement: 100.00%\n", "")
