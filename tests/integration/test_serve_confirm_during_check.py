"""Verdict effects complete while an unrelated Check retains its run slot."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Integration tests that serve applies confirm and reject verdict effects, and refuses a reject on a running ticket, while an unrelated Check holds its run slot, without blocking disjoint admission.
# relates: [clutch/config.py, clutch/control.py, clutch/journal.py, clutch/stages.py, tests/integration/serve_rig.py, tests/integration/test_cli.py]
# owner: engine
# verified: 407dfd0f
# hash: 746142c3da2e766b76118a2501b1ac80f0853f0fee875b9fa14430b4cead3084

# The generated metadata purpose can exceed the line length limit.
# ruff: noqa: E501

import asyncio
from contextlib import asynccontextmanager

import pytest

from clutch import stages
from clutch.control import AdmissionRequest, publish_request
from clutch.journal import EventType
from tests.integration.serve_rig import admission_graph, admission_ticket, finish, start_admission, until
from tests.integration.test_cli import root


@pytest.mark.asyncio
async def test_confirmation_during_queued_merge_and_check(root, monkeypatch):
    entered, release = asyncio.Event(), asyncio.Event()
    original_check = stages.check

    async def held_check(ctx, ticket, slip, *, attempt):
        if ticket.stem == "one":
            entered.set()
            await release.wait()
        return await original_check(ctx, ticket, slip, attempt=attempt)

    monkeypatch.setattr(stages, "check", held_check)
    rig = await admission_graph(root, monkeypatch, {}, endings={"one": "noop"})
    admission_ticket(root, "one", paths=("docs/one",), priority="P0")
    admission_ticket(root, "two", paths=("docs/two",))
    path = root / "tickets/two/ticket.md"
    path.write_text(path.read_text().replace("state: confirmed", "state: draft"))
    run = await start_admission(rig, monkeypatch)
    try:
        await until(rig, entered.is_set)
        rig.owner.merge_work = lambda: True
        merging = rig.owner.core.admission.merging
        entries = []

        @asynccontextmanager
        async def counted_merging():
            async with merging():
                entries.append(True)
                yield

        monkeypatch.setattr(rig.owner.core.admission, "merging", counted_merging)
        await until(rig, lambda: len(entries) >= 1)
        publish_request(rig.checkout.config.state_dir, AdmissionRequest("confirm-two", rig.owner.control.projection.lifecycle_id, "confirm", "two", None, "operator"), rig.fs)
        key = "ticket-plane/two/confirm/confirm-two"
        try:
            await until(rig, lambda: any(e.type == EventType.EFFECT_COMPLETION and e.key == key for e in rig.journal.read()))
        except AssertionError as exc:
            raise AssertionError("CONFIRM_NOT_APPLIED_WHILE_CHECK_HELD") from exc
        events = rig.journal.read()
        assert not release.is_set()
        assert "state: confirmed" in path.read_text()
        signals = [e for e in events if e.ticket == "two" and e.body.get("signal") == "draft_confirmed"]
        assert len(signals) == 1
        committed = await rig.checkout.git._run(root, "show", "main:tickets/two/ticket.md")
        assert "state: confirmed" in committed
        assert [e.type for e in events if e.key == key] == [EventType.EFFECT_INTENT, EventType.EFFECT_COMPLETION]
    finally:
        release.set()
        await finish(rig, run)


@pytest.mark.asyncio
async def test_reject_and_refusal_do_not_block_disjoint_admission(root, monkeypatch):
    from dataclasses import replace

    import yaml

    from clutch.config import load_config

    entered, release, other_entered = (asyncio.Event() for _ in range(3))
    original_check = stages.check

    async def held_check(ctx, ticket, slip, *, attempt):
        if ticket.stem == "one":
            entered.set()
            await release.wait()
        elif ticket.stem == "other":
            other_entered.set()
        return await original_check(ctx, ticket, slip, attempt=attempt)

    monkeypatch.setattr(stages, "check", held_check)
    rig = await admission_graph(root, monkeypatch, {}, endings={"one": "noop", "other": "noop"})
    config_path = root / "config.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["scheduler"] = {"parallel": {"enabled": True, "max_runs": 2}, "max_unmerged": 4}
    config_path.write_text(yaml.safe_dump(config))
    rig.checkout = replace(rig.checkout, config=load_config(config_path, cwd=root))
    admission_ticket(root, "one", paths=("docs/one",), priority="P0")
    admission_ticket(root, "draft", paths=("docs/draft",))
    admission_ticket(root, "other", paths=("docs/other",), priority="P1")
    other = root / "tickets/other/ticket.md"
    other.write_text(other.read_text().replace("state: confirmed", "state: draft"))
    path = root / "tickets/draft/ticket.md"
    path.write_text(path.read_text().replace("state: confirmed", "state: draft"))
    run = await start_admission(rig, monkeypatch)
    try:
        await until(rig, entered.is_set)
        lifecycle = rig.owner.control.projection.lifecycle_id
        publish_request(rig.checkout.config.state_dir, AdmissionRequest("reject-running", lifecycle, "reject", "one", None, "operator"), rig.fs)
        publish_request(rig.checkout.config.state_dir, AdmissionRequest("reject-draft", lifecycle, "reject", "draft", None, "operator", "not needed"), rig.fs)
        keys = {"ticket-plane/one/reject/reject-running", "ticket-plane/draft/reject/reject-draft"}
        await until(rig, lambda: keys <= {e.key for e in rig.journal.read() if e.type == EventType.EFFECT_COMPLETION})
        completions = {e.key: e.body["result"] for e in rig.journal.read() if e.type == EventType.EFFECT_COMPLETION and e.key in keys}
        assert completions["ticket-plane/one/reject/reject-running"]["refusal"] is not None
        assert completions["ticket-plane/draft/reject/reject-draft"]["refusal"] is None
        assert "state: rejected" in path.read_text()
        assert not rig.owner.core.admission.exclusive_pending()
        publish_request(rig.checkout.config.state_dir, AdmissionRequest("confirm-other", lifecycle, "confirm", "other", None, "operator"), rig.fs)
        await until(rig, other_entered.is_set)
        assert not release.is_set()
    finally:
        release.set()
        await finish(rig, run)
