# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose:
# relates: [clutch/__main__.py, clutch/lockfile.py, clutch/meta.py, tests/integration/test_cli.py, tests/integration/test_git_tree_id.py]
# owner: engine
# verified: a5584821
# hash: 082d74e346ae59357a4075fb0168eb0c42a2880d13b7def36c8a1f69232940ed
import asyncio

from clutch.__main__ import main
from clutch.lockfile import Lockfile
from clutch.meta import digest, parse
from tests.integration.test_cli import CONFIG, ENV, Clock
from tests.integration.test_git_tree_id import setup_repo


def test_refresh_and_fill_with_writer_held(tmp_path, capsys):
    repo, git = setup_repo(tmp_path)
    (repo / "config.yaml").write_text(CONFIG + "\nmeta:\n  paths:\n    - {root: docs/, kind: plan}\n")
    (repo / "docs").mkdir()
    target = repo / "docs/example.md"
    target.write_text("original body\n")

    async def prepare():
        await git.init(repo, branch="main")
        await git.add(repo, ["docs/example.md"])
        await git.commit(repo, "initial")

    asyncio.run(prepare())
    holder = Lockfile(repo / ".clutch/state", instance_id="distinct-holder", verb="serve", clock=Clock())
    holder.acquire()
    try:
        assert main(["meta", "refresh", "docs/example.md"], cwd=repo, env=ENV, clock=Clock()) == 0
        fields, body, _ = parse(target.read_text(), ".md")
        assert body == "original body\n"
        assert fields["hash"] == digest("original body\n")
        assert main(["meta", "fill", "docs/example.md"], cwd=repo, env=ENV, clock=Clock()) == 2
        assert "distinct-holder" in capsys.readouterr().err
    finally:
        holder.release()


def test_refresh_refuses_when_commit_lock_is_held(tmp_path, monkeypatch, capsys):
    import fcntl
    from datetime import datetime, timedelta, timezone

    repo, _ = setup_repo(tmp_path)
    (repo / "config.yaml").write_text(CONFIG)
    state = repo / ".clutch/state"
    state.mkdir(parents=True)
    lock_path = state / "commit.lock"
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        times = iter((now, now + timedelta(seconds=61)))
        assert main(["meta", "refresh"], cwd=repo, env=ENV, clock=lambda: next(times)) == 2
    assert "commit.lock is held" in capsys.readouterr().err
