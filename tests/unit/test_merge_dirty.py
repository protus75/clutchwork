# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Dirty-checkout findings for staged paths outside the diff, renames, and unstaged paths that overlap the branch diff
# relates: [clutch/merge.py]
# owner: clutch/merge.py
# verified: 452057e3
# hash: 945dca6e90f73bf5f11615593a0721271729d2e5b395a550f447c2cd1a5d5e09
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from clutch.merge import dirty_overlap
from tests.git_fake import GitFake


def findings(status):
    git = GitFake(status_porcelain=status, diff_names=["branch.py"])
    return asyncio.run(dirty_overlap(SimpleNamespace(git=git, repo="repo"), "ticket"))


def test_staged_only_path_outside_diff_is_refused():
    [finding] = findings("M  other.py\0")
    assert finding.code == "dirty_checkout" and "other.py" in finding.message
    assert "sweep" in finding.message and "unstage" in finding.paved_road


def test_unstaged_path_outside_diff_is_not_refused():
    assert findings(" M other.py\0") == []


def test_staged_rename_collects_both_paths():
    [finding] = findings("R  new.py\0old.py\0")
    assert "new.py" in finding.message and "old.py" in finding.message


def test_staged_and_overlapping_paths_give_both_findings():
    result = findings("M  other.py\0 M branch.py\0")
    assert len(result) == 2 and all(f.code == "dirty_checkout" for f in result)
    assert "branch.py" in result[0].message and "overwrite" in result[0].message
    assert "other.py" in result[1].message and "sweep" in result[1].message
