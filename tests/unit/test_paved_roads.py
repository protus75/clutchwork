import asyncio
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch.box import Box, BoxError
from clutch.config import Retro as RetroSettings
from clutch.drain import Report
from clutch.journal import EventType
from clutch.providers import ClaudeAdapter, CodexAdapter
from clutch.retro import Retro
from clutch.status import dismiss_admission, run_admission, triage_admission
from tests.fakes import FakeJournal


def test_drain_heads_name_the_drain_verb():
    for report in (Report(killed=True), Report(halted="12h elapsed")):
        text = report.render()
        assert "Continue with `clutch engine drain`." in text
        assert "python -m clutch" not in text


def test_missing_ticket_road_names_clutch_verbs():
    assert run_admission("item", [], False, None).paved_road == "author it with `clutch ticket new item`, fill it, then `clutch engine run item`"


def test_unknown_box_id_carries_a_road():
    for admission in (triage_admission("missing", []), dismiss_admission("missing", [])):
        assert (admission.outcome, admission.message, admission.paved_road) == ("refuse", "unknown box id missing", "name ids that `clutch status` lists")


def test_enqueue_errors_name_a_repair():
    box = Box(Path("box"), None)
    with pytest.raises(BoxError) as exc:
        box.enqueue(message_class="suggestion", origin="x", summary="s", stage="check")
    assert str(exc.value) == "stage and outcome must both be set or both be null; pass both or neither"
    with pytest.raises(BoxError) as exc:
        box.enqueue(message_class="bug_report", origin="x", summary="s")
    assert str(exc.value).startswith("invalid box message: ")
    assert str(exc.value).endswith("; correct the fields named above and enqueue again")


def test_login_roads_name_the_drain_verb():
    assert ClaudeAdapter.LOGIN_ROAD == "run claude interactively and complete /login, then `clutch engine drain`"
    assert CodexAdapter.LOGIN_ROAD == "run codex login, then `clutch engine drain`"


@pytest.mark.parametrize("exception", [False, True])
def test_retro_error_code_names_the_stage_outcome(monkeypatch, exception):
    from clutch import daemon, retro, runner

    journal = FakeJournal()
    journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="one")
    run = AsyncMock(return_value=SimpleNamespace(outcome="invalid_artifact"))
    rev_parse = AsyncMock(side_effect=OSError("disk full") if exception else None, return_value="head")
    box = SimpleNamespace(messages=lambda: [], enqueue=lambda **kw: calls.append(kw))
    calls = []
    checkout = SimpleNamespace(
        journal=journal,
        config=SimpleNamespace(retro=RetroSettings(), state_dir=Path("state"), drain=SimpleNamespace(max_ticket_minutes=10)),
        clock=lambda: datetime(2026, 1, 2, tzinfo=UTC),
        git=SimpleNamespace(rev_parse=rev_parse),
        repo=Path("repo"),
        fs=None,
    )
    driver = SimpleNamespace(run=run, log=SimpleNamespace(event=lambda *a, **kw: None))
    pipeline = SimpleNamespace(stages=SimpleNamespace(driver=driver))

    async def evidence(*args):
        return {"merged_count": 1}

    monkeypatch.setattr(retro, "production_evidence", evidence)
    monkeypatch.setattr(retro, "load_spec", lambda _: SimpleNamespace(meta=SimpleNamespace(version="1", tier="x", effort="x")))

    class Specs:
        def __truediv__(self, name):
            return SimpleNamespace(read_text=lambda: "")

    monkeypatch.setattr(runner, "SPECS_DIR", Specs())
    monkeypatch.setattr(daemon, "storm_producer", lambda **kw: box)
    asyncio.run(Retro(checkout, pipeline)(forced=True))
    [failed] = [e for e in journal.read() if e.body.get("kind") == "retro_failed"]
    assert failed.body["error_code"] == ("OSError" if exception else "invalid_artifact")
    assert len(calls) == 1 and calls[0]["origin"] == "retro-failed/initial/forced"
    assert run.await_count == (0 if exception else 1)
