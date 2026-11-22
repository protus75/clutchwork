"""Changed ticket intake and publication proceed beside active implementations."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Integration test that changed-ticket intake, draft/priority edits and stop requests proceed while two implementations hold admission slots, without an exclusive gate pending.
# relates: [clutch/llm.py, clutch/serve.py, tests/integration/serve_rig.py, tests/integration/test_cli.py, tests/integration/test_serve_parallel_admission.py]
# owner: engine
# verified: d32c32ad
# hash: 1cda67f69423d8dc69c493e8c4110ed48340ca18124eed7563f034f187771301

import asyncio
import json

import pytest

from clutch import serve
from clutch.llm import FakeLLM
from tests.integration.serve_rig import admission_ticket, finish, request, start_admission, until
from tests.integration.test_cli import root  # noqa: F401
from tests.integration.test_serve_parallel_admission import parallel_rig

pytestmark = pytest.mark.disk_io_skip


@pytest.mark.asyncio
async def test_changed_tickets_overlap_and_stop(root, monkeypatch):
    rig = await parallel_rig(root, monkeypatch, 2)
    entered = {stem: asyncio.Event() for stem in ("one", "two")}
    release = asyncio.Event()
    call = FakeLLM.call

    async def blocked(model, req):
        if req.surface == "implement":
            entered[req.ticket].set()
            await release.wait()
        return await call(model, req)

    monkeypatch.setattr(FakeLLM, "call", blocked)
    admission_ticket(root, "one", paths=("docs/one",), priority="P0")
    run = await start_admission(rig, monkeypatch)
    try:
        await until(rig, entered["one"].is_set)
        admission_ticket(root, "two", paths=("docs/two",), priority="P1")
        await until(rig, entered["two"].is_set)
        assert not release.is_set()
        admission_ticket(root, "draft", paths=("docs/draft",))
        path = root / "tickets/draft/ticket.md"
        path.write_text(path.read_text().replace("state: confirmed", "state: draft"))
        await until(rig, lambda: "draft" in rig.owner.core.scheduler.pending)
        assert any(e.ticket == "draft" and e.body.get("signal") == "ticket_intake" and e.body.get("state") == "draft" for e in rig.journal.read())
        path.write_text(path.read_text().replace("priority: P2", "priority: P1"))
        await until(rig, lambda: rig.owner.core.scheduler.pending["draft"].frontmatter.priority == "P1")
        rig.time.advance(serve.SERVE_POLL_S * 2)
        assert not rig.owner.core.admission.exclusive_pending()
        request(rig, "stop", "stop-held")
        await until(rig, lambda: rig.owner.control.projection.stop_requested)
        assert set(rig.owner.core.admission.runs) == {"one", "two"}
        release.set()
        await until(rig, run.done)
        assert await run == 0
        assert json.loads((rig.checkout.config.state_dir / "control/active.json").read_text()) is None
    finally:
        release.set()
        if not run.done():
            await finish(rig, run)
