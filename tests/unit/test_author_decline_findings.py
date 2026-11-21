"""Author declines preserve findings across driver calls."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Author declines preserve findings across driver calls.
# relates: [clutch/artifacts.py, clutch/author.py, clutch/stages.py, tests/fakes.py, tests/unit/test_retro_recurrence.py]
# owner: engine
# verified: 93253297
# hash: b4489258f9b311a17ebbe868ca0bb891c1ed983b40167dfda9aa831483363891

from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import author
from clutch.artifacts import Finding
from clutch.stages import findings_text
from tests.fakes import FakeJournal
from tests.unit.test_retro_recurrence import message


@pytest.mark.asyncio
async def test_decline_collects_distinct_findings_in_order(monkeypatch, tmp_path):
    first = Finding(code="stem", message="already named", paved_road="choose another")
    repeated = Finding(code="stem", message="already named", paved_road="different advice")
    last = Finding(code="row", message="wrong stem", paved_road="use the row stem")
    evidence = []

    async def ls_files(repo):
        return ["clutch/specs/review.md"]

    async def open_tickets(checkout):
        return "none"

    async def decline(checkout, driver, box, item, text):
        evidence.append(text)

    async def run(stage, *args, **kwargs):
        stage.render(None, [])
        stage.render(None, [first])
        return SimpleNamespace(outcome="declined", artifact=None, findings=[repeated, last])

    monkeypatch.setattr(Path, "read_text", lambda self: "spec")
    monkeypatch.setattr(author, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(effort="medium")))
    monkeypatch.setattr(author, "render", lambda spec, inputs: "prompt")
    monkeypatch.setattr(author, "list_open_tickets", open_tickets)
    monkeypatch.setattr(author, "failure_declined", decline)
    checkout = SimpleNamespace(repo=tmp_path, git=SimpleNamespace(ls_files=ls_files), journal=FakeJournal(), config=SimpleNamespace(state_dir=tmp_path, routing_default_tier="medium"))
    item = message().model_copy(update={"verdict": SimpleNamespace(rationale="repair")})
    await author.author(checkout, SimpleNamespace(run=run), SimpleNamespace(root=tmp_path), item, 1)
    assert evidence[0] == findings_text([first, last])
    assert evidence[0].count("- stem: already named") == 1

    async def single(stage, *args, **kwargs):
        stage.render(None, [])
        return SimpleNamespace(outcome="declined", artifact=None, findings=[last])

    await author.author(checkout, SimpleNamespace(run=single), SimpleNamespace(root=tmp_path), item, 1)
    assert evidence[1] == findings_text([last])
