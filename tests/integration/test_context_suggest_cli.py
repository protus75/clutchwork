# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: End-to-end test of clutch context suggest: refuses with no index, builds the index, suggests files that changed together while another lock is held without changing the database, and checks that the docs list the verb
# relates: [clutch/__main__.py]
# owner: engine
# verified: ae1a5a3b
# hash: 63477a9b6550a99a9ebdba85854a713e1ff1a2a4dbf44a70d3db6f74d60ee911
from pathlib import Path

import pytest

pytestmark = pytest.mark.disk_io_skip


def test_documentation():
    root = Path(__file__).resolve().parents[2]
    assert (root / "clutch/docs/host-running.md").read_text().count("| `context suggest` |") == 1
    assert (root / "docs/how-clutch-works.md").read_text().count("| `context suggest <stem>` |") == 1
    assert "clutch context suggest" in (root / "README.md").read_text()


def test_context_suggest_end_to_end(tmp_path, monkeypatch, capsys):
    import asyncio

    from clutch import index
    from clutch.__main__ import main
    from clutch.lockfile import Lockfile
    from tests.cli_helpers import CONFIG, ENV, Clock
    from tests.integration.test_git_tree_id import setup_repo

    repo, git = setup_repo(tmp_path)
    (repo / "config.yaml").write_text(CONFIG)
    (repo / "tickets/demo").mkdir(parents=True)
    (repo / "tickets/demo/ticket.md").write_text("## Goal / Why\nContext\n## Scope fence\n- fence.py\n")

    async def prepare():
        await git.init(repo, branch="main")
        for number in (1, 2):
            (repo / "fence.py").write_text(f"fence = {number}\n")
            (repo / "related.py").write_text(f"related = {number}\n")
            await git.add(repo, ["fence.py", "related.py"])
            await git.commit(repo, f"change {number}\n\nclutch-ticket: past-{number}")

    asyncio.run(prepare())

    class Creator:
        def load(self, conn, name):
            return []

        def create(self, conn, name):
            return []

    monkeypatch.setattr(index, "default_creator", Creator())
    assert main(["context", "suggest", "demo"], cwd=repo, env=ENV, clock=Clock()) == 2
    assert "no_index" in capsys.readouterr().err
    assert main(["index", "build"], cwd=repo, env=ENV, clock=Clock()) == 0
    capsys.readouterr()
    db = repo / ".clutch/state/index.duckdb"
    before = db.read_bytes()
    lock = Lockfile(repo / ".clutch/state", verb="serve", instance_id="holder", clock=Clock())
    lock.acquire()
    try:
        assert main(["context", "suggest", "demo"], cwd=repo, env=ENV, clock=Clock()) == 0
    finally:
        lock.release()
    assert capsys.readouterr().out == "context suggest: suggested\n- related.py  # changed with fence.py in 2 past tickets\n"
    assert db.read_bytes() == before
