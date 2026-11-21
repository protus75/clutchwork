"""Identity canonicalization and review stability."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for requisition input identity: canonical hashing in the composer, which review inputs change the identity, and how review_with_identity attaches it to the verdict or drops it.
# relates: [clutch/config.py, clutch/requisition.py, tests/unit/test_route_kinds_filter.py]
# owner: engine
# verified: 9c24a9bd
# hash: 9c299816d725ba3d76a81eecf6a77fa6f5e80302bbff6a867bc4307e3cd727c3

import asyncio
import re
from types import SimpleNamespace
from unittest.mock import AsyncMock

from clutch import requisition
from tests.unit.test_route_kinds_filter import config


def test_composer():
    first = requisition.input_identity({"b": [b"a", b"b"], "a": 4})
    assert re.fullmatch(r"[0-9a-f]{64}", first)
    assert first == requisition.input_identity({"a": 4, "b": [b"a", b"b"]})
    assert first != requisition.input_identity({"a": 4, "b": [b"b", b"a"]})


def test_gather_inputs(tmp_path, monkeypatch):
    repo = tmp_path
    (repo / "src").write_bytes(b"one")
    (repo / "ctx").write_bytes(b"context")
    (repo / "requisition_review.md").write_bytes(b"review")
    (repo / "implement.md").write_bytes(b"implement")
    (repo / "coverage").write_bytes(b"map")
    ticket = SimpleNamespace(context=("ctx",))
    sibling = ["siblings"]
    monkeypatch.setattr(requisition, "sibling_tickets_block", lambda *args: sibling[0])
    git = SimpleNamespace(ls_files=AsyncMock(return_value=["src", "tickets/other/ticket.md"]))
    cfg = config("  - {tier: medium, surface: requisition_review, candidates: [{provider: codex, model: a}]}\n")
    text = "---\nstate: confirmed\n---\nbody"

    def gather(value=text, tier="medium"):
        return asyncio.run(requisition.review_input_identity(repo, value, ticket, cfg, git, repo, repo / "coverage", [], tier=tier))

    base = gather()
    assert base is not None
    assert gather(text.replace("confirmed", "draft")) == base
    assert gather(text.replace("body", "other")) != base
    git.ls_files.return_value.append("tickets/other/extra")
    assert gather() == base
    for name in ("src", "ctx", "coverage", "requisition_review.md", "implement.md"):
        path = repo / name
        original = path.read_bytes()
        path.write_bytes(b"changed")
        assert gather() != base
        path.write_bytes(original)
    (repo / "src").unlink()
    assert gather() != base
    (repo / "src").write_bytes(b"one")
    sibling[0] = "another sibling"
    assert gather() != base
    sibling[0] = "siblings"
    cfg.routing[0].candidates[0].model = "different"
    assert gather() != base
    cfg.routing[0].candidates[0].model = "a"
    from clutch.config import Candidate, Panel, Route

    cfg.routing.append(Route(tier="high", surface="requisition_review", candidates=[Candidate(provider="codex", model="a")]))
    assert gather(tier="high") != base
    cfg.routing[0].panel = Panel(size=1, combine="findings-union")
    assert gather() != base
    cfg.routing[0].panel = None
    cfg.routing[0].candidates.append(Candidate(provider="claude", model="b"))
    assert gather() != base


def test_wrapper(monkeypatch):
    verdict = SimpleNamespace(mechanical=None, model_copy=lambda update: update["input_identity"])
    monkeypatch.setattr(requisition, "review_target", lambda *args: object())
    monkeypatch.setattr(requisition, "review_ticket", AsyncMock(return_value=verdict))
    gather = AsyncMock(side_effect=["a", "a", "a", "b", None, None])
    monkeypatch.setattr(requisition, "review_input_identity", gather)

    async def run():
        return await requisition.review_with_identity(None, git=None, config=None, history=[], repo=None, stem="s", text="t", specs_dir=None, coverage_map=None, tier="high")

    assert asyncio.run(run()) == "a"
    assert asyncio.run(run()) is None
    assert asyncio.run(run()) is None
    verdict.mechanical = "ticket lint"
    gather.side_effect = ["a"]
    assert asyncio.run(run()) is verdict
