# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Metadata refresh and drift findings during check
# relates: [clutch/gates.py, clutch/meta.py, clutch/seams.py, clutch/stages.py]
# owner: engine
# verified: abdfb3f9
# hash: 9f80e41a2abc3513c544205cfabd366b52716edf7977fae1eb2a95a85a339e3b
import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from clutch import meta, metafill, stages
from clutch.gates import merge_severity
from clutch.seams import LocalFileSystem


def setup(tmp_path, files, changed, paths=True):
    for path, data in files.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data)
    git = SimpleNamespace(diff_names=AsyncMock(return_value=changed), ls_files=AsyncMock(return_value=list(files)), rev_parse=AsyncMock(return_value="123456789"), commit=AsyncMock())
    config = SimpleNamespace(meta=SimpleNamespace(paths=[SimpleNamespace(root="docs/", kind="plan")] if paths else []), review=SimpleNamespace(autofix=[]))
    (tmp_path / "meta.md").write_text("fake spec")
    driver = SimpleNamespace(journal=SimpleNamespace(read=lambda: []))
    return SimpleNamespace(driver=driver, specs_dir=tmp_path, repo=tmp_path, worktree=lambda stem: tmp_path, fs=LocalFileSystem(), git=git, config=config), SimpleNamespace(stem="work")


def block(body, purpose, stale=False):
    fields = dict(schema="clutch.meta/1.0", kind="plan", purpose=purpose, relates=[], owner="engine", verified="12345678", hash="stale" if stale else meta.digest(body))
    return meta.compose(fields, body, 0, ".md")[0]


def test_refresh_reasons_commit_and_repeat(tmp_path, monkeypatch):
    monkeypatch.setattr("clutch.specs.load_spec", lambda text: text)

    async def ask(paths, payload):
        return metafill.MetaReply(files={p: metafill.MetaEntry(purpose="filled purpose", relates=[], owner="") for p in paths})

    monkeypatch.setattr(metafill, "make_ask", lambda *args: ask)
    files = {
        "docs/new.md": "new\n",
        "docs/old.md": block("old\n", "old purpose", True),
        "docs/bad.md": "<!-- clutch:meta\nbad\n-->\n",
        "docs/ok.md": block("ok\n", "ok purpose"),
        "docs/empty.md": block("empty\n", "", True),
    }
    ctx, ticket = setup(tmp_path, files, list(files))
    findings = asyncio.run(stages.check_meta(ctx, ticket))
    assert {f.message for f in findings} == {"docs/bad.md: malformed"}
    assert len(findings) == 1
    assert (tmp_path / "docs/bad.md").read_text() == files["docs/bad.md"]
    ctx.git.commit.assert_awaited_once_with(tmp_path, "clutch(work): meta", only=["docs/empty.md", "docs/new.md", "docs/old.md"])
    for path in ["docs/new.md", "docs/old.md", "docs/empty.md"]:
        fields, body, _ = meta.parse((tmp_path / path).read_text(), ".md")
        assert fields["hash"] == meta.digest(body)
    ctx.git.commit.reset_mock()
    again = asyncio.run(stages.check_meta(ctx, ticket))
    assert "docs/old.md: purpose_unverified" not in [f.message for f in again]
    ctx.git.commit.assert_not_awaited()


def test_ignores_unrelated_and_deleted(tmp_path):
    files = {"docs/untouched.md": "untouched\n", "docs/stale.md": block("stale\n", "purpose", True), "src/a.py": "a = 1\n", "tickets/work/a.md": "ticket\n"}
    ctx, ticket = setup(tmp_path, files, ["src/a.py", "tickets/work/a.md", "docs/deleted.md"])
    assert asyncio.run(stages.check_meta(ctx, ticket)) == []
    ctx.git.commit.assert_not_awaited()
    assert {path: (tmp_path / path).read_text() for path in files} == files
    ctx.git.ls_files.assert_not_awaited()
    ctx.config.meta.paths.append(SimpleNamespace(root="tickets/", kind="plan"))
    ctx.git.diff_names.return_value = ["tickets/work/a.md"]
    assert asyncio.run(stages.check_meta(ctx, ticket)) == []
    ctx.git.ls_files.assert_not_awaited()
    assert (tmp_path / "tickets/work/a.md").read_text() == files["tickets/work/a.md"]


@pytest.mark.parametrize("setting,outcome,verdict", [(None, "ok", "fail"), ("hard", "gate_failed", "fail"), ("disabled", "ok", None)])
def test_check_outcome(tmp_path, monkeypatch, setting, outcome, verdict):
    ctx, ticket = setup(tmp_path, {"docs/new.md": "body\n"}, ["docs/new.md"], paths=setting != "disabled")
    ticket.frontmatter = SimpleNamespace(kind="feature", gate_bypass=[], source="human")
    ticket.verification = []
    ticket.sections = {}
    monkeypatch.setattr("clutch.specs.load_spec", lambda text: text)
    monkeypatch.setattr(metafill, "make_ask", lambda *args: AsyncMock(return_value=None))
    ctx.driver = SimpleNamespace(journal=SimpleNamespace(read=lambda: []), clock=lambda: datetime(2020, 1, 1, tzinfo=timezone.utc), provider_wait=lambda *args: 0, severity=merge_severity(None))
    if setting == "hard":
        ctx.driver.severity["meta_drift"] = "hard"
    item = stages.Evidence(stem="work", head_sha="abc", claimed="ok", scope_fence=[], changed_files=["docs/new.md"], inserted_lines=0, verification=[], run_record=None)
    monkeypatch.setattr(stages, "gather_evidence", AsyncMock(return_value=item))
    monkeypatch.setattr(stages, "check_hosts", AsyncMock(return_value=([], [])))
    monkeypatch.setattr(stages, "lift_outbox", AsyncMock())
    monkeypatch.setattr(stages, "CHECK_GATES", ())
    result = asyncio.run(stages.check(ctx, ticket, SimpleNamespace(outcome="ok"), attempt=1))
    reports = [r for r in result.artifact.reports if r.code == "meta_drift"]
    assert result.outcome == outcome
    assert result.artifact.passed == (outcome == "ok")
    assert [r.verdict for r in reports] == ([verdict] if verdict else [])
    if setting == "disabled":
        ctx.git.commit.assert_not_awaited()
