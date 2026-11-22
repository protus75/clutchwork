# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks each shared CLI test helper in tests/cli_helpers.py: config, clock, env, root fixture, git fake, journal, ticket writer, cli wrapper and the Stages stub.
# relates: [clutch/journal.py, tests/cli_helpers.py, tests/config_fixture.py, tests/fakes.py, tests/git_fake.py]
# owner: engine
# verified: ae1a5a3b
# hash: 09f418c0a1ad36dc940c9c7f4ca4d2e191b898ace446224ec509eabd337bce8e
import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import yaml

from clutch.journal import EventType
from tests import cli_helpers as h
from tests.config_fixture import build_config
from tests.fakes import FakeClock, FakeJournal
from tests.git_fake import GitFake


def test_imports():
    from tests.cli_helpers import CONFIG, ENV, PLAN, TICKET, Clock, Stages, cli, core_config, git_fake, git_out, journal, root, ticket, with_retro_driver, write

    assert all(value is not None for value in (CONFIG, Clock, ENV, PLAN, Stages, TICKET, cli, core_config, git_fake, git_out, journal, root, ticket, with_retro_driver, write))


def test_config():
    assert h.CONFIG == build_config()


def test_clock():
    assert h.Clock is FakeClock


def test_env():
    assert h.ENV["GIT_AUTHOR_EMAIL"] == "t@t"


def test_plan():
    assert "Failure spine" in h.PLAN


def test_ticket_template():
    assert "{depends}" in h.TICKET


def test_ticket():
    assert "- earlier" in h.ticket("- earlier")


def test_root(tmp_path):
    repo = h.root.__wrapped__(tmp_path)
    assert not (repo / ".git").exists()
    assert (repo / "clutch/thing.py").read_text() == ""
    assert (repo / "config.yaml").read_text() == h.CONFIG
    assert (repo / "CLUTCH_PLAN.md").read_text() == h.PLAN
    assert (repo / ".gitignore").read_text() == ".clutch/\n"
    assert (repo / "AGENTS.md").is_file() and (repo / "CLAUDE.md").is_file()
    assert isinstance(h.git_fake(repo), GitFake)


def test_git_fake(tmp_path):
    assert h.git_fake(tmp_path) is h.git_fake(tmp_path)
    assert h.git_fake(tmp_path) is not h.git_fake(tmp_path / "other")


def test_git_out(tmp_path):
    assert h.git_out(tmp_path, "status") == ""
    assert h.git_fake(tmp_path).calls[-1] == ("git_out", ("status",), {})


def test_journal(tmp_path):
    journal = h.journal(tmp_path)
    assert isinstance(journal, FakeJournal)
    event = journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="one")
    assert journal.read() == [event]


def test_write(tmp_path):
    h.write(tmp_path, "one", "distinct")
    assert (tmp_path / "tickets/one/ticket.md").read_text() == "distinct"


def test_core_config(tmp_path):
    path = h.core_config(tmp_path, [("high", "review", ["codex"])])
    assert path == tmp_path / "config.yaml"
    assert yaml.safe_load(path.read_text())["routing"] == [{"tier": "high", "surface": "review", "candidates": [{"provider": "codex"}]}]


def test_cli(tmp_path):
    def invoke(*args, **kwargs):
        assert h.main_module.Git() is h.git_fake(tmp_path)
        assert isinstance(h.main_module.SubprocessExec(), h.FakeExec)
        return 17

    with patch.object(h.main_module, "main", side_effect=invoke) as main:
        assert h.cli(tmp_path, "view", "status") == 17
        args, kwargs = main.call_args
        assert args == (["view", "status"],)
        assert kwargs["cwd"] == tmp_path and kwargs["env"] is h.ENV
        assert isinstance(kwargs["clock"], FakeClock) and isinstance(kwargs["pipeline"], h.Stages)


def test_with_retro_driver():
    dispatch = SimpleNamespace()
    marker = object()
    with patch("clutch.runner.bind", return_value=SimpleNamespace(stages=marker)):
        assert h.with_retro_driver(object(), dispatch) is dispatch
    assert dispatch.stages is marker


def test_stages(tmp_path):
    checkout = SimpleNamespace(config=SimpleNamespace(state_dir=tmp_path), journal=FakeJournal())
    stages = h.Stages("gate_failed")
    with patch.object(h, "with_retro_driver", side_effect=lambda checkout, dispatch: dispatch):
        dispatch = stages(checkout)
    assert asyncio.run(dispatch(SimpleNamespace(stem="one"))) == "gate_failed"
    assert stages.calls == ["one"] and stages.lock_held == [False]
    assert checkout.journal.read()[0].body == {"to": "gate_failed"}
