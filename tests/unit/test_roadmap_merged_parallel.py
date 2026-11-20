import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

import clutch.__main__ as cli
from clutch import roadmap
from clutch.journal import EventType
from clutch.runner import Refusal
from tests.fakes import FakeJournal


class FakeGit:
    def __init__(self, log):
        self.log = log

    async def rev_parse(self, repo, ref):
        return "sha"

    async def _run(self, repo, *args):
        return self.log


def checkout(log="a-row\nb-row\nc-row\n"):
    return SimpleNamespace(repo=Path("/repo"), journal=FakeJournal(), git=FakeGit(log))


def state(c, stem, target, **body):
    c.journal.append(EventType.STATE_TRANSITION, {"to": target, **body}, ticket=stem)


def run(c, stems=(), **kwargs):
    return asyncio.run(roadmap.merged(c, stems, **kwargs))


def test_overlapping_runs_count():
    c = checkout()
    for stem, target in [("a-row", "running"), ("b-row", "running"), ("a-row", "merged"), ("b-row", "merged"), ("c-row", "running"), ("c-row", "merged")]:
        state(c, stem, target)
    assert run(c, since="v1", at_least=2, parallel=True) == (True, ["roadmap merged: ok"])
    assert run(c, since="v1", at_least=3, parallel=True) == (False, ["roadmap merged: 2 of 3 tickets merged since v1 match"])


def test_serial_runs_do_not_count():
    c = checkout("a-row\nb-row\n")
    for stem, target in [("a-row", "running"), ("a-row", "merged"), ("b-row", "running"), ("b-row", "merged")]:
        state(c, stem, target)
    assert run(c, since="v1", at_least=1, parallel=True) == (False, ["roadmap merged: 0 of 1 tickets merged since v1 match"])
    assert run(c, since="v1", at_least=1) == (True, ["roadmap merged: ok"])


def test_spent_cap_on_a_parallel_stem_fails():
    c = checkout("b-row\n")
    state(c, "a-row", "running")
    state(c, "b-row", "running")
    state(c, "a-row", "gate_failed", reason="merge_conflict_rerun_spent")
    state(c, "b-row", "merged")
    state(c, "d-row", "running")
    state(c, "d-row", "gate_failed", reason="merge_conflict_rerun_spent")
    assert run(c, since="v1", at_least=1, parallel=True) == (False, ["roadmap merged: a-row hit merge_conflict_rerun_spent"])


def test_parallel_needs_a_count():
    c = checkout()
    read = c.journal.read
    c.journal.read = lambda: pytest.fail("journal read")
    with pytest.raises(Refusal, match="count filter needs --at-least"):
        run(c, ["a-row"], parallel=True)
    c.journal.read = read
    assert run(c, since="v1", at_least=1, parallel=True) == (False, ["roadmap merged: 0 of 1 tickets merged since v1 match"])


def test_main_passes_parallel(monkeypatch):
    monkeypatch.setattr(cli, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=Path("/state")))
    monkeypatch.setattr(cli, "child_env", lambda *a: {})
    calls = []

    async def fake(checkout, stems, **kwargs):
        calls.append(kwargs["parallel"])
        return True, ["roadmap merged: ok"]

    monkeypatch.setattr(roadmap, "merged", fake)
    args = ["roadmap", "merged", "--since", "v1", "--at-least", "10"]
    cli.main(args + ["--parallel"], cwd=Path("/repo"), env={})
    cli.main(args, cwd=Path("/repo"), env={})
    assert calls == [True, False]
