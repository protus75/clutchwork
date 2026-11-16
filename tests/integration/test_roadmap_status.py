import asyncio
import shlex
import sys
from datetime import UTC, datetime

import clutch.__main__ as cli
from clutch import roadmap
from clutch.git import CommitLock, Git
from clutch.journal import EventType, Journal
from clutch.seams import SubprocessExec
from tests.integration.test_cli import CONFIG, ENV


def test_roadmap_status_end_to_end(tmp_path, capsys):
    def clock():
        return datetime.now(UTC)

    git = Git(SubprocessExec(), env=ENV, timeout=10, commit_lock=CommitLock(tmp_path / ".clutch/state", clock=clock, sleep=asyncio.sleep))

    def call(*args):
        return asyncio.run(git._run(tmp_path, *args)).strip()

    asyncio.run(git.init(tmp_path, branch="main"))
    (tmp_path / "config.yaml").write_text(CONFIG)
    path = tmp_path / roadmap.ROADMAP
    path.parent.mkdir()
    command = shlex.join([sys.executable, "-c", "pass"])
    path.write_text(
        "### 1.0.0\n| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n|---|---|---|---|---|---|---|---|\n| 1 | `done-row` | roadmap | feature | P2 | | | done |\n"
        "| 2 | `next-row` | roadmap | feature | P2 | | | next |\n```gate\n" + command + "\n```\n"
    )
    asyncio.run(git.add(tmp_path, ["config.yaml", roadmap.ROADMAP]))
    asyncio.run(git.commit(tmp_path, "initial"))
    journal = Journal(tmp_path / ".clutch/state", clock)
    journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="done-row")
    segments = list((tmp_path / ".clutch/state").rglob("*.jsonl"))
    before = (call("rev-parse", "HEAD"), call("status", "--porcelain"), {p: p.read_bytes() for p in segments})
    assert cli.main(["roadmap", "status"], cwd=tmp_path, env=ENV) == 0
    assert capsys.readouterr().out == "release 1.0.0: 1 merged, 0 authored, 1 ready, 0 blocked; gate not run\nnext: next-row\n"
    assert (call("rev-parse", "HEAD"), call("status", "--porcelain"), {p: p.read_bytes() for p in segments}) == before
    assert cli.main(["roadmap", "gate", "1.0.0"], cwd=tmp_path, env=ENV) == 0
    capsys.readouterr()
    ts = journal.read()[-1].ts
    assert cli.main(["roadmap", "status"], cwd=tmp_path, env=ENV) == 0
    assert capsys.readouterr().out == f"release 1.0.0: 1 merged, 0 authored, 1 ready, 0 blocked; gate passed {ts}\nnext: next-row\n"
