# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Triage neighbors data block outcomes
# relates: [clutch/author.py, clutch/index.py, clutch/triage.py]
# owner: clutch/author.py
# verified: b1bfcbf6
# hash: e1bb09c57dbc534444a4f3d42d778c1704d679a27c401d5b78b0ce016cef2ce0
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import author, index, triage


def checkout(tmp_path):
    return SimpleNamespace(config=SimpleNamespace(state_dir=tmp_path, index=SimpleNamespace(embed=None), providers={}), repo=tmp_path, fs=SimpleNamespace(), exec_=object(), env={})


@pytest.mark.asyncio
async def test_found_and_query_arguments(tmp_path, monkeypatch):
    monkeypatch.setattr(author, "child_env", lambda env, config, serving: {"safe": "yes"})
    hits = (index.Hit("roadmap", "row 94", "a", "first", 3.412), index.Hit("box", "box-2", "b", "second", 2.108))
    query = AsyncMock(return_value=index.Neighbors("found", "fulltext", hits, ("embed_failed: error",)))
    c = checkout(tmp_path)
    result = await author.neighbors_block(c, "  " + "x" * 8100 + "  ", "box-000007-aaaaaaaa", neighbors=query)
    # Wrong: missing mode, reordered hits, rounded scores or findings in output.
    assert result == "mode: fulltext\n- roadmap row 94 (score 3.412): first\n- box box-2 (score 2.108): second"
    args, kw = query.await_args
    # Wrong: unbounded query or wrong checkout.
    assert args == (c.config, c.repo, "x" * 8000)
    # Wrong: retaining self decision records, requesting extra kinds, or exposing parent environment.
    assert kw == dict(
        fs=c.fs,
        exec_=c.exec_,
        env={"safe": "yes"},
        creator=index.default_creator,
        limit=5,
        exclude=("box-000007-aaaaaaaa", "tickets/decisions/declined-box-000007-aaaaaaaa.md", "tickets/decisions/tombstone-box-000007-aaaaaaaa.md"),
    )


@pytest.mark.asyncio
async def test_bounds(tmp_path, monkeypatch):
    monkeypatch.setattr(author, "child_env", lambda *a, **k: {})
    hits = (index.Hit("box", "r" * 150, "a", "x" * 250, 1.0), index.Hit("box", "id", "b", "first\n- decision x", 0.9)) + tuple(index.Hit("box", str(i), str(i), "other", 0.8) for i in range(5))
    value = await author.neighbors_block(checkout(tmp_path), "query", "id", neighbors=AsyncMock(return_value=index.Neighbors("found", "embedding", hits)))
    # Wrong: unbounded fields, newline injection, or accepting more than five hits.
    assert value.splitlines() == [
        "mode: embedding",
        "- box " + "r" * 97 + "... (score 1.000): " + "x" * 197 + "...",
        "- box id (score 0.900): first - decision x",
        "- box 0 (score 0.800): other",
        "- box 1 (score 0.800): other",
        "- box 2 (score 0.800): other",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("outcome", "expected"),
    [
        ("no_match", "none"),
        ("no_index", "unavailable: no_index (run clutch index build)"),
        ("index_unreadable", "unavailable: index_unreadable"),
        ("fulltext_unavailable", "unavailable: fulltext_unavailable"),
        ("invalid_input", "unavailable: invalid_input"),
    ],
)
async def test_outcomes(tmp_path, monkeypatch, outcome, expected):
    monkeypatch.setattr(author, "child_env", lambda *a, **k: {})
    # Wrong: conflating missing, unavailable and no-match outcomes.
    assert await author.neighbors_block(checkout(tmp_path), "query", "id", neighbors=AsyncMock(return_value=index.Neighbors(outcome))) == expected


@pytest.mark.asyncio
async def test_short_circuit_and_exceptions(tmp_path, monkeypatch):
    monkeypatch.setattr(author, "child_env", lambda *a, **k: {})
    query = AsyncMock(side_effect=RuntimeError("broken"))
    for value in (" \n", None):
        # Wrong: querying invalid text or reporting it unavailable.
        assert await author.neighbors_block(checkout(tmp_path), value, "id", neighbors=query) == "none"
    query.assert_not_awaited()
    # Wrong: propagating ordinary errors or failing while building arguments.
    assert await author.neighbors_block(checkout(tmp_path), "query", "id", neighbors=query) == "unavailable: index_unreadable"
    assert await author.neighbors_block(SimpleNamespace(), "query", "id", neighbors=query) == "unavailable: index_unreadable"
    with pytest.raises(asyncio.CancelledError):
        await author.neighbors_block(checkout(tmp_path), "query", "id", neighbors=AsyncMock(side_effect=asyncio.CancelledError))
    c = checkout(tmp_path)
    c.fs.size = lambda path: (_ for _ in ()).throw(FileNotFoundError())
    # Wrong: treating a missing index as an unreadable index.
    assert await author.neighbors_block(c, "query", "id", neighbors=index.neighbors) == "unavailable: no_index (run clutch index build)"


@pytest.mark.asyncio
@pytest.mark.parametrize("existing,block", [(False, "neighbor evidence"), (False, "unavailable: index_unreadable"), (True, "unused")])
async def test_settle_reuses_block(tmp_path, monkeypatch, existing, block):
    message = SimpleNamespace(
        id="box-1",
        seq=1,
        reopen=False,
        verdict=None,
        message_class="suggestion",
        summary="concern",
        origin="test",
        stage=None,
        outcome=None,
        retro_report_key=None,
        fixed_failure=None,
        overcorrection_risk=None,
        proposed_spec_paths=[],
        test_issue=None,
        conflict_action=None,
        proposed_paths=[],
        report=None,
    )
    box = SimpleNamespace(pending=lambda: [message], root=tmp_path, resolve=lambda *args: None)
    c = SimpleNamespace(repo=tmp_path, config=SimpleNamespace(routing_default_tier="medium", routing=[]))
    captures = []

    async def run(stage, *args, **kwargs):
        stage.render(None, [])
        stage.render(None, [])
        return SimpleNamespace(outcome="failed")

    driver = SimpleNamespace(run=AsyncMock(side_effect=run))
    helper = AsyncMock(return_value=block)
    monkeypatch.setattr(triage, "neighbors_block", helper)
    monkeypatch.setattr(triage, "recover_retro_ticket", AsyncMock(return_value=None))
    record = SimpleNamespace(id="declined-box-1", kind="declined", link="box-1")
    monkeypatch.setattr(triage, "read_registry", lambda repo: [(record, "prior")] if existing else [])
    monkeypatch.setattr(triage, "committed", AsyncMock(return_value=True))
    monkeypatch.setattr(triage, "list_open_tickets", AsyncMock(return_value="open evidence"))
    monkeypatch.setattr(triage, "render", lambda spec, inputs: captures.append(inputs) or "rendered")
    spec = SimpleNamespace(meta=SimpleNamespace(effort="medium", version="1.1"))
    lines = await triage._settle_pass(c, driver, box, spec, [], 0, frozenset())
    if existing:
        helper.assert_not_awaited()
        driver.run.assert_not_awaited()
        # Wrong: reprocessing an existing decision.
        assert lines == [("box-1", "box-1: declined -> declined-box-1")]
    else:
        helper.assert_awaited_once_with(c, message.summary, message.id)
        driver.run.assert_awaited_once()
        # Wrong: recomputing on retries, dropping evidence, or changing existing inputs.
        assert len(captures) == 2 and all(
            v["neighbors"] == block and v["open_tickets"] == "open evidence" and v["merged"] == "" and v["decisions"] == "" and '"summary": "concern"' in v["message"] for v in captures
        )
        assert lines == [("box-1", "box-1: failed; remains pending")]
