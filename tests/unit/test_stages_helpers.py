# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests for the exported names and helpers in `tests/stages_helpers.py`: constants, the repo fixture, agent, author, git and the seams used by `run`.
# relates: [clutch/llm.py, clutch/specs/__init__.py, clutch/stages.py, tests/cli_helpers.py, tests/fakes.py, tests/stage_replies.py, tests/stages_helpers.py]
# owner: engine
# verified: 0a4d026b
# hash: f78034843f533ea402987049054df115bc0c8dd8012629d637589a8331e5e7fd
import json

from clutch.llm import LLMRequest
from tests import stages_helpers as h
from tests.cli_helpers import git_fake
from tests.fakes import FakeExec, FakeJournal
from tests.stage_replies import implement_reply, review_verdict


def test_imports():
    from tests.stages_helpers import (
        CONFIG,
        ENV,
        SAMPLE_REPORT,
        SECRET,
        SNAG,
        SPECS,
        STEM,
        TICKET,
        SampleReport,
        _report_bytes,
        adopt_conduct,
        agent,
        author,
        evidence,
        git,
        implement_reply,
        repo,
        report_context,
        run,
        verdict,
    )

    assert all(
        value is not None
        for value in (
            CONFIG,
            ENV,
            SAMPLE_REPORT,
            SECRET,
            SNAG,
            SPECS,
            STEM,
            SampleReport,
            TICKET,
            _report_bytes,
            adopt_conduct,
            agent,
            author,
            evidence,
            git,
            implement_reply,
            repo,
            report_context,
            run,
            verdict,
        )
    )


def test_config():
    assert "auth: FAKE_KEY" in h.CONFIG


def test_env():
    assert h.ENV["FAKE_KEY"] == "sk-test-not-for-children"


def test_sample_report_name():
    assert h.SAMPLE_REPORT == "sample-report.json"


def test_secret():
    assert h.SECRET == "sk-test-not-for-children"


def test_snag():
    assert h.SNAG["path"] == "clutch/thing.py"


def test_stem():
    assert h.STEM == "add-thing"


def test_ticket():
    assert "`thing.py` holds the word ok." in h.TICKET.format(bypass="")


def test_sample_report():
    assert h.SampleReport(produced_by_spec_version=1, produced_at_sha="sha", entries=["entry"]).entries == ["entry"]


def test_report_bytes():
    assert json.loads(h._report_bytes())["entries"] == ["one"]


def test_adopt_conduct(tmp_path):
    (tmp_path / "config.yaml").write_text(h.CONFIG)
    paths = h.adopt_conduct(tmp_path)
    assert paths and all((tmp_path / p).is_file() for p in paths)


def test_agent(tmp_path):
    result = h.agent({"x/a": "hello"})(LLMRequest(surface="implement", rendered="", tier="medium", effort="medium", ticket=h.STEM, worktree=tmp_path))
    assert (tmp_path / "x/a").read_text() == "hello"
    assert [call[0] for call in git_fake(tmp_path).calls] == ["add", "commit"]
    assert result == implement_reply()


def test_author(repo):
    h.author(repo)
    assert (repo / "tickets" / h.STEM / "ticket.md").read_text() == h.TICKET.format(bypass="")
    assert git_fake(repo).calls[-1][1][1] == f"clutch({h.STEM}): ticket"


def test_evidence():
    assert h.evidence(head_sha="different").head_sha == "different"


def test_git(tmp_path):
    assert h.git(tmp_path, "status") == ""
    assert git_fake(tmp_path).calls[-1] == ("git_out", ("status",), {})


def test_implement_reply():
    assert h.implement_reply is implement_reply


def test_verdict():
    assert h.verdict is review_verdict


def test_repo(repo):
    assert not (repo / ".git").exists()
    assert (repo / "config.yaml").read_text() == h.CONFIG


def test_run(repo, monkeypatch):
    from clutch import stages
    from clutch.specs import Spec, SpecMeta

    real_run_stages = h.run_stages

    async def verify_seams(ctx, ticket):
        assert isinstance(ctx.exec_, FakeExec)
        assert isinstance(ctx.driver.journal, FakeJournal)
        return await real_run_stages(ctx, ticket)

    monkeypatch.setattr(h, "run_stages", verify_seams)
    spec = Spec(SpecMeta(llm_surface="implement", tier="medium", effort="medium", version="1.0"), "test", ())
    monkeypatch.setattr(stages, "_spec", lambda ctx, surface: spec)
    monkeypatch.setattr(stages, "render", lambda spec, inputs: "test prompt")
    result, llm, config = h.run(repo, [h.agent({"clutch/thing.py": "changed"}, "incomplete")])
    assert result.results["implement"].outcome == "incomplete"
    assert llm.requests[0].worktree == config.worktree_root / h.STEM
    assert (llm.requests[0].worktree / "clutch/thing.py").read_text() == "changed"


repo = h.repo
