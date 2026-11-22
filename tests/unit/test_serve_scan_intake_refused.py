# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify that a refused intake (a stray staged file) leaves Serve.scan returning the last ticket set and logs the refusal once, instead of stopping serve.
# relates: [clutch/serve.py, clutch/tickets.py, tests/unit/test_serve_idle_poll.py]
# owner: engine
# verified: 00000000
# hash: 0000000000000000000000000000000000000000000000000000000000000000
from types import SimpleNamespace

import pytest

from clutch import serve
from clutch.artifacts import Finding
from clutch.tickets import IntakeRefused
from tests.unit.test_serve_idle_poll import owner  # noqa: F401


@pytest.mark.asyncio
async def test_refused_intake_keeps_serving(owner, monkeypatch):  # noqa: F811
    events = []
    owner.log = SimpleNamespace(event=lambda name, **fields: events.append((name, fields)))
    owner.intake_refusal = None
    owner.scanned = {"kept": "ticket"}
    owner.checkout.git._overrides["status_porcelain"] = "M  config.yaml\n"

    async def refuse(*args, **kwargs):
        raise IntakeRefused(Finding(code="intake_stray", message="staged changes outside pending ticket files: config.yaml", paved_road="unstage them"))

    monkeypatch.setattr(serve, "intake", refuse)
    # Before the fix this raised and serve stopped with every in-flight run.
    assert await owner.scan() == {"kept": "ticket"}
    owner.scan_snapshot = "stale"
    assert await owner.scan() == {"kept": "ticket"}
    # One log line per distinct refusal, not one per poll.
    assert events == [("intake_refused", {"error": "staged changes outside pending ticket files: config.yaml -- unstage them"})]
