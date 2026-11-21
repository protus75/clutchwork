# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test author calibration
# relates: [clutch/author.py, clutch/calibration.py, clutch/journal.py, tests/fakes.py, tests/unit/test_retro_recurrence.py]
# owner: engine
# verified: 93253297
# hash: 87b4551a6446b6e3cd156b037cd809b4a8a222e66ec751ecde8baef4dd34472b
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from clutch import author, calibration
from clutch.journal import EventType
from tests.fakes import FakeJournal
from tests.unit.test_retro_recurrence import message


def test_latest_reads_the_newest_calibration():
    journal = FakeJournal()
    older = [{"provider": "claude", "model": "old", "runs": 1, "expected_p50": 30.0, "actual_p50": 3.0, "actual_p90": 3.0}]
    newer = [{"provider": "codex", "model": "m1", "runs": 2, "expected_p50": 45.0, "actual_p50": 6.0, "actual_p90": 8.4}]
    for rows in (older, newer):
        journal.append(EventType.SIGNAL, {"signal": calibration.ESTIMATE_CALIBRATION, "rows": rows})
        journal.append(EventType.SIGNAL, {"signal": "unrelated", "rows": older})
    journal.append(EventType.EFFECT_COMPLETION, {"signal": calibration.ESTIMATE_CALIBRATION, "rows": older})
    # Wrong: select the oldest calibration, an unrelated signal, or a non-signal event.
    assert calibration.latest(journal.read()) == newer
    # Wrong: assume a calibration exists and index into an empty history.
    assert calibration.latest(FakeJournal().read()) == []


@pytest.mark.parametrize("has_calibration, expected", [(True, "codex/m1: 2 runs, estimate p50 45.0m, actual p50 6.0m, actual p90 8.4m\n"), (False, "none\n")])
def test_author_prompt_carries_the_latest_table(monkeypatch, has_calibration, expected):
    class Done(Exception):
        pass

    async def ls_files(repo):
        return ["clutch/specs/review.md"]

    async def open_tickets(checkout):
        return "none"

    async def run(stage, *args, **kwargs):
        stage.render(None, [])
        raise Done

    journal = FakeJournal()
    if has_calibration:
        for row in (
            {"provider": "claude", "model": "old", "runs": 1, "expected_p50": 30.0, "actual_p50": 3.0, "actual_p90": 3.0},
            {"provider": "codex", "model": "m1", "runs": 2, "expected_p50": 45.0, "actual_p50": 6.0, "actual_p90": 8.4},
        ):
            journal.append(EventType.SIGNAL, {"signal": calibration.ESTIMATE_CALIBRATION, "rows": [row]})
    inputs = []
    monkeypatch.setattr(Path, "read_text", lambda self: "spec")
    monkeypatch.setattr(author, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(effort="medium")))
    monkeypatch.setattr(author, "render", lambda spec, values: inputs.append(values) or "rendered")
    monkeypatch.setattr(author, "list_open_tickets", open_tickets)
    monkeypatch.setattr(author, "template", lambda kind: f"template for {kind}")
    checkout = SimpleNamespace(repo=Path("/repo"), git=SimpleNamespace(ls_files=ls_files), journal=journal, config=SimpleNamespace(state_dir=Path("/state"), routing_default_tier="medium"))
    item = message().model_copy(update={"verdict": SimpleNamespace(rationale="observed")})
    with pytest.raises(Done):
        asyncio.run(author.author(checkout, SimpleNamespace(run=run), SimpleNamespace(root=Path("/box")), item, 1))
    # Wrong: omit calibration, pass the older table, or emit an empty block before calibration.
    assert inputs[0]["calibration"] == expected
