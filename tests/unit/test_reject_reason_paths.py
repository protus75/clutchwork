# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: An operator reject reason flows through the CLI parser, the control inbox, drain/serve admission, and runner verdict paths into the reject signal
# relates: [clutch/__main__.py, clutch/control.py, clutch/drain.py, clutch/journal.py, clutch/lockfile.py, clutch/runner.py, clutch/serve.py]
# owner: engine
# verified: 452057e3
# hash: bac19d52e80efd8ea332ff8316ca721190ddb685f084d9a8a79a32ea98c98f2c
import asyncio
import json
from pathlib import PurePath
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from clutch import __main__ as entry
from clutch import control, drain, runner
from clutch.journal import EventType
from clutch.lockfile import LockHeld
from clutch.serve import Serve
from tests.git_fake import GitFake


class Journal:
    def __init__(self, events=()):
        self.events = list(events)

    def read(self):
        return list(self.events)

    def append(self, kind, body, *, ticket=None, key=None):
        self.events.append(SimpleNamespace(type=kind, body=body, ticket=ticket, key=key))


@pytest.mark.parametrize("reason", [None, "r"])
def test_reject_ticket_signal(monkeypatch, reason):
    journal = Journal()
    checkout = SimpleNamespace(repo=PurePath("missing"), journal=journal)
    monkeypatch.setattr(runner, "_dead_dependents", AsyncMock())

    # PurePath has no I/O; the missing path is provided by a fake instead.
    class Missing:
        def __truediv__(self, value):
            return self

        def is_file(self):
            return False

    checkout.repo = Missing()
    asyncio.run(runner.reject_ticket("sample", checkout, reason=reason))
    assert journal.events[0].body == {"signal": "reject_verdict", "verdict": "kill", "actor": "operator", **({"reason": "r"} if reason else {})}


@pytest.mark.parametrize("reason", [None, "r"])
def test_verdict_forward(monkeypatch, reason):
    lock = Mock()
    monkeypatch.setattr(runner, "Lockfile", lambda *a, **kw: lock)
    monkeypatch.setattr(runner, "reap", AsyncMock())
    target = AsyncMock(return_value=0)
    monkeypatch.setattr(runner, "verdict_locked", target)
    checkout = SimpleNamespace(config=SimpleNamespace(state_dir="state"), git=GitFake(describe="head"), repo="repo", clock=None)
    asyncio.run(runner.verdict("sample", checkout, kill=True, reason=reason))
    target.assert_awaited_once_with("sample", checkout, kill=True, extension=False, **({"reason": "r"} if reason else {}))


@pytest.mark.parametrize("reason", [None, "r"])
def test_locked_forward(monkeypatch, reason):
    class Missing:
        def __truediv__(self, value):
            return self

        def is_file(self):
            return False

    history = [SimpleNamespace(ticket="sample", type=EventType.STATE_TRANSITION, body={"to": "gate_failed", "routed": "reject_queue"})]
    checkout = SimpleNamespace(repo=Missing(), git=None, journal=Journal(history), fs=None)
    monkeypatch.setattr(runner, "intake", AsyncMock(return_value=SimpleNamespace(refused={})))
    target = AsyncMock(return_value=True)
    monkeypatch.setattr(runner, "reject_ticket", target)
    asyncio.run(runner.verdict_locked("sample", checkout, kill=True, reason=reason))
    target.assert_awaited_once_with("sample", checkout, **({"reason": "r"} if reason else {}))


@pytest.mark.parametrize("reason", [None, "r"])
def test_apply_admission_forward(monkeypatch, reason):
    class Missing:
        def __truediv__(self, value):
            return self

        def is_file(self):
            return False

    checkout = SimpleNamespace(repo=Missing(), journal=Journal(), git=GitFake(rev_parse="base"))
    target = AsyncMock()
    monkeypatch.setattr(runner, "verdict_locked", target)
    asyncio.run(runner.apply_admission("sample", "reject", "key", "operator", checkout, reason=reason))
    target.assert_awaited_once_with("sample", checkout, kill=True, extension=False, **({"reason": "r"} if reason else {}))


@pytest.mark.parametrize("reason", [None, "r"])
def test_drain_and_serve_forward(monkeypatch, reason):
    target = AsyncMock(return_value={"refusal": None})
    monkeypatch.setattr(runner, "apply_admission", target)

    async def settle(callback):
        await callback("sample", "reject", "key", "operator", reason=reason)

    checkout = SimpleNamespace(control=SimpleNamespace(inbox=SimpleNamespace(settle_admissions=settle)))
    asyncio.run(drain.settle_admissions(checkout))
    target.assert_awaited_once_with("sample", "reject", "key", "operator", checkout, **({"reason": "r"} if reason else {}))
    target.reset_mock()
    owner = object.__new__(Serve)
    owner.checkout, owner.published = checkout, {}
    asyncio.run(owner.apply_verdict("sample", "reject", "key", "operator", reason=reason))
    target.assert_awaited_once_with("sample", "reject", "key", "operator", checkout, **({"reason": "r"} if reason else {}))


@pytest.mark.parametrize("reason", [None, "r"])
def test_consume_and_settle(reason):
    request = dict(request_id="req", lifecycle_id="life", verb="reject", stem="sample", hold_id=None, actor="operator", **({"operator_reason": reason} if reason else {}))
    journal = Journal()
    inbox = control.ControlInbox(
        journal=journal,
        lifecycle_id="life",
        holds=set,
        apply=lambda _: None,
        files=lambda: [PurePath("req.json")],
        read=lambda _: json.dumps(request).encode(),
        known=lambda _: True,
    )
    inbox.consume()
    body = journal.events[0].body
    assert {k: body[k] for k in request} == request
    assert ("operator_reason" in body) == (reason is not None)
    callback = AsyncMock(return_value={"refusal": None})
    asyncio.run(inbox.settle_admissions(callback))
    callback.assert_awaited_once_with("sample", "reject", "ticket-plane/sample/reject/req", "operator", **({"reason": "r"} if reason else {}))


def test_locked_cli_publishes_reason(monkeypatch):
    class Missing:
        def __truediv__(self, value):
            return self

        def is_file(self):
            return False

    checkout = SimpleNamespace(repo=Missing(), journal=Journal(), git=None, fs=None, config=SimpleNamespace(state_dir=PurePath("state")))
    monkeypatch.setattr(runner, "verdict", AsyncMock(side_effect=LockHeld(PurePath("lock"), {"verb": "drain"})))
    monkeypatch.setattr(runner, "ticket_pending", AsyncMock(return_value=False))
    monkeypatch.setattr(control, "read_active", lambda *a: ("life", None))
    published = []
    monkeypatch.setattr(control, "publish_request", lambda state, req, fs: published.append(req))
    assert asyncio.run(entry._verdict(checkout, "sample", "reject", None, True, False, reason="r")) == 0
    assert published[0].operator_reason == "r"


def test_parser_and_dispatch(monkeypatch):
    parser = entry._parser()
    assert parser.parse_args(["ticket", "reject", "--reason", "r", "sample"]).reason == "r"
    assert not hasattr(parser.parse_args(["ticket", "confirm", "sample"]), "reason")
    monkeypatch.setattr(entry, "load_config", lambda *a, **kw: SimpleNamespace(state_dir="state", providers=[]))
    for name in ("Journal", "Git", "CommitLock", "SubprocessExec"):
        monkeypatch.setattr(entry, name, lambda *a, **kw: object())
    target = AsyncMock(return_value=0)
    monkeypatch.setattr(entry, "_verdict", target)
    assert entry.main(["ticket", "reject", "--yes", "--reason", "r", "sample"], env={}) == 0
    assert target.await_args.kwargs == {"reason": "r"}
