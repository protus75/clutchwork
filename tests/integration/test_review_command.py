"""On-demand review uses the committed ticket and records its verdict."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests `clutch ticket review`: it reviews the committed ticket, journals the verdict, handles the checkout and commit locks, provisional dependencies, prior findings and intake of only the named ticket
# relates: [clutch/__main__.py, clutch/journal.py, clutch/llm.py, clutch/lockfile.py, clutch/reconcile.py, clutch/requisition.py, clutch/status.py]
# owner: clutch/__main__.py
# verified: ae1a5a3b
# hash: 8b31ed1e561f1d9e98fc05df512f24a8f180f0a5492211ac919d7d3296f24ded

import pytest

from clutch.__main__ import main
from clutch.journal import EventType, Journal
from clutch.llm import FakeLLM
from clutch.lockfile import Lockfile
from clutch.reconcile import orphans
from clutch.requisition import FIRST_REVIEW
from clutch.status import last_states
from tests.cli_helpers import ENV, git_out, ticket, write
from tests.integration.test_drain import Clock, commit_ticket, confirmed, make_root
from tests.stage_replies import requisition_reply as reply

pytestmark = pytest.mark.disk_io_skip


def run(root, monkeypatch, llm, stem):
    monkeypatch.setattr("clutch.__main__.ProviderLLM", lambda *args, **kwargs: llm)
    return main(["ticket", "review", stem], cwd=root, env=ENV, clock=Clock())


def verdicts(root):
    return [e for e in Journal(root / ".clutch/state", Clock()).read() if e.type == EventType.SIGNAL and e.body.get("signal") == "requisition_verdict"]


def test_review_preflight_failure_refuses(tmp_path, monkeypatch, capsys):
    root = make_root(tmp_path)
    write(root, "candidate", ticket())

    async def preflight(self):
        return ["probe refused"]

    monkeypatch.setattr("clutch.providers.ProviderLLM.preflight", preflight)
    assert main(["ticket", "review", "candidate"], cwd=root, env=ENV, clock=Clock()) == 2
    assert "clutch ticket: probe refused" in capsys.readouterr().err
    assert verdicts(root) == []
    lock = Lockfile(root / ".clutch/state", verb="drain", instance_id="probe", clock=Clock())
    lock.acquire()
    lock.release()


def test_review_approve_journals_verdict_for_committed_blob(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    write(root, "candidate", ticket())
    assert run(root, monkeypatch, FakeLLM([reply("approve")]), "candidate") == 0
    [event] = verdicts(root)
    assert event.body["verdict"] == "approve"
    assert event.body["ticket_sha"] == git_out(root, "rev-parse", "main:tickets/candidate/ticket.md").strip()
    assert "state: confirmed" in git_out(root, "show", "main:tickets/candidate/ticket.md")


def test_review_snag_prints_findings_and_exits_1(tmp_path, monkeypatch, capsys):
    root = make_root(tmp_path)
    write(root, "candidate", ticket())
    finding = {"code": "fence", "path": "thing.py", "line": 7, "message": "missing caller", "paved_road": "add caller"}
    assert run(root, monkeypatch, FakeLLM([reply("snag", [finding])]), "candidate") == 1
    assert "- [fence] thing.py:7 missing caller (add caller)" in capsys.readouterr().out
    assert verdicts(root)[0].body["verdict"] == "snag"


def test_review_refuses_without_a_model_call(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    commit_ticket(root, "merged", confirmed())
    Journal(root / ".clutch/state", Clock()).append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="merged")
    llm = FakeLLM([])
    for stem in ("missing", "merged"):
        assert run(root, monkeypatch, llm, stem) == 2
    assert llm.requests == []


def test_review_unmerged_dependency_is_provisional(tmp_path, monkeypatch, capsys):
    root = make_root(tmp_path)
    commit_ticket(root, "dependency", confirmed())
    commit_ticket(root, "candidate", confirmed("- dependency"))
    llm = FakeLLM([reply("approve")])
    assert run(root, monkeypatch, llm, "candidate") == 0
    output = capsys.readouterr().out
    assert "review candidate: provisional, not recorded -- depends on unmerged dependency; the drain reviews it again before its first run" in output
    assert "review candidate: approve" in output
    assert len(llm.requests) == 1
    assert verdicts(root) == []


def test_review_releases_checkout_lock_during_call(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    write(root, "candidate", ticket())
    state_dir = root / ".clutch/state"
    journal = Journal(state_dir, Clock())
    journal.append(EventType.STATE_TRANSITION, {"to": "confirmed"}, ticket="candidate")
    observed = []

    def probe(request):
        lock = Lockfile(state_dir, verb="drain", instance_id="probe", clock=Clock())
        lock.acquire()
        try:
            events = journal.read()
            observed.append((lock.held, orphans(events), last_states(events)["candidate"]))
        finally:
            lock.release()
        return reply("approve")

    assert run(root, monkeypatch, FakeLLM([probe]), "candidate") == 0
    assert observed == [(True, [], "confirmed")]
    assert last_states(journal.read())["candidate"] == "confirmed"
    assert [event.body["verdict"] for event in verdicts(root)] == ["approve"]


def test_review_committed_ticket_while_checkout_locked(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    commit_ticket(root, "candidate", confirmed())
    lock = Lockfile(root / ".clutch/state", verb="drain", instance_id="engine", clock=Clock())
    lock.acquire()
    try:
        llm = FakeLLM([reply("approve")])
        assert run(root, monkeypatch, llm, "candidate") == 0
        [event] = verdicts(root)
        assert event.body["verdict"] == "approve"
        assert event.body["ticket_sha"] == git_out(root, "rev-parse", "main:tickets/candidate/ticket.md").strip()
        assert len(llm.requests) == 1
    finally:
        lock.release()


def test_review_changed_ticket_while_checkout_locked(tmp_path, monkeypatch, capsys):
    root = make_root(tmp_path)
    commit_ticket(root, "candidate", confirmed())
    path = root / "tickets/candidate/ticket.md"
    path.write_text(path.read_text().replace("## Goal / Why", "## Goal / Why\nPending edit"))
    lock = Lockfile(root / ".clutch/state", verb="drain", instance_id="engine", clock=Clock())
    lock.acquire()
    try:
        llm = FakeLLM([reply("approve")])
        assert run(root, monkeypatch, llm, "candidate") == 0
        assert "Pending edit" in git_out(root, "show", "main:tickets/candidate/ticket.md")
        assert verdicts(root)[0].body["verdict"] == "approve"
    finally:
        lock.release()


def test_review_uses_previous_findings_after_edit(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    commit_ticket(root, "candidate", confirmed())
    finding = {"code": "fence", "message": "missing caller", "paved_road": "add caller"}
    llm = FakeLLM([reply("snag", [finding]), reply("approve")])
    assert run(root, monkeypatch, llm, "candidate") == 1
    path = root / "tickets/candidate/ticket.md"
    path.write_text(path.read_text().replace("## Goal / Why", "## Goal / Why\nChanged."))
    git_out(root, "add", "tickets/candidate/ticket.md")
    git_out(root, "commit", "-m", "edit ticket")
    assert run(root, monkeypatch, llm, "candidate") == 0
    blocks = [r.rendered.split("<<clutch-data:begin prior_review>>\n", 1)[1].split("\n<<clutch-data:end prior_review>>", 1)[0] for r in llm.requests]
    assert blocks[0] == FIRST_REVIEW
    assert "missing caller" in blocks[1] and "+Changed." in blocks[1]


def test_review_does_not_reap_running_ticket(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    commit_ticket(root, "candidate", confirmed())
    path = root / "tickets/candidate/ticket.md"
    path.write_text(path.read_text().replace("## Goal / Why", "## Goal / Why\nChanged."))
    journal = Journal(root / ".clutch/state", Clock())
    journal.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="other")
    lock = Lockfile(root / ".clutch/state", verb="drain", instance_id="engine", clock=Clock())
    lock.acquire()
    try:
        assert run(root, monkeypatch, FakeLLM([reply("approve")]), "candidate") == 0
        assert last_states(journal.read())["other"] == "running"
    finally:
        lock.release()


def test_review_commit_lock_timeout(tmp_path, monkeypatch, capsys):
    import fcntl
    from datetime import timedelta

    from clutch import __main__ as entry
    from clutch.lockfile import CommitLock

    root = make_root(tmp_path)
    commit_ticket(root, "candidate", confirmed())
    path = root / "tickets/candidate/ticket.md"
    path.write_text(path.read_text().replace("## Goal / Why", "## Goal / Why\nChanged."))
    clock = Clock()

    async def sleep(seconds):
        clock.now += timedelta(seconds=seconds)

    monkeypatch.setattr(entry, "CommitLock", lambda state, **kwargs: CommitLock(state, clock=clock, sleep=sleep))
    (root / ".clutch/state").mkdir(parents=True, exist_ok=True)
    with (root / ".clutch/state/commit.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert entry.main(["ticket", "review", "candidate"], cwd=root, env=ENV, clock=clock) == 2
    assert "commit.lock" in capsys.readouterr().err
    assert "Changed." not in git_out(root, "show", "main:tickets/candidate/ticket.md")


def test_review_intakes_only_named_ticket(tmp_path, monkeypatch):
    root = make_root(tmp_path)
    draft = ticket().replace("---\n", "---\nstate: draft\n", 1)
    write(root, "alpha", draft)
    write(root, "beta", draft)
    beta = (root / "tickets/beta/ticket.md").read_bytes()
    assert run(root, monkeypatch, FakeLLM([reply("approve")]), "alpha") == 0
    subjects = git_out(root, "log", "--format=%s").splitlines()
    assert "clutch(alpha): ticket" in subjects
    assert "clutch(beta): ticket" not in subjects
    assert git_out(root, "status", "--porcelain", "--", "tickets/beta/").strip()
    assert (root / "tickets/beta/ticket.md").read_bytes() == beta
    events = Journal(root / ".clutch/state", Clock()).read()
    assert not any(e.type == EventType.SIGNAL and e.body.get("signal") == "ticket_intake" and e.ticket == "beta" for e in events)
