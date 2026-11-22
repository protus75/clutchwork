# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Runs `clutch roadmap merged` end to end over stems, a release and a since-tag count check, without changing git or the journal
# relates: [clutch/__main__.py, clutch/git.py, clutch/journal.py, clutch/lockfile.py, clutch/seams.py, tests/integration/test_cli.py]
# owner: clutch/roadmap.py
# verified: d32c32ad
# hash: 3976ef7da22db4b52cba643a029eec238b8381b18f168ac4f1090eb3d9c9ea9c
import asyncio
from datetime import UTC, datetime

import pytest

from clutch.__main__ import main
from clutch.git import Git
from clutch.journal import EventType, Journal
from clutch.lockfile import CommitLock
from clutch.seams import SubprocessExec
from tests.integration.test_cli import CONFIG, ENV

pytestmark = pytest.mark.disk_io_skip


def test_roadmap_merged_end_to_end(tmp_path, capsys):
    def clock():
        return datetime.now(UTC)

    git = Git(SubprocessExec(), env=ENV, timeout=10, commit_lock=CommitLock(tmp_path / ".clutch/state", clock=clock, sleep=asyncio.sleep))

    def call(*args):
        return asyncio.run(git._run(tmp_path, *args)).strip()

    asyncio.run(git.init(tmp_path, branch="main"))
    (tmp_path / "config.yaml").write_text(CONFIG)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/roadmap.md").write_text(
        "### 1.0.0\n| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n|---|---|---|---|---|---|---|---|\n| 1 | `a-row` | roadmap | feature | P1 | | | a |\n"
        "| 2 | `b-row` | roadmap | feature | P1 | | | b |\n"
    )
    asyncio.run(git.add(tmp_path, ["config.yaml", "docs/roadmap.md"]))
    asyncio.run(git.commit(tmp_path, "initial"))
    asyncio.run(git.tag(tmp_path, "v1.0.0", "phase", "HEAD"))
    for i, message in enumerate(["first\n\nclutch-ticket: a-row", "second\n\nclutch-ticket: b-row", "ordinary"]):
        (tmp_path / "change").write_text(str(i))
        asyncio.run(git.add(tmp_path, ["change"]))
        asyncio.run(git.commit(tmp_path, message))
    journal = Journal(tmp_path / ".clutch/state", clock)
    for stem in ("a-row", "b-row"):
        journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket=stem)
    head, tags = call("rev-parse", "HEAD"), call("tag", "--list")
    segments = {p: p.read_bytes() for p in journal.dir.glob("*") if p.is_file()}
    for args in (["a-row", "b-row"], ["--release", "1.0.0"], ["--since", "v1.0.0", "--at-least", "2"]):
        assert main(["roadmap", "merged", *args], cwd=tmp_path, env=ENV) == 0
        assert capsys.readouterr().out == "roadmap merged: ok\n"
    assert main(["roadmap", "merged", "--since", "v1.0.0", "--at-least", "3"], cwd=tmp_path, env=ENV) == 1
    assert capsys.readouterr().out == "roadmap merged: 2 of 3 tickets merged since v1.0.0 match\n"
    assert main(["roadmap", "merged", "--since", "v9.9.9", "--at-least", "1"], cwd=tmp_path, env=ENV) == 2
    assert capsys.readouterr().err.startswith("clutch roadmap:")
    assert (call("rev-parse", "HEAD"), call("tag", "--list")) == (head, tags)
    assert {p: p.read_bytes() for p in journal.dir.glob("*") if p.is_file()} == segments
