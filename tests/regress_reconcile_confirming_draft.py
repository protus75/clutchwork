"""Standalone reproducer for the confirmation versus idle recovery race."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Standalone reproducer for the race between draft confirmation and idle recovery; prints pass, defect or error as JSON and exits 0, 1 or 2
# relates: [clutch/control.py, clutch/journal.py, tests/integration/serve_rig.py, tests/integration/test_cli.py]
# owner: engine
# verified: 7abfadd2
# hash: 9ee2d40c107ace6547aa75a146265765329dceb1ea6d630b954c63ef17bdef70

import asyncio
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch.control import AdmissionRequest, publish_request
from clutch.journal import EventType
from tests.cli_helpers import root
from tests.integration.serve_rig import admission_ticket
from tests.loop_helpers import graph


async def scenario(root, monkeypatch):
    rig = await graph(root, monkeypatch)
    admission_ticket(root, "draft", paths=("docs/draft",))
    path = root / "tickets/draft/ticket.md"
    path.write_text(path.read_text().replace("state: confirmed", "state: draft"))
    await rig.checkout.git.add(root, ["tickets/draft/ticket.md"])
    await rig.checkout.git.commit(root, "draft fixture")
    owner = rig.owner
    owner.checkpoint = SimpleNamespace(poll=AsyncMock())
    owner.heartbeat = SimpleNamespace(cycle=lambda: None)
    owner.notifications = SimpleNamespace(poll=lambda: None)
    # Real inbox processing writes the request intent before invoking this callback.
    entered, release, completed = asyncio.Event(), asyncio.Event(), asyncio.Event()
    original = owner.apply_verdict

    async def held(*args, **kwargs):
        entered.set()
        await release.wait()
        return await original(*args, **kwargs)

    owner.apply_verdict = held
    settle = owner.control.inbox.settle_admissions

    async def observed(verdict):
        await settle(verdict)
        completed.set()

    owner.control.inbox.settle_admissions = observed
    lifecycle = owner.control.projection.lifecycle_id
    publish_request(rig.checkout.config.state_dir, AdmissionRequest("confirm-draft", lifecycle, "confirm", "draft", None, "operator"), rig.fs)
    task = asyncio.create_task(owner.verdicts())
    try:
        await entered.wait()
        key = "ticket-plane/draft/confirm/confirm-draft"
        before = rig.journal.read()
        assert any(e.type == EventType.EFFECT_INTENT and e.key == key for e in before)
        assert not any(e.type == EventType.EFFECT_COMPLETION and e.key == key for e in before)
        await owner.maintenance()
        release.set()
        await completed.wait()
        events = [e for e in rig.journal.read() if e.ticket == "draft"]
        return path.read_text(), events, key
    finally:
        release.set()
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


def result_ok(text, events, key):
    return (
        "state: confirmed" in text
        and not any(e.type == EventType.STATE_TRANSITION and e.body.get("to") == "abandoned" for e in events)
        and not any(e.body.get("reason") == "orphaned run" for e in events)
        and any(e.type == EventType.EFFECT_COMPLETION and e.key == key and e.body["result"]["refusal"] is None for e in events)
    )


def main():
    scratch = Path(".clutch/scratch")
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch.resolve()) as directory, pytest.MonkeyPatch.context() as patch:
        repo = root.__wrapped__(Path(directory))
        with redirect_stdout(io.StringIO()):
            text, events, key = asyncio.run(scenario(repo, patch))
        if result_ok(text, events, key):
            return "pass"
        abandoned = any(e.type == EventType.STATE_TRANSITION and e.body.get("to") == "abandoned" for e in events)
        alert = any(e.body.get("reason") == "orphaned run" for e in events)
        return "defect" if abandoned and alert else "error"


if __name__ == "__main__":
    try:
        status = main()
    except Exception:
        status = "error"
    print(json.dumps({"regression_result": status}))
    sys.exit({"pass": 0, "defect": 1, "error": 2}[status])
