from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import triage


@pytest.mark.asyncio
@pytest.mark.parametrize(("rejected", "expected"), [(True, "declined"), (False, "tombstone")])
async def test_tombstone_rejected(monkeypatch, rejected, expected, tmp_path):
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
    box = SimpleNamespace(pending=lambda: [message], messages=lambda: [message], root=tmp_path)
    checkout = SimpleNamespace(repo=tmp_path, config=SimpleNamespace(routing_default_tier="medium"))
    response = triage.TriageReply(verdict="tombstone", link="target", summary="summary", rationale="reason", evidence=["original"], reopen_after_days=30)
    driver = SimpleNamespace(run=AsyncMock(return_value=SimpleNamespace(outcome="ok", artifact=response)))
    monkeypatch.setattr(triage, "recover_retro_ticket", AsyncMock(return_value=None))
    monkeypatch.setattr(triage, "read_registry", lambda repo: [])
    monkeypatch.setattr(triage, "list_open_tickets", AsyncMock(return_value=""))
    monkeypatch.setattr(triage, "committed", AsyncMock(return_value=True))
    monkeypatch.setattr(triage, "is_rejected", AsyncMock(return_value=rejected))
    record = AsyncMock(return_value="recorded")
    monkeypatch.setattr(triage, "_record", record)
    spec = SimpleNamespace(meta=SimpleNamespace(effort="medium", version="1"))
    await triage._settle_pass(checkout, driver, box, spec, [], 0, frozenset())
    args = record.await_args.args
    assert args[4] == expected
    assert args[5] == ("box-1" if rejected else "target")
    assert args[6].evidence == (["original", "unresolvable link: target"] if rejected else ["original"])
