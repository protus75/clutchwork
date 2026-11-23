# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Check stage fills a drifted metadata purpose through a scripted model call and commits the rewrite as a clutch(<stem>): meta commit
# relates: [clutch/driver.py, clutch/gates.py, clutch/llm.py, clutch/meta.py, clutch/redact.py, clutch/stages.py, tests/fakes.py, tests/git_fake.py]
# owner: engine
# verified: 9dc8c407
# hash: f64f6a21f5fea6ac5bff7537b9b6ce6082bb119b9ebb3d1ea139d5ca02332817
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from clutch import meta, stages
from clutch.driver import Driver, Spool
from clutch.gates import merge_severity
from clutch.llm import FakeLLM
from clutch.redact import Redactor
from tests.fakes import FakeClock, FakeFileSystem, FakeJournal
from tests.git_fake import GitFake


def test_check_fills_meta_inside_check_stage(monkeypatch):
    root = Path("/work/work")
    path = "docs/edited.md"
    fs = FakeFileSystem()
    fields = dict(schema="clutch.meta/1.0", kind="plan", purpose="", relates=[], owner="engine", verified="12345678", hash="stale")
    fs.write(root / path, meta.compose(fields, "edited body\n", 0, ".md")[0].encode())
    git = GitFake(diff_names=[path], ls_files=[path], rev_parse="123456789")
    clock = FakeClock()
    redactor = Redactor({})
    log = SimpleNamespace(event=lambda *args, **kwargs: None)
    llm = FakeLLM([json.dumps({"files": {path: {"purpose": "scripted purpose", "relates": [], "owner": ""}}})])
    driver = Driver(
        llm=llm, journal=FakeJournal(clock), redactor=redactor, spool=Spool(Path("/state"), redactor, fs), log=log, clock=clock, sleep=asyncio.sleep, severity=merge_severity(None), retry_cap=0
    )
    config = SimpleNamespace(meta=SimpleNamespace(paths=[SimpleNamespace(root="docs/", kind="plan")]), review=SimpleNamespace(autofix=[]))
    ctx = SimpleNamespace(repo=Path("/repo"), worktree=lambda stem: root, specs_dir=Path(__file__).resolve().parents[2] / "clutch/specs", fs=fs, git=git, driver=driver, config=config)
    ticket = SimpleNamespace(stem="work", frontmatter=SimpleNamespace(kind="feature", gate_bypass=[], source="human"), sections={}, verification=[])
    evidence = stages.Evidence(stem="work", head_sha="abc", claimed="ok", scope_fence=[], changed_files=[path], inserted_lines=0, verification=[], run_record=None)
    monkeypatch.setattr(stages, "gather_evidence", AsyncMock(return_value=evidence))
    monkeypatch.setattr(stages, "check_hosts", AsyncMock(return_value=([], [])))
    monkeypatch.setattr(stages, "lift_outbox", AsyncMock())
    monkeypatch.setattr(stages, "CHECK_GATES", ())
    result = asyncio.run(stages.check(ctx, ticket, SimpleNamespace(outcome="ok"), attempt=1))
    assert result.outcome == "ok"
    assert meta.parse(fs.read_bytes(root / path).decode(), ".md")[0]["purpose"] == "scripted purpose"
    assert ("commit", (root, "clutch(work): meta"), {"only": [path]}) in git.calls
