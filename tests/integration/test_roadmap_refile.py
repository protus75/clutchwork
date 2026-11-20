# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test roadmap refile
# relates: [clutch/box.py, clutch/git.py, clutch/journal.py, clutch/roadmap.py, clutch/seams.py, tests/integration/test_cli.py]
# owner: engine
# verified: 96e46658
# hash: d423e2cf15311dbbfea3b54cb22e77040147ac6f34f9d86d39860013afd7410e
import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from clutch import roadmap
from clutch.box import Box, Resolution
from clutch.git import CommitLock, Git
from clutch.journal import Journal
from clutch.seams import LocalFileSystem, SubprocessExec
from tests.integration.test_cli import ENV


def test_decline_with_real_journal_and_box(tmp_path):
    def clock():
        return datetime.now(UTC)

    git = Git(SubprocessExec(), env=ENV, timeout=10, commit_lock=CommitLock(tmp_path / "state", clock=clock, sleep=asyncio.sleep))
    asyncio.run(git.init(tmp_path, branch="main"))
    path = tmp_path / roadmap.ROADMAP
    path.parent.mkdir()
    path.write_text("### 1.0.0\n| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n|---|---|---|---|---|---|---|---|\n| 1 | `held-row` | roadmap | feature | P1 | | | Build it. |\n")
    asyncio.run(git.add(tmp_path, [roadmap.ROADMAP]))
    asyncio.run(git.commit(tmp_path, "initial"))
    fs = LocalFileSystem()
    checkout = SimpleNamespace(repo=tmp_path, git=git, fs=fs, config=SimpleNamespace(state_dir=tmp_path / "state", caps=SimpleNamespace(supervise=2)), journal=Journal(tmp_path / "state", clock))
    box = Box(checkout.config.state_dir / "box", fs)

    async def decline(ids):
        box.resolve(ids[0], Resolution(kind="declined", link="missing"))

    asyncio.run(roadmap.author_ahead(checkout, 1, decline))
    lines = asyncio.run(roadmap.author_ahead(checkout, 1, decline))
    assert len(box.messages()) == 2
    assert all("reword the row's Content" not in line for line in lines)
