"""Author publication and rollback share the atomic Git writer boundary."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Verify atomic Author publication, compensation and decision-record writes.
# relates: [clutch/author.py, clutch/git.py, clutch/seams.py, clutch/triage.py, tests/fakes.py, tests/unit/test_author_roadmap_row.py]
# owner: engine
# verified: 9c24a9bd
# hash: f021b55d91aa8643a86587f9c73873e734693a9de2efb919cf77c54e054f49a9

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from clutch import author, triage
from clutch.git import GitError, NothingToCommit, blob_sha
from clutch.seams import LocalFileSystem
from tests.fakes import FakeJournal
from tests.unit.test_author_roadmap_row import row
from tests.unit.test_retro_recurrence import message


class Lock:
    def __init__(self):
        self.locked = False

    async def __aenter__(self):
        if self.locked:
            raise RuntimeError("recursive writer acquire")
        self.locked = True

    async def __aexit__(self, *args):
        self.locked = False


class Git:
    def __init__(self, repo, failure):
        self.repo, self.failure = repo, failure
        self.lock = Lock()
        self.commits = []
        self.head = {}

    @property
    def locked(self):
        return self.lock.locked

    async def ls_files(self, repo):
        return ["docs/sample-plan.md"]

    async def _run(self, repo, *args):
        if args[0] == "ls-tree":
            return blob_sha(self.head[args[-1]]) if args[-1] in self.head else ""
        if self.failure == "listing":
            raise GitError(["git"], 1, "", "listing refused")
        return ""

    async def commit_edit(self, repo, msg, *, only, edit):
        async with self.lock:
            await edit()
            if msg == "clutch(sample-row): ticket":
                if self.failure in {"commit", "later", "landed", "prior"}:
                    if self.failure == "later":
                        (repo / only[0]).write_bytes(b"later writer")
                    if self.failure == "landed":
                        self.head = {name: (repo / name).read_bytes() for name in only}
                    raise OSError("commit refused")
            if "compensate" in msg:
                raise NothingToCommit(["git"], 0, "", "")
            self.commits.append((msg, only))
            return "sha"


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["none", "commit", "partial", "later", "landed", "listing", "snapshot", "prior"])
async def test_publication_and_compensation(tmp_path, monkeypatch, failure):
    git = Git(tmp_path, failure)
    ticket = tmp_path / "tickets/sample-row/ticket.md"
    evidence = ticket.parent / "evidence/report.json"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"owned evidence")
    if failure == "prior":
        ticket.write_bytes(b"prior candidate")
    gate_seen = []
    removals = []
    read_bytes, rmdir = Path.read_bytes, Path.rmdir

    def reading(path):
        if failure == "snapshot" and path == evidence and not git.locked:
            raise OSError("snapshot refused")
        return read_bytes(path)

    def removing(path):
        assert git.locked  # Rules out directory removal after commit_edit returns.
        removals.append(path)
        return rmdir(path)

    class FS(LocalFileSystem):
        def write(self, path, data):
            assert git.locked  # Rules out pre-lock publication and restoration.
            super().write(path, data)
            if path == ticket and failure == "partial":
                raise OSError("write completed then failed")

    async def run(stage, *args, **kwargs):
        assert not git.locked  # Rules out a lock spanning the Author call.
        gate = stage.gates[0]
        gate.copied["sample-row"] = [str(evidence.relative_to(tmp_path))]
        gate.copied_bytes[str(evidence.relative_to(tmp_path))] = b"owned evidence"
        gate_seen.append(gate)
        reply = author.AuthorReply(stem="sample-row", ticket="reviewed ticket")
        await stage.review(reply, 1)
        return SimpleNamespace(outcome="ok", artifact=reply)

    async def review(*args, **kwargs):
        assert not git.locked  # Rules out a lock spanning requisition review.
        return SimpleNamespace(verdict="approve", findings=[], calls=1, ticket_sha="review", provider="fake", model="fake", spec_version="1", input_identity=None)

    async def effect(action, **kwargs):
        return await action()

    monkeypatch.setattr(Path, "read_text", lambda self: "spec")
    monkeypatch.setattr(Path, "read_bytes", reading)
    monkeypatch.setattr(Path, "rmdir", removing)
    monkeypatch.setattr(author, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(effort="medium")))
    monkeypatch.setattr(author, "list_open_tickets", AsyncMock(return_value="none"))
    monkeypatch.setattr(author, "neighbors_block", AsyncMock(return_value="none"))
    monkeypatch.setattr(author, "review_with_identity", review)
    decline = AsyncMock(return_value=author.AuthorOutcome(declined="declined"))
    monkeypatch.setattr(author, "failure_declined", decline)
    monkeypatch.setattr(author.AuthorGate, "check", lambda *args: SimpleNamespace(verdict="pass"))
    monkeypatch.setattr(author, "stamp", lambda text, *args: text)

    validations = []

    def validate(*args):
        validations.append(args)
        if len(validations) > 1:
            assert git.locked  # Rules out final validation before the writer lock.
        return SimpleNamespace(scope_fence=(), frontmatter=SimpleNamespace(gate_bypass=[]))

    monkeypatch.setattr(author, "validate_ticket", validate)
    monkeypatch.setattr(author, "resolve_baseline", lambda *args, **kwargs: SimpleNamespace(binds=False))
    monkeypatch.setattr(author, "start_state", lambda *args, **kwargs: "draft")
    checkout = SimpleNamespace(
        repo=tmp_path, git=git, fs=FS(), journal=FakeJournal(), config=SimpleNamespace(state_dir=tmp_path, review=SimpleNamespace(coverage_map=None), routing_default_tier="medium")
    )
    box = SimpleNamespace(root=tmp_path / "box", resolve=lambda *args: None)
    driver = SimpleNamespace(run=run, effects=SimpleNamespace(run=effect))
    item = message().model_copy(update={"message_class": "roadmap_row", "roadmap_row": row(), "verdict": SimpleNamespace(rationale="test")})
    result = await author.author(checkout, driver, box, item, 1)
    # A no-op implementation cannot satisfy the distinct success/failure tree states.
    if failure == "none":
        assert result.stem == "sample-row" and ticket.read_bytes() == b"reviewed ticket"
        assert git.commits == [("clutch(sample-row): ticket", ["tickets/sample-row/ticket.md", "tickets/sample-row/evidence/report.json"])]
        decline.assert_not_awaited()
    else:
        assert result.declined == "declined"
        decline.assert_awaited_once()
        assert "commit failed:" in decline.await_args.args[-1]
        if failure in {"later", "landed"}:
            assert ticket.read_bytes() == (b"later writer" if failure == "later" else b"reviewed ticket")
            assert evidence.exists() == (failure == "landed")
        elif failure == "prior":
            assert ticket.read_bytes() == b"prior candidate"
            assert not evidence.exists()
        else:
            assert not ticket.parent.exists()
            assert removals == [evidence.parent, ticket.parent]
    assert gate_seen[0].copied == {}  # Rules out stale gate ownership after handling failure.


@pytest.mark.asyncio
@pytest.mark.parametrize("caller", ["direct", "failure", "triage"])
async def test_decision_record_writes_under_lock(tmp_path, caller):
    git = Git(tmp_path, "none")
    writes, effects = [], []

    class FS(LocalFileSystem):
        def write(self, path, data):
            assert git.locked  # Rules out writing at either caller before commit_record.
            writes.append((path, data))
            super().write(path, data)

    async def effect(action, **kwargs):
        effects.append(kwargs)
        return await action()

    checkout = SimpleNamespace(repo=tmp_path, git=git, fs=FS())
    driver = SimpleNamespace(effects=SimpleNamespace(run=effect))
    box = SimpleNamespace(resolve=lambda *args: None)
    item = message()
    record_id = "special" if caller == "direct" else f"declined-{item.id}"
    if caller == "direct":
        await author.commit_record(checkout, driver, record_id, b"distinct record bytes")
    elif caller == "failure":
        await author.failure_declined(checkout, driver, box, item, "distinct failure")
    else:
        reply = triage.TriageReply(verdict="declined", link=None, summary="distinct triage", rationale="classified", evidence=[], reopen_after_days=9)
        await triage._record(checkout, driver, box, item.id, "declined", item.id, reply, "raw")
    assert len(writes) == 1  # Rules out both caller and callback writing.
    assert (b"distinct record bytes" if caller == "direct" else b"distinct failure" if caller == "failure" else b"distinct triage") in writes[0][1]
    assert git.commits == [(f"clutch(decisions): {record_id}", [str(author.record_path(record_id))])]
    assert effects == [{"key": f"ticket-plane/decisions/{record_id}", "ticket": None}]
