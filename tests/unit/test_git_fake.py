"""Contract for the shared Git seam fake."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Contract tests for GitFake: its method signatures match Git, and its overrides, call recording, defaults and lock objects behave as specified
# relates: [clutch/git.py, tests/git_fake.py]
# owner: engine
# verified: bc0baafb
# hash: ae85b3636e38301fbbd628715a01b562b1a7ad308f8efb7e7e87bf72477e17b6

import asyncio
import inspect
from pathlib import Path

import pytest

from clutch.git import Git
from tests.git_fake import GitFake


def signatures(cls):
    return {name: inspect.signature(member).parameters for name, member in inspect.getmembers(cls) if not name.startswith("_") and (inspect.iscoroutinefunction(member) or name == "main_write")}


def test_parity_detects_added_method(monkeypatch):
    assert signatures(GitFake) == signatures(Git)

    class ChangedGit(Git):
        pass

    async def added(self, dir):
        pass

    monkeypatch.setattr(ChangedGit, "added", added, raising=False)
    assert signatures(GitFake) != signatures(ChangedGit)


@pytest.mark.asyncio
async def test_overrides_and_calls():
    root = Path("/r")
    fake = GitFake(rev_parse="sha")
    assert await fake.rev_parse(root, "HEAD") == "sha"
    assert fake.calls == [("rev_parse", (root, "HEAD"), {})]
    error = ValueError("broken")
    with pytest.raises(ValueError) as caught:
        await GitFake(rev_parse=error).rev_parse(root, "HEAD")
    assert caught.value is error

    async def callback(dir, rev):
        return f"{dir}:{rev}"

    assert await GitFake(rev_parse=callback).rev_parse(root, "HEAD") == "/r:HEAD"
    with pytest.raises(TypeError):
        GitFake(nope=1)


@pytest.mark.asyncio
async def test_defaults_and_locks():
    fake = GitFake()
    root = Path("/r")
    assert await fake.status_porcelain(root) == ""
    assert await fake.ls_files(root) == []
    assert await fake.previous_release_tag(root) is None
    assert await fake.git_common_dir(root) == Path("/r/.git")
    assert isinstance(fake._commit_lock, asyncio.Lock)
    assert isinstance(fake.main_write(), asyncio.Lock)
    assert fake.main_write() is fake.main_write()
