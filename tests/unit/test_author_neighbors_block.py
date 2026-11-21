# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Author neighbors data block wiring and outcomes
# relates: [clutch/author.py, clutch/box.py, clutch/index.py, tests/fakes.py, tests/unit/test_retro_recurrence.py]
# owner: engine
# verified: bce07f02
# hash: 8ad03d724a4c3bbf72ce49da1725dfb2e56b4b558e805398a61d502be9aa78dd
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import author, index
from clutch.box import RoadmapRow
from tests.fakes import FakeJournal
from tests.unit.test_retro_recurrence import message

HITS = (index.Hit("roadmap", "row 3", "a", "first", 3.412), index.Hit("box", "box-2", "b", "second", 2.108))
FOUND = index.Neighbors("found", "fulltext", HITS, ("embed_failed: error",))
BLOCK = "mode: fulltext\n- roadmap row 3 (score 3.412): first\n- box box-2 (score 2.108): second"
REAL_HELPER = author.neighbors_block


async def drive(tmp_path, monkeypatch, query, *, roadmap=False, missing_fs=False, blank=False):
    captures = []

    async def ls_files(repo):
        return ["docs/plan.md"]

    async def run(stage, *args, **kwargs):
        stage.render(None, [])
        stage.render(None, [])
        raise StopAsyncIteration

    async def wrapper(*args, **kwargs):
        return await REAL_HELPER(*args, **kwargs, neighbors=query)

    monkeypatch.setattr(Path, "read_text", lambda self: "spec")
    monkeypatch.setattr(author, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(effort="medium")))
    monkeypatch.setattr(author, "render", lambda spec, values: captures.append(values) or "rendered")
    monkeypatch.setattr(author, "list_open_tickets", AsyncMock(return_value="open evidence"))
    monkeypatch.setattr(author, "template", lambda kind: "skeleton")
    monkeypatch.setattr(author, "context_block", lambda *args: "context evidence")
    monkeypatch.setattr(author, "child_env", lambda *args, **kwargs: {})
    monkeypatch.setattr(author, "neighbors_block", wrapper)
    row = RoadmapRow(number=94, release="0.5", stem="row-stem", owner="engine", kind="feature", priority="P2", content="Quarantine a flaky test", plan="docs/plan.md")
    if blank:
        row = SimpleNamespace(number=94, stem="row-stem", content=" ", plan="docs/plan.md", model_dump_json=lambda: "{}")
    item = message().model_copy(
        update={
            "message_class": "roadmap_row" if roadmap else "bug_report",
            "roadmap_row": row if roadmap else None,
            "summary": "Fix flaky drain test",
            "verdict": SimpleNamespace(rationale="different rationale"),
            "bug_origin": "player",
            "has_repro": True,
        }
    )
    checkout = SimpleNamespace(
        repo=tmp_path, git=SimpleNamespace(ls_files=ls_files), journal=FakeJournal(), config=SimpleNamespace(state_dir=tmp_path, routing_default_tier="medium"), exec_=object(), env={}
    )
    if not missing_fs:
        checkout.fs = object()
    driver = SimpleNamespace(run=AsyncMock(side_effect=run))
    with pytest.raises(StopAsyncIteration):
        await author.author(checkout, driver, SimpleNamespace(root=tmp_path), item, 1)
    driver.run.assert_awaited_once()
    return captures, item


@pytest.mark.asyncio
@pytest.mark.parametrize("roadmap", [False, True])
async def test_author_query_and_reprompt(tmp_path, monkeypatch, roadmap):
    query = AsyncMock(return_value=FOUND)
    captures, item = await drive(tmp_path, monkeypatch, query, roadmap=roadmap)
    # Wrong: search rationale or recompute the block on a re-prompt.
    query.assert_awaited_once()
    args, kwargs = query.await_args
    assert args[2] == ("Quarantine a flaky test" if roadmap else "Fix flaky drain test")
    # Wrong: include a message's own decision or roadmap row.
    assert kwargs["exclude"] == (item.id, f"tickets/decisions/declined-{item.id}.md", f"tickets/decisions/tombstone-{item.id}.md", *(("row 94",) if roadmap else ()))
    # Wrong: omit mode or change the evidence between renders.
    assert len(captures) == 2 and captures[0] == captures[1]
    assert captures[0]["neighbors"] == BLOCK
    assert captures[0]["context_suggest"] == "context evidence" and captures[0]["open_tickets"] == "open evidence"


@pytest.mark.asyncio
async def test_helper_default_and_extra_exclusions(tmp_path, monkeypatch):
    monkeypatch.setattr(author, "child_env", lambda *a, **k: {})
    checkout = SimpleNamespace(config=object(), repo=tmp_path, fs=object(), exec_=object(), env={})
    query = AsyncMock(return_value=FOUND)
    for extra in [(), ("row 94",)]:
        kwargs = {"exclude_refs": extra} if extra else {}
        # Wrong: alter Triage's default tuple or drop the added row.
        assert await REAL_HELPER(checkout, "query", "id", neighbors=query, **kwargs) == BLOCK
        assert query.await_args.kwargs["exclude"] == ("id", "tickets/decisions/declined-id.md", "tickets/decisions/tombstone-id.md", *extra)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("result", "expected"),
    [
        (index.Neighbors("no_match"), "none"),
        (index.Neighbors("no_index"), "unavailable: no_index (run clutch index build)"),
        (index.Neighbors("index_unreadable"), "unavailable: index_unreadable"),
        (index.Neighbors("fulltext_unavailable"), "unavailable: fulltext_unavailable"),
        (index.Neighbors("invalid_input"), "unavailable: invalid_input"),
        (FOUND, BLOCK),
        (RuntimeError("broken"), "unavailable: index_unreadable"),
    ],
)
async def test_outcomes_keep_other_inputs(tmp_path, monkeypatch, result, expected):
    baseline, _ = await drive(tmp_path, monkeypatch, AsyncMock(return_value=FOUND))
    query = AsyncMock(side_effect=result) if isinstance(result, Exception) else AsyncMock(return_value=result)
    captures, _ = await drive(tmp_path, monkeypatch, query)
    # Wrong: index outcome changes the stage's other inputs or leaks findings.
    assert [{k: v for k, v in values.items() if k != "neighbors"} for values in captures] == [{k: v for k, v in values.items() if k != "neighbors"} for values in baseline]
    assert [v["neighbors"] for v in captures] == [expected, expected]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["missing_fs", "blank"])
async def test_short_circuit(tmp_path, monkeypatch, case):
    query = AsyncMock(return_value=FOUND)
    captures, _ = await drive(tmp_path, monkeypatch, query, roadmap=case == "blank", missing_fs=case == "missing_fs", blank=case == "blank")
    # Wrong: query invalid input or raise on missing checkout seams.
    assert captures[0]["neighbors"] == ("none" if case == "blank" else "unavailable: index_unreadable")
    query.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_propagates(tmp_path, monkeypatch):
    # Wrong: swallow cancellation as an index failure.
    with pytest.raises(asyncio.CancelledError):
        await drive(tmp_path, monkeypatch, AsyncMock(side_effect=asyncio.CancelledError))
