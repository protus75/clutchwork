# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: verify local config survives squash merges
# relates: [clutch/git.py, clutch/merge.py, clutch/seams.py]
# owner: clutch/merge.py
# verified: 407dfd0f
# hash: eeefe9098af94a6bf69c7c62ad14a5660c94f9b4110a45dcacbf8668134e0004
import asyncio
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock

import pytest

from clutch.git import GitError
from clutch.merge import dirty_overlap, write_squash
from clutch.seams import LocalFileSystem


@pytest.mark.asyncio
async def test_dirty_config_exempt():
    git = NS(
        main_write=asyncio.Lock, _commit_lock=asyncio.Lock(), status_porcelain=AsyncMock(return_value="M  config.yaml\0 M other.py\0"), diff_names=AsyncMock(return_value=["config.yaml", "other.py"])
    )
    findings = await dirty_overlap(NS(git=git, repo="repo"), "work")
    assert len(findings) == 1 and "other.py" in findings[0].message and "config.yaml" not in findings[0].message


@pytest.mark.asyncio
@pytest.mark.parametrize("status,fail", [(" M config.yaml\0", False), ("M  config.yaml\0", True), (" M other.py\0", False)])
async def test_squash_config(tmp_path, status, fail, monkeypatch):
    config = tmp_path / "config.yaml"
    config.write_bytes(b"owner\n")
    state = tmp_path / "state"
    calls = []

    async def command(repo, *args):
        calls.append(args)
        if args[0] == "show":
            return "base\n"
        if args[0] == "checkout":
            config.write_bytes(b"base\n")
        if args[0] == "merge-file":
            if fail:
                raise GitError(list(args), -1, "", "failed")
            (state / "merge-config-local").write_bytes(b"owner wins\nticket addition\n")
        return ""

    async def squash(*args):
        if "config.yaml" in status:
            assert config.read_bytes() == b"base\n"
        config.write_bytes(b"ticket\n")
        return "commit"

    async def effect(fn, **kwargs):
        return await fn()

    git = NS(status_porcelain=AsyncMock(return_value=status), diff_names=AsyncMock(return_value=["x"]), _run=command, merge_squash=squash)
    ctx = NS(repo=tmp_path, config=NS(state_dir=state), fs=LocalFileSystem(), git=git, driver=NS(effects=NS(run=effect), journal=NS(read=lambda: [], append=lambda *a, **kw: None)))
    ticket = NS(stem="work", frontmatter=NS(source="human"), sections={"Goal / Why": "goal"})
    monkeypatch.setattr("clutch.merge.refresh_index", AsyncMock())
    if fail:
        with pytest.raises(GitError):
            await write_squash(ctx, ticket, "reviewed", attempt=1)
        assert config.read_bytes() == b"owner\n"
    else:
        await write_squash(ctx, ticket, "reviewed", attempt=1)
        if "config.yaml" in status:
            assert config.read_bytes() == b"owner wins\nticket addition\n"
            assert calls == [
                ("show", "HEAD:config.yaml"),
                ("checkout", "HEAD", "--", "config.yaml"),
                ("merge-file", "--ours", str(state / "merge-config-local"), str(state / "merge-config-base"), str(config)),
            ]
        else:
            assert config.read_bytes() == b"ticket\n" and calls == []
