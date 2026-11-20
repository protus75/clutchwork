# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test merge dirty
# relates: [clutch/merge.py]
# owner: clutch/merge.py
# verified: 9a610809
# hash: 94ab11eae99d8a04bb6e0695758af1d8e4b46227552897bec098eecbe791a6f6
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from clutch.merge import dirty_overlap


def findings(status):
    git = SimpleNamespace(main_write=asyncio.Lock, status_porcelain=AsyncMock(return_value=status), diff_names=AsyncMock(return_value=["branch.py"]))
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
