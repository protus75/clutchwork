# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks that runner verdict confirm, reject and admission repair write ticket.md only inside the Git.commit_edit callback, and that a draft refusal is raised before any commit.
# relates: [clutch/journal.py, clutch/runner.py]
# owner: engine
# verified: 2dd7da28
# hash: eac980381693f305a66459e33c07503de7637fe1b248c7f361a975bc333406b8
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import runner
from clutch.journal import EventType


class Journal:
    def __init__(self, events=()):
        self.events = list(events)

    def read(self):
        return list(self.events)

    def append(self, kind, body, *, ticket=None, key=None):
        self.events.append(SimpleNamespace(type=kind, body=body, ticket=ticket, key=key))


@pytest.mark.parametrize("branch", ["confirm", "reject", "repair"])
def test_ticket_edit_waits_for_commit_callback(monkeypatch, branch):
    root = Path("/fake")
    path = root / "tickets/sample/ticket.md"
    original = "---\nstate: draft\npriority: P1\n---\n"
    state = "rejected" if branch == "reject" else "confirmed"
    stamped = original.replace("state: draft", f"state: {state}")
    files = {path: stamped if branch == "repair" else original}
    entered, release = asyncio.Event(), asyncio.Event()
    inside = False
    writes = []
    commits = []

    class FS:
        def write(self, target, data):
            writes.append((inside, target, data.decode()))
            files[target] = data.decode()

    async def commit_edit(repo, message, *, only, edit):
        nonlocal inside
        entered.set()
        await release.wait()
        inside = True
        try:
            await edit()
            commits.append((message, only, files[path]))
        finally:
            inside = False
        return "sha"

    async def run(repo, *args):
        return original if args[0] == "show" else ""

    events = []
    if branch == "repair":
        events = [
            SimpleNamespace(type=EventType.EFFECT_INTENT, key="key", ticket="sample", body={}),
            SimpleNamespace(type=EventType.EFFECT_INTENT, key="key", ticket="sample", body={}),
            SimpleNamespace(type=EventType.EFFECT_COMPLETION, key="key/baseline", ticket="sample", body={"result": "base"}),
        ]
    journal = Journal(events)
    checkout = SimpleNamespace(repo=root, fs=FS(), journal=journal, git=SimpleNamespace(commit_edit=commit_edit, rev_parse=AsyncMock(return_value="base"), _run=run))
    monkeypatch.setattr(Path, "is_file", lambda p: p in files)
    monkeypatch.setattr(Path, "read_text", lambda p, *a, **kw: files[p])
    monkeypatch.setattr(runner, "intake", AsyncMock(return_value=SimpleNamespace(refused={})))
    monkeypatch.setattr(runner, "_dead_dependents", AsyncMock())
    if branch == "repair":
        monkeypatch.setattr(runner, "verdict_locked", AsyncMock())

    async def exercise():
        if branch == "repair":
            task = asyncio.create_task(runner.apply_admission("sample", "confirm", "key", "operator", checkout))
        else:
            task = asyncio.create_task(runner.verdict_locked("sample", checkout, kill=branch == "reject"))
        await entered.wait()
        assert files[path] == (stamped if branch == "repair" else original)
        assert writes == []
        release.set()
        await task

    asyncio.run(exercise())
    assert commits == [(f"clutch(sample): {state}", ["tickets/sample/ticket.md"], stamped)]
    assert writes == ([] if branch == "repair" else [(True, path, stamped)])


def test_draft_refusal_precedes_commit(monkeypatch):
    path = Path("/fake/tickets/sample/ticket.md")
    checkout = SimpleNamespace(repo=Path("/fake"), journal=Journal(), git=SimpleNamespace(commit_edit=AsyncMock()), fs=None)
    monkeypatch.setattr(Path, "is_file", lambda p: p == path)
    monkeypatch.setattr(Path, "read_text", lambda p, *a, **kw: "---\nstate: draft\n---\n")
    monkeypatch.setattr(runner, "intake", AsyncMock(return_value=SimpleNamespace(refused={})))
    monkeypatch.setattr(runner, "verdict_refusal", lambda *a: ("refused first", "resolve it"))
    with pytest.raises(runner.Refusal, match="refused first"):
        asyncio.run(runner.verdict_locked("sample", checkout, kill=False))
    checkout.git.commit_edit.assert_not_awaited()
