import pytest
from pydantic import TypeAdapter, ValidationError

from clutch import box, git, llm, tickets
from clutch.artifacts import is_repo_relative
from clutch.author import AuthorReply


def test_author_reply_keeps_final_newline():
    assert AuthorReply(stem="s", ticket="x\n").ticket == "x\n"
    with pytest.raises(ValidationError):
        AuthorReply(stem="s", ticket=" \n")


@pytest.mark.parametrize("value,expected", [("", False), ("  ", False), ("/a", False), ("a/../b", False), ("a\\b", False), ("a\0b", False), ("a/b", True), ("tickets/x/", True)])
def test_is_repo_relative(value, expected):
    assert is_repo_relative(value) is expected
    if value == "a\\b":
        with pytest.raises(ValidationError):
            TypeAdapter(box.RepoPath).validate_python(value)


def test_blob_sha():
    assert git.blob_sha(b"hello\n") == "ce013625030ba8dba906f756967f9e9ca394464a"


def test_owner_constants():
    assert llm.TIERS == ("low", "medium", "high", "max")
    assert tickets.PRIORITIES == ("P0", "P1", "P2", "P3")
    assert tickets.KINDS == ("feature", "bug", "chore")
    for field, value in (("kind", "graphics"), ("priority", "P4")):
        data = dict(state="draft", source="human", priority="P1", kind="bug")
        data[field] = value
        with pytest.raises(ValidationError) as exc:
            tickets.Frontmatter(**data)
        assert field in str(exc.value)
    with pytest.raises(ValueError):
        tickets.template("graphics")


def test_inbox_paths_reject_traversal():
    from clutch.inbox import EvidencePaths, PlayerReport

    assert EvidencePaths(replay="traces/run.log").replay == "traces/run.log"
    with pytest.raises(ValidationError):
        EvidencePaths(replay="../run.log")
    with pytest.raises(ValidationError):
        PlayerReport(schema_version=1, origin="player", summary="failure", app_commit="abc", app_version="v1", implicated_paths=["../outside"])


def test_baseline_rejects_missing_identity():
    from pathlib import Path

    from clutch.baseline import _matches

    assert _matches(None, {}, Path("unused")) is False
