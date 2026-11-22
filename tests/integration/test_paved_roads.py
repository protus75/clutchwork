# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that refusal and failure messages (reject queue, halted drain, box errors, retro failures) name a working paved-road verb or repair
# relates: [clutch/box.py, clutch/journal.py, clutch/seams.py, tests/integration/test_cli.py, tests/integration/test_drain.py, tests/integration/test_retro.py]
# owner: engine
# verified: ae1a5a3b
# hash: ff7c5d855ffad7d1bbaa6433506184bf60cc6d7a59ed286145ffbed7526a5f53
import asyncio
from datetime import timedelta

import pytest

from clutch.box import Box, BoxError, Resolution, read_registry
from clutch.journal import EventType
from clutch.seams import LocalFileSystem
from tests.cli_helpers import ticket, write
from tests.integration.test_drain import START, Clock, Script, commit_ticket, confirmed, drain, journal, make_root
from tests.integration.test_retro import merged, rig

pytestmark = pytest.mark.disk_io_skip


def test_reject_queue_road_names_confirm_and_reject(tmp_path, capsys):
    root = make_root(tmp_path)
    commit_ticket(root, "spent", confirmed())
    j = journal(root)
    j.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="spent")
    j.append(EventType.STATE_TRANSITION, {"to": "gate_failed", "stage": "check"}, ticket="spent")
    for _ in range(3):
        j.append(EventType.CAP_CONSUMED, {"cap": "retry", "ticket_sha": "x"}, ticket="spent")
    assert drain(root, Script()) == 0
    assert (
        "- spent: gate_failed at check; retry cap spent (3/3) -- edit tickets/spent/ticket.md, then `clutch ticket confirm spent`; or retire it with `clutch ticket reject spent`"
    ) in capsys.readouterr().out


def test_halted_reoffer_road_names_the_drain_verb(tmp_path, capsys):
    root = make_root(tmp_path)
    write(root, "red", ticket())
    clock = Clock()

    def overrun(checkout):
        clock.now = START + timedelta(hours=13)

    assert drain(root, Script(outcomes={"red": ["gate_failed"]}, hooks={"red": overrun}), clock) == 1
    assert "- red: gate_failed at review; 3 of 3 retry units left -- `clutch engine drain` re-offers it" in capsys.readouterr().out


def test_box_reads_name_a_repair(tmp_path):
    root = tmp_path / "box"
    root.mkdir()
    box = Box(root, LocalFileSystem())
    bad = root / "bad.json"
    bad.write_text("{}")
    with pytest.raises(BoxError) as exc:
        box.messages()
    assert "bad.json" in str(exc.value) and str(exc.value).endswith("; move it out of the box directory or restore it from backup")
    bad.unlink()
    id, _ = box.enqueue(message_class="suggestion", origin="x", summary="s")
    box.resolve(id, Resolution(kind="ticket", link="done"))
    with pytest.raises(BoxError) as exc:
        box.resolve(id, Resolution(kind="ticket", link="done"))
    assert str(exc.value) == f"box id {id} is already resolved; its resolution stands and `clutch view status` shows it"
    decisions = tmp_path / "tickets" / "decisions"
    decisions.mkdir(parents=True)
    (decisions / "b.md").write_text("body only")
    with pytest.raises(BoxError) as exc:
        read_registry(tmp_path)
    text = str(exc.value)
    assert "b.md" in text and "decision record missing YAML frontmatter" in text
    assert text.endswith("; restore it from its last commit") and text.count("restore it from its last commit") == 1


def test_retro_failure_records_the_stage_outcome(tmp_path):
    c, _, hook, _ = rig(tmp_path, ["not json at all"])
    merged(c.journal)
    asyncio.run(hook(forced=True))
    [failed] = [e for e in c.journal.read() if e.body.get("kind") == "retro_failed"]
    assert failed.body == {"kind": "retro_failed", "window_boundary": "initial", "trigger": "forced", "error_code": "invalid_artifact"}
    [message] = Box(c.config.state_dir / "box", c.fs).messages()
    assert message.message_class == "failure_report" and message.origin == failed.key


def test_retro_exception_keeps_its_class_name(tmp_path):
    c, _, hook, _ = rig(tmp_path, ['{"proposals": []}'])

    async def fail(*args):
        raise OSError("disk full")

    hook.commit_report = fail
    merged(c.journal)
    asyncio.run(hook(forced=True))
    [failed] = [e for e in c.journal.read() if e.body.get("kind") == "retro_failed"]
    assert failed.body["error_code"] == "OSError"
    [message] = Box(c.config.state_dir / "box", c.fs).messages()
    assert message.message_class == "failure_report" and message.origin == failed.key
