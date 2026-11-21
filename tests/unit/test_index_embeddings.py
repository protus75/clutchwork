"""Embedding validation, recovery and creator ordering."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Embedding validation, recovery and creator ordering
# relates: [clutch/seams.py, tests/unit/test_index_build.py]
# owner: engine
# verified: 4b218af1
# hash: 8f44b52961a88c3b3052d2c871e6021f6adbcb17054ef98f7622491e4f0058b3

import pytest

from clutch.seams import ExecutableNotFound
from tests.unit.test_index_build import Creator, Exec, rig, rows, run


@pytest.mark.asyncio
async def test_embeddings_and_cleanup(rig):
    rig.config.index.embed = ["fake"]
    assert await run(rig) == []
    assert len(rows(rig, "embeddings")) == len(rows(rig, "chunks")) == 5
    assert rig.creator.calls == [("load", "vss"), ("load", "fts"), ("create", "vss")]
    assert len(rig.fs.removed) == 5
    for argv, call in rig.exec.calls:
        assert argv == ["fake"] and call["cwd"] == rig.root and call["timeout"] == 60 and call["env"] == {"X": "y"}
        assert call["stdin_path"].parent == rig.config.state_dir
        assert call["stdin_path"] in rig.fs.removed and not call["stdin_path"].exists()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("reply", "reason"),
    [
        ((2, "", ""), "exit 2"),
        (ExecutableNotFound("missing"), "exec ExecutableNotFound"),
        (TimeoutError(), "exec TimeoutError"),
        (OSError(), "exec OSError"),
        ((0, "oops", ""), "not json"),
        ((0, '"hello"', ""), "not a vector"),
        ((0, "{}", ""), "not a vector"),
        ((0, "[]", ""), "not a vector"),
        ((0, '[1,"x"]', ""), "not a vector"),
        ((0, "[true]", ""), "not a vector"),
        ((0, "[NaN]", ""), "not a vector"),
        ((0, "[1e308]", ""), "not a vector"),
    ],
)
async def test_failure_and_recovery(rig, reply, reason):
    rig.config.index.embed = ["fake"]
    rig.exec = Exec([reply])
    assert await run(rig) == [f"embed_failed: a.md#First: {reason}"]
    assert len(rig.fs.removed) == 1 and not rig.fs.removed[0].exists()
    assert len(rows(rig, "files")) == 2 and len(rows(rig, "chunks")) == 5
    assert len(rows(rig, "touches")) == 2 and len(rows(rig, "calls")) == 1
    assert rig.creator.calls[-1] == ("create", "fts")
    with pytest.raises(Exception):
        rows(rig, "embeddings")
    rig.exec = Exec()
    rig.creator = Creator()
    assert await run(rig) == []
    assert len(rows(rig, "embeddings")) == 5 and len(rig.exec.calls) == 5


@pytest.mark.asyncio
async def test_length_mismatch_new_and_existing(rig):
    rig.config.index.embed = ["fake"]
    rig.exec = Exec([(0, "[1,2,3]", ""), (0, "[1,2]", "")])
    assert await run(rig) == ["embed_failed: a.md#Next: length 2 != 3"]
    rig.exec = Exec()
    assert await run(rig) == []
    rig.fs.write(rig.root / "a.md", b"# New\ntext")
    rig.exec = Exec([(0, "[1,2]", "")])
    assert await run(rig) == ["embed_failed: a.md#New: length 2 != 3"]
    with pytest.raises(Exception):
        rows(rig, "embeddings")


@pytest.mark.asyncio
async def test_disabling_embeddings_removes_table(rig):
    rig.config.index.embed = ["fake"]
    assert await run(rig) == []
    rig.config.index.embed = None
    rig.creator = Creator()
    rig.exec.calls.clear()
    assert await run(rig) == []
    assert not rig.exec.calls
    assert rig.creator.calls == [("load", "fts"), ("create", "fts")]
    with pytest.raises(Exception):
        rows(rig, "embeddings")
