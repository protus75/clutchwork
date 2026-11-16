from clutch.__main__ import main
from clutch.config import load_config
from clutch.journal import EventType, Journal
from clutch.llm import FakeLLM
from clutch.policy import baseline_identity
from clutch.roadmap import parse
from tests.integration.test_author import _routes
from tests.integration.test_cli import ENV, git_out
from tests.integration.test_drain import Clock, make_root
from tests.integration.test_triage import author_reply, requisition_reply
from tests.unit.test_roadmap_table import document, row


def setup_repo(tmp_path):
    root = make_root(tmp_path)
    _routes(root)
    config = root / "config.yaml"
    config.write_text(config.read_text().replace("engine_plane_safety_inventory: []", "engine_plane_safety_inventory: [config.yaml]"))
    cfg = load_config(None, cwd=root)
    journal = Journal(cfg.state_dir, Clock())
    journal.append(EventType.SIGNAL, {"signal": "review_baseline", "verdict": "NO_GO", "identity": baseline_identity(cfg)})
    (root / "docs").mkdir()
    (root / "docs/sample-plan.md").write_text("# Sample plan\n\nBuild the work.\n")
    (root / "docs/roadmap.md").write_text(
        document(
            row(1, "`first-row`", owner="sample plan 1", priority="P2", content="Build first."),
            row(2, "`second-row`", owner="sample plan 1", priority="P2", depends="`first-row`", content="Build second."),
        )
    )
    git_out(root, "add", "config.yaml", "docs")
    git_out(root, "commit", "-m", "roadmap setup")
    return root, journal


def test_roadmap_author_end_to_end(tmp_path, monkeypatch, capsys):
    root, journal = setup_repo(tmp_path)

    def run(llm):
        monkeypatch.setattr("clutch.__main__.ProviderLLM", lambda *a, **k: llm)
        return main(["roadmap", "author", "--ahead", "1"], cwd=root, env=ENV, clock=Clock())

    llm = FakeLLM([author_reply("first-row"), requisition_reply("approve")])
    assert run(llm) == 0
    out = capsys.readouterr().out
    assert "roadmap: authored row 1 first-row" in out and "roadmap: 1 of 1 rows open" in out
    assert git_out(root, "log", "-2", "--format=%s").splitlines() == ["clutch(roadmap): author first-row", "clutch(first-row): ticket"]
    assert git_out(root, "show", "--format=", "--name-only", "HEAD").strip() == "docs/roadmap.md"
    assert parse((root / "docs/roadmap.md").read_text())[0].linked
    assert "state: confirmed" in (root / "tickets/first-row/ticket.md").read_text()
    assert all(req.surface != "triage" for req in llm.requests)
    head = git_out(root, "rev-parse", "HEAD")
    empty = FakeLLM([])
    assert run(empty) == 0 and not empty.requests
    assert git_out(root, "rev-parse", "HEAD") == head
    assert "roadmap: 1 of 1 rows open" in capsys.readouterr().out
    journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="first-row")
    llm2 = FakeLLM([author_reply("second-row"), requisition_reply("approve")])
    assert run(llm2) == 0
    assert git_out(root, "log", "-3", "--format=%s").splitlines() == ["clutch(roadmap): author second-row", "clutch(second-row): ticket", "clutch(roadmap): strike first-row"]
    first, second = parse((root / "docs/roadmap.md").read_text())
    assert first.struck and second.linked


def test_roadmap_author_refusals_change_nothing(tmp_path, monkeypatch, capsys):
    from clutch.lockfile import Lockfile

    root, _ = setup_repo(tmp_path)
    monkeypatch.setattr("clutch.__main__.ProviderLLM", lambda *a, **k: llm)
    llm = FakeLLM([])
    path = root / "docs/roadmap.md"
    path.write_text(path.read_text() + "\nchanged\n")
    head, content = git_out(root, "rev-parse", "HEAD"), path.read_bytes()
    assert main(["roadmap", "author"], cwd=root, env=ENV, clock=Clock()) == 2
    assert capsys.readouterr().err.startswith("clutch roadmap:")
    path.write_bytes(content[:-9])
    content = path.read_bytes()
    config = load_config(None, cwd=root)
    lock = Lockfile(config.state_dir, verb="test", instance_id="test", clock=Clock())
    lock.acquire()
    try:
        assert main(["roadmap", "author"], cwd=root, env=ENV, clock=Clock()) == 2
        assert capsys.readouterr().err.startswith("clutch roadmap:")
    finally:
        lock.release()
    assert main(["roadmap", "author", "--ahead", "0"], cwd=root, env=ENV, clock=Clock()) == 2
    assert capsys.readouterr().err.startswith("clutch roadmap:")
    assert git_out(root, "rev-parse", "HEAD") == head and path.read_bytes() == content
    assert not list((config.state_dir / "box").glob("*")) and not llm.requests
