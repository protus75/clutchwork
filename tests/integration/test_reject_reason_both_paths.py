# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test reject reason both paths
# relates: [clutch/__main__.py, clutch/ask.py, clutch/config.py, clutch/control.py, clutch/journal.py, clutch/lockfile.py, clutch/roadmap.py, clutch/runner.py]
# owner: engine
# verified: 96e46658
# hash: ea7380f14fa1aecaa72990a9538412e2be214ca4a672641d458c3b7d38871374
import asyncio
from pathlib import Path

import pytest

from clutch import __main__ as entry
from clutch import ask, control, runner
from clutch.journal import EventType
from clutch.lockfile import Lockfile
from clutch.roadmap import rejection_reason
from clutch.tickets import stamp
from tests.integration.test_mergequeue import admission_control, commit, ready
from tests.integration.test_mergequeue import ctx as context_fixture

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("inbox", [False, True])
def test_reject_both_paths(tmp_path, inbox):
    ctx = context_fixture.__wrapped__(tmp_path)

    async def exercise():
        ticket = await ready(ctx)
        path = ctx.repo / f"tickets/{ticket.stem}/ticket.md"
        ctx.fs.write(path, stamp(path.read_text(), "state", "draft").encode())
        await commit(ctx, ctx.repo, [str(path.relative_to(ctx.repo))])
        ctx.driver.journal.append(EventType.SIGNAL, {"signal": "ticket_intake", "state": "draft"}, ticket=ticket.stem)
        checkout = runner.Checkout(ctx.repo, ctx.config, ctx.env, ctx.exec_, ctx.git, ctx.driver.journal, ctx.fs, ctx.driver.clock, ctx.driver.sleep)
        if inbox:
            consumer = admission_control(ctx, known=lambda stem: stem == ticket.stem)
            owner = entry.build_serve(checkout)
            lock = Lockfile(ctx.config.state_dir, verb="drain", instance_id="live", clock=ctx.driver.clock)
            lock.acquire()
            control.write_active(ctx.config.state_dir, consumer.projection, ctx.fs, hold_id=None)
        try:
            assert await asyncio.to_thread(entry.main, ["ticket", "reject", "--yes", "--reason", "scope too wide", ticket.stem], cwd=ctx.repo, env=ctx.env, clock=ctx.driver.clock) == 0
            if inbox:
                consumer.inbox.consume()
                await consumer.inbox.settle_admissions(owner.apply_verdict)
            events = ctx.driver.journal.read()
            signal = next(e for e in events if e.body.get("signal") == "reject_verdict")
            assert signal.body == {"signal": "reject_verdict", "verdict": "kill", "actor": "operator", "reason": "scope too wide"}
            assert rejection_reason(events, ticket.stem).startswith("scope too wide")
        finally:
            if inbox:
                lock.release()

    asyncio.run(exercise())


def test_help_docs_and_prompt(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        entry._parser().parse_args(["ticket", "confirm", "--reason", "x", "sample"])
    assert error.value.code == 2
    with pytest.raises(SystemExit) as help_exit:
        entry._parser().parse_args(["ticket", "reject", "--help"])
    assert help_exit.value.code == 0
    assert "--reason" in capsys.readouterr().out
    for path in ("docs/how-clutch-works.md", "clutch/docs/host-running.md"):
        assert any("ticket reject" in line and "--reason" in line for line in (ROOT / path).read_text().splitlines())
    from clutch.config import load_config
    from tests.integration.test_config import VALID

    (tmp_path / "config.yaml").write_text(VALID)
    assert "ticket reject --yes --reason" in ask.render("drafts", ["sample"], load_config(None, cwd=tmp_path), tmp_path)
