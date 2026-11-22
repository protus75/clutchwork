# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for stages.check_meta: it has the model fill meta headers before refreshing and committing them, skips the model when the diff is clean, and keeps the empty_purpose finding when the model does not reply
# relates: [clutch/meta.py, clutch/metafill.py, clutch/seams.py, clutch/stages.py]
# owner: engine
# verified: 10f08d74
# hash: 25f0e2d4efbf71f460835afa4b0712eddf308aae04b47631021b731bfb5974f9
# ruff: noqa: E501
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from clutch import meta, metafill, stages
from clutch.seams import LocalFileSystem
from tests.git_fake import GitFake


def test_fill_before_refresh_and_commit(tmp_path, monkeypatch):
    (tmp_path / "meta.md").write_text("spec")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/new.md").write_text("new content\n")
    body = "changed content\n"
    fields = dict(schema="clutch.meta/1.0", kind="plan", purpose="old purpose", relates=[], owner="engine", verified="12345678", hash="old")
    (tmp_path / "docs/old.md").write_text(meta.compose(fields, body, 0, ".md")[0])
    files = ["docs/new.md", "docs/old.md"]
    git = GitFake(diff_names=files, ls_files=files, rev_parse="123456789")
    driver = SimpleNamespace(journal=SimpleNamespace(read=lambda: [1, 2]))
    ctx = SimpleNamespace(
        repo=tmp_path,
        worktree=lambda stem: tmp_path,
        specs_dir=tmp_path,
        fs=LocalFileSystem(),
        git=git,
        driver=driver,
        config=SimpleNamespace(meta=SimpleNamespace(paths=[SimpleNamespace(root="docs/", kind="plan")])),
    )
    monkeypatch.setattr("clutch.specs.load_spec", lambda text: text)

    async def reply(paths, payload):
        return metafill.MetaReply(files={path: metafill.MetaEntry(purpose="model purpose", relates=[], owner="") for path in paths})

    ask = AsyncMock(side_effect=reply)
    factory = Mock(return_value=ask)
    monkeypatch.setattr(metafill, "make_ask", factory)
    ticket = SimpleNamespace(stem="work")
    # Skipping fill, filling after refresh, or failing to commit its writes breaks these assertions.
    assert asyncio.run(stages.check_meta(ctx, ticket)) == []
    factory.assert_called_once_with(driver, "spec", tmp_path, 2)
    assert ask.await_args.args[0] == files
    assert [meta.parse((tmp_path / p).read_text(), ".md")[0]["purpose"] for p in files] == ["model purpose", "model purpose"]
    assert [call for call in git.calls if call[0] == "commit"] == [("commit", (tmp_path, "clutch(work): meta"), {"only": files})]
    factory.reset_mock()
    git.calls.clear()
    # A clean diff must not ask the model again.
    assert asyncio.run(stages.check_meta(ctx, ticket)) == []
    factory.assert_not_called()
    assert not [call for call in git.calls if call[0] == "commit"]


def test_no_reply_keeps_empty_finding(tmp_path, monkeypatch):
    (tmp_path / "meta.md").write_text("spec")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/new.md").write_text("new content\n")
    files = ["docs/new.md"]
    git = GitFake(diff_names=files, ls_files=files, rev_parse="123456789")
    ctx = SimpleNamespace(
        repo=tmp_path,
        worktree=lambda stem: tmp_path,
        specs_dir=tmp_path,
        fs=LocalFileSystem(),
        git=git,
        driver=SimpleNamespace(journal=SimpleNamespace(read=lambda: [])),
        config=SimpleNamespace(meta=SimpleNamespace(paths=[SimpleNamespace(root="docs/", kind="plan")])),
    )
    monkeypatch.setattr("clutch.specs.load_spec", lambda text: text)
    ask = AsyncMock(return_value=None)
    monkeypatch.setattr(metafill, "make_ask", lambda *args: ask)
    # A failed fill must preserve the empty-purpose finding.
    findings = asyncio.run(stages.check_meta(ctx, SimpleNamespace(stem="work")))
    assert [f.message for f in findings] == ["docs/new.md: empty_purpose"]
    ask.assert_awaited_once()
