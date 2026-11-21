# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: clutch index build end to end through main
# relates: [clutch/__main__.py]
# owner: engine
# verified: 99c2ebc3
# hash: 9a2eb70d1428f2cbb97162653cf1ca79d18ae4f272b8b5afce03a0b81c66a204
import asyncio

import duckdb

from clutch import index
from clutch.__main__ import main
from clutch.lockfile import Lockfile
from tests.integration.test_cli import CONFIG, ENV, Clock
from tests.integration.test_git_tree_id import setup_repo


def test_index_build(tmp_path, monkeypatch, capsys):
    repo, git = setup_repo(tmp_path)
    (repo / "config.yaml").write_text(CONFIG)
    (repo / "tracked.md").write_text("# Indexed document\n")

    async def prepare():
        await git.init(repo, branch="main")
        await git.add(repo, ["tracked.md"])
        await git.commit(repo, "base")

    asyncio.run(prepare())

    class Creator:
        def __init__(self):
            self.calls = []

        def load(self, conn, name):
            self.calls.append(("load", name))
            return []

        def create(self, conn, name):
            self.calls.append(("create", name))
            return []

    creator = Creator()
    monkeypatch.setattr(index, "default_creator", creator)
    assert main(["index", "build"], cwd=repo, env=ENV, clock=Clock()) == 0
    db = repo / ".clutch/state/index.duckdb"
    assert db.exists()
    with duckdb.connect(str(db)) as conn:
        assert conn.execute("SELECT path FROM files WHERE path = 'tracked.md'").fetchall() == [("tracked.md",)]
    assert ("load", "fts") in creator.calls
    assert main(["index", "build"], cwd=repo, env=ENV, clock=Clock()) == 0
    lock = Lockfile(repo / ".clutch/state", verb="serve", instance_id="holder", clock=Clock())
    lock.acquire()
    try:
        assert main(["index", "build"], cwd=repo, env=ENV, clock=Clock()) == 2
        err = capsys.readouterr().err
        assert err.startswith("clutch index: ") and " -- " in err
    finally:
        lock.release()
