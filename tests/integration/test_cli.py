# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Integration tests for clutch CLI verbs: ticket new and order, view status, engine run and retro, host doctor, core and docs, config migrate, and box suggest
# relates: [clutch/__init__.py, clutch/__main__.py, clutch/box.py, clutch/config.py, clutch/gates.py, clutch/git.py, clutch/hostfiles.py, clutch/journal.py]
# owner: clutch/__main__.py
# verified: 69d790e1
# hash: f8f167958c2aa6a2cdf1ee1207d1652d1d1badb57419fea9ddcf9e3f800a18d1
import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest

from clutch.__main__ import main
from clutch.git import Git
from clutch.journal import EventType, Journal
from clutch.lockfile import Lockfile, LockHeld
from clutch.runner import Refusal
from clutch.seams import SubprocessExec
from tests.cli_helpers import CONFIG, ENV, PLAN, TICKET, Clock, Stages, cli, core_config, git_fake, git_out, journal, root, ticket, with_retro_driver, write
from tests.config_fixture import build_config
from tests.misc_helpers import commit_lock

pytestmark = pytest.mark.disk_io_skip


# --- new ----------------------------------------------------------------------------------------


def test_new_templates_a_ticket_and_lints_it(root, capsys):
    assert cli(root, "ticket", "new", "add-thing") == 0
    path = root / "tickets" / "add-thing" / "ticket.md"
    text = path.read_text()
    assert "## Acceptance criteria" in text and "## Verification" in text
    assert "state: draft" in text and "state: confirmed" not in text
    assert "kind: feature" in text and "## Regression" not in text
    assert "<measurable outcome naming a check in backticks>" in text
    out = capsys.readouterr().out
    assert "tickets/add-thing/ticket.md" in out
    assert "`## Context`" in out and "`## Time budget`" in out  # lint names what is left to fill
    assert git_out(root, "status", "--porcelain", "--", "tickets").startswith("??")  # authored, not committed
    assert not (root / ".clutch").exists()  # file authorship is outside the lock fence


def test_new_kind_flag(root, capsys):
    assert cli(root, "ticket", "new", "fix-thing", "--kind", "bug") == 2
    assert not (root / "tickets/fix-thing").exists()
    (root / "out.txt").write_bytes(b"failure\x00output")
    assert cli(root, "ticket", "new", "fix-thing", "--kind", "bug", "--evidence", "out.txt") == 0
    assert (root / "tickets/fix-thing/evidence/out.txt").read_bytes() == b"failure\x00output"
    text = (root / "tickets/fix-thing/ticket.md").read_text()
    assert "kind: bug" in text and "## Regression" in text
    assert "regression_result" in text
    assert "no evidence file" not in capsys.readouterr().out
    with pytest.raises(SystemExit) as exc:
        cli(root, "ticket", "new", "unknown-kind", "--kind", "unknown")
    assert exc.value.code == 2
    assert not (root / "tickets/unknown-kind").exists()


def test_new_refuses_an_existing_stem(root, capsys):
    write(root, "add-thing", "keep me\n")
    assert cli(root, "ticket", "new", "add-thing") == 2
    assert (root / "tickets" / "add-thing" / "ticket.md").read_text() == "keep me\n"
    assert "already exists" in capsys.readouterr().err


def test_new_refuses_a_bad_stem(root, capsys):
    assert cli(root, "ticket", "new", "Bad_Stem") == 2
    assert not (root / "tickets").exists()
    assert "kebab-case" in capsys.readouterr().err


# --- status -------------------------------------------------------------------------------------


def order_ticket():
    return ticket().replace("priority: P2", "state: confirmed\nsource: human\npriority: P2")


def test_order_sets_priority(root, capsys):
    original = order_ticket()
    write(root, "first", original)
    assert cli(root, "ticket", "order", "first", "--priority", "P0") == 0
    assert (root / "tickets/first/ticket.md").read_text() == original.replace("priority: P2", "priority: P0")
    assert "priority: P0" in capsys.readouterr().out


def test_order_sets_and_clears_runs_before(root):
    original = order_ticket()
    for stem in ("first", "second", "third"):
        write(root, stem, original)
    path = root / "tickets/first/ticket.md"
    assert cli(root, "ticket", "order", "first", "--runs-before", "second") == 0
    assert path.read_text() == original.replace("## Context", "## Runs before\n- second\n\n## Context")
    assert cli(root, "ticket", "order", "first", "--runs-before", "third", "second") == 0
    assert path.read_text() == original.replace("## Context", "## Runs before\n- third\n- second\n\n## Context")
    assert cli(root, "ticket", "order", "first", "--runs-before") == 0
    assert path.read_text() == original


def test_order_refuses_invalid_and_leaves_file(root, capsys):
    original = order_ticket()
    write(root, "first", original)
    write(root, "second", original.replace("## Context", "## Runs before\n- first\n\n## Context"))
    path = root / "tickets/first/ticket.md"
    for target, message in (("second", "cycle"), ("first", "itself"), ("absent", "does not resolve")):
        assert cli(root, "ticket", "order", "first", "--runs-before", target) == 2
        assert message in capsys.readouterr().err
        assert path.read_text() == original


@pytest.mark.parametrize("state", ["running", "merged", "already_satisfied", "rejected"])
def test_order_refuses_running_settled_and_rejected(root, capsys, state, monkeypatch):
    monkeypatch.setattr("clutch.observe.lock_holder", lambda state: object())
    original = order_ticket()
    write(root, "first", original)
    journal(root).append(EventType.STATE_TRANSITION, {"to": state}, ticket="first")
    assert cli(root, "ticket", "order", "first", "--priority", "P1") == 2
    assert state in capsys.readouterr().err
    assert (root / "tickets/first/ticket.md").read_text() == original


def test_order_refuses_bad_stem_and_no_option(root, capsys):
    original = order_ticket()
    write(root, "first", original)
    for args, message in ((("Bad_Stem", "--priority", "P1"), "kebab-case"), (("absent", "--priority", "P1"), "does not exist"), (("first",), "option")):
        assert cli(root, "ticket", "order", *args) == 2
        assert message in capsys.readouterr().err
        assert (root / "tickets/first/ticket.md").read_text() == original
    assert not (root / ".clutch").exists()


def test_order_takes_no_lock(root):
    original = order_ticket()
    write(root, "first", original)
    head = git_out(root, "rev-parse", "HEAD")
    assert cli(root, "ticket", "order", "first", "--priority", "P3") == 0
    assert (root / "tickets/first/ticket.md").read_text() == original.replace("priority: P2", "priority: P3")
    assert not (root / ".clutch").exists()
    assert git_out(root, "rev-parse", "HEAD") == head
    assert git_out(root, "status", "--porcelain", "--", "tickets").startswith("??")


def test_status_on_an_empty_journal(root, capsys):
    assert cli(root, "view", "status") == 0
    out = capsys.readouterr().out
    for heading in ("merged", "in flight", "blocked", "intake", "spend"):
        assert heading in out
    assert "current-window scorecard:\n- boundary: initial\n- merged tickets: 0\n- spend: $0.00" in out
    assert "window provenance:" in out and "## Surface scorecard" in out
    assert not (root / ".clutch").exists()  # write-free: no journal, no lockfile


def test_status_projects_the_journal(root, capsys):
    j = journal(root)
    j.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="a")
    j.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="a")
    j.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="b")
    j.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket="c")
    j.append(EventType.STATE_TRANSITION, {"to": "gate_failed"}, ticket="c")
    j.append(EventType.EFFECT_COMPLETION, {"result": {}, "cost": {"usd": 0.25}}, ticket="b", key="llm/b/0/x/1/1")
    j.append(EventType.EFFECT_COMPLETION, {"result": {}, "cost": {"usd": 0.5}}, ticket="c", key="llm/c/0/x/1/1")
    j.append(EventType.SIGNAL, {"signal": "ticket_intake", "source": "human", "state": "confirmed", "new": True, "commit": "abc123"}, ticket="d")
    before = sorted(p.read_bytes() for p in (root / ".clutch").rglob("*") if p.is_file())

    assert cli(root, "view", "status") == 0
    out = capsys.readouterr().out
    section = dict(block.split("\n", 1) for block in out.strip().split("\n\n"))
    assert section["merged:"] == "1"
    assert "b" in section["interrupted (the engine stopped mid-run; reject it, or start the engine to rerun it):"]
    assert "c: gate_failed" in section["blocked:"]
    assert "d: source: human" in section["intake:"]
    assert "$0.75" in section["spend:"]
    assert "merged tickets: 1" in section["current-window scorecard:"]
    assert "spend: $0.75" in section["current-window scorecard:"]
    assert sorted(p.read_bytes() for p in (root / ".clutch").rglob("*") if p.is_file()) == before


def test_status_is_deterministic(root, capsys):
    j = journal(root)
    for stem in ("z", "a", "m"):
        j.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket=stem)
    cli(root, "view", "status")
    first = capsys.readouterr().out
    cli(root, "view", "status")
    assert capsys.readouterr().out == first
    assert "merged:\n3\n" in first
    assert "- merged tickets: 3\n" in first


def test_status_escape_projection(tmp_path, monkeypatch, capsys):
    from clutch.__main__ import _status
    from clutch.retro import RetroArtifact, production_evidence, project_window, render_report
    from clutch.status import render
    from tests.loop_helpers import escape_report, escape_rig

    async def setup():
        c, _, _, _, admitted = await escape_rig(tmp_path)
        c, _, _ = await escape_report(c, commit=admitted.commit)
        status = await _status(c)
        window = project_window(c.journal.read())
        evidence = await production_evidence(window, c)
        return c, status, window, evidence

    c, status, window, evidence = asyncio.run(setup())
    before = c.journal.read()

    def forbidden(*args, **kwargs):
        pytest.fail("status escape rendering read or mutated state")

    with monkeypatch.context() as patch:
        for target, method in ((c.fs, "write"), (c.journal, "read"), (c.journal, "append"), (c.git, "_run"), (Path, "read_text"), (Path, "read_bytes")):
            patch.setattr(target, method, forbidden)
        text = render(status)
        receipt = render_report(window, evidence, {}, [], RetroArtifact(proposals=[]))
        assert text.split("| Surface |")[1] == receipt.split("| Surface |")[1]
        assert "| review | 1 | 0 | 1 | 0 | 0.0000 | 1.0000 | false |" in text
    assert c.journal.read() == before
    assert main(["view", "status"], cwd=c.repo, env=ENV, clock=c.clock) == 0
    output = capsys.readouterr().out
    assert output.split("| Surface |")[1] == text.split("| Surface |")[1]
    assert c.journal.read() == before


# --- run ----------------------------------------------------------------------------------------


def test_run_logs_lifecycle_on_merge(root):
    import json

    write(root, "add-thing", ticket())
    assert cli(root, "engine", "run", "add-thing", stages=Stages()) == 0
    events = [json.loads(line) for line in (root / ".clutch/state/engine.log").read_text().splitlines()]
    assert [(e["event"], e["verb"], e["pid"], e.get("outcome")) for e in events if e["event"] in {"engine_start", "engine_stop"}] == [
        ("engine_start", "run", os.getpid(), None),
        ("engine_stop", "run", os.getpid(), "merged"),
    ]


def test_run_dispatches_the_locked_validated_stem_to_the_stage_seam(root):
    write(root, "add-thing", ticket())
    stages = Stages()
    assert cli(root, "engine", "run", "add-thing", stages=stages) == 0
    assert stages.calls == ["add-thing"]
    assert stages.lock_held == [True]  # the one process holding the lock is the one dispatching
    assert git_out(root, "status", "--porcelain") == ""  # intake committed the ticket before dispatch
    assert "clutch(add-thing): ticket" in git_out(root, "log", "--format=%s")
    events = [(e.type, e.ticket, e.body.get("to")) for e in journal(root).read()]
    assert (EventType.STATE_TRANSITION, "add-thing", "running") in events
    assert events.index((EventType.STATE_TRANSITION, "add-thing", "running")) < events.index((EventType.STATE_TRANSITION, "add-thing", "merged"))
    Lockfile(root / ".clutch" / "state", verb="drain", instance_id="after", clock=Clock()).acquire()  # released on exit


def test_run_exits_1_on_a_non_ok_terminal(root):
    write(root, "add-thing", ticket())
    assert cli(root, "engine", "run", "add-thing", stages=Stages("gate_failed")) == 1
    assert (root / "tickets" / "add-thing" / "ticket.md").is_file()


def test_run_refused_when_the_lockfile_is_already_held(root, capsys):
    write(root, "add-thing", ticket())
    holder = Lockfile(root / ".clutch" / "state", verb="drain", instance_id="other", clock=Clock())
    holder.acquire()
    try:
        stages = Stages()
        assert cli(root, "engine", "run", "add-thing", stages=stages) == 2
    finally:
        holder.release()
    assert stages.calls == []
    assert "other" in capsys.readouterr().err  # the holder identity names who to wait for
    assert git_out(root, "status", "--porcelain").startswith("??")  # intake never ran: nothing committed
    assert journal(root).read() == []


def test_run_refuses_an_invalid_ticket(root, capsys):
    write(root, "add-thing", ticket().replace("## Verification", "## Verify"))
    stages = Stages()
    assert cli(root, "engine", "run", "add-thing", stages=stages) == 2
    assert stages.calls == []
    assert "ticket_schema" in capsys.readouterr().err
    assert not any(e.type == EventType.STATE_TRANSITION for e in journal(root).read())


def test_run_refuses_a_missing_stem(root, capsys):
    stages = Stages()
    assert cli(root, "engine", "run", "no-such", stages=stages) == 2
    assert stages.calls == []
    assert "new no-such" in capsys.readouterr().err


def test_run_refuses_an_unmerged_dependency(root, capsys):
    write(root, "first", ticket())
    write(root, "second", ticket(depends="- first"))
    stages = Stages()
    assert cli(root, "engine", "run", "second", stages=stages) == 2
    assert stages.calls == []
    assert "run first" in capsys.readouterr().err
    assert cli(root, "engine", "run", "first", stages=stages) == 0
    assert cli(root, "engine", "run", "second", stages=stages) == 0
    assert stages.calls == ["first", "second"]


def test_run_refuses_a_merged_ticket(root, capsys):
    write(root, "add-thing", ticket())
    stages = Stages()
    assert cli(root, "engine", "run", "add-thing", stages=stages) == 0
    assert cli(root, "engine", "run", "add-thing", stages=stages) == 2
    assert stages.calls == ["add-thing"]
    assert "merged" in capsys.readouterr().err


def test_run_refused_before_the_lock_when_the_pipeline_refuses(root, capsys):
    def unbuilt(checkout):
        raise Refusal("pipeline missing", "build it")

    write(root, "add-thing", ticket())
    assert main(["engine", "run", "add-thing"], cwd=root, env=ENV, clock=Clock(), pipeline=unbuilt) == 2
    assert "pipeline missing -- build it" in capsys.readouterr().err
    assert journal(root).read() == []


def test_config_error_exits_2(root, capsys):
    (root / "config.yaml").write_text("schema_version: 1\n")
    assert cli(root, "view", "status") == 2
    assert "config.yaml" in capsys.readouterr().err


# --- module entry -------------------------------------------------------------------------------


def test_python_dash_m_clutch_is_the_entry(root):
    env = {**ENV, "PYTHONPATH": str(Path(__file__).resolve().parents[2])}
    proc = subprocess.run([sys.executable, "-m", "clutch", "view", "status"], cwd=root, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "merged:" in proc.stdout
    proc = subprocess.run([sys.executable, "-m", "clutch", "bogus"], cwd=root, env=env, capture_output=True, text=True)
    assert proc.returncode == 2


def test_project_declares_build_and_console_script():
    import tomllib

    pyproject = tomllib.loads((Path(__file__).resolve().parents[2] / "pyproject.toml").read_text())
    assert pyproject["build-system"]["build-backend"] == "uv_build"  # A virtual project cannot build a wheel.
    assert pyproject["project"]["scripts"]["clutch"] == "clutch.__main__:main"  # The installed command must invoke the CLI.


def released(root):
    lock = Lockfile(root / ".clutch/state", verb="drain", instance_id="after", clock=Clock())
    lock.acquire()
    lock.release()


@pytest.mark.parametrize("completed_report", [False, True])
def test_retro_no_merge(root, capsys, completed_report):
    if completed_report:
        journal(root).append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="one")
        assert cli(root, "engine", "retro") == 0
        capsys.readouterr()

    def factory(c):
        class Dispatch:
            async def prepare(self):
                pytest.fail("unselected pipeline prepared")

            async def __call__(self, ticket):
                pytest.fail("ticket dispatched")

        return Dispatch()

    head = git_out(root, "rev-parse", "HEAD")
    assert cli(root, "engine", "retro", stages=factory) == 0
    assert capsys.readouterr().out == "retro: no merge since the latest completed report\n"
    assert git_out(root, "rev-parse", "HEAD") == head
    assert (root / "tickets/retro").exists() == completed_report
    released(root)


def test_retro_success(root, capsys, monkeypatch):
    import clutch.__main__ as module
    from clutch import runner
    from clutch.llm import FakeLLM
    from clutch.retro import Retro, project_window

    llm = FakeLLM(['{"proposals": []}'])
    config = root / "config.yaml"
    config.write_text(config.read_text().replace("review: {}", "  - {tier: medium, surface: retro, candidates: [{provider: claude}]}\nreview: {}"))
    seen = []
    from clutch.providers import ProviderLLM

    async def preflight(self):
        contender = Lockfile(self._config.state_dir, verb="drain", instance_id="other", clock=Clock())
        with pytest.raises(LockHeld):
            contender.acquire()
        seen.append(self.session)
        return []

    async def call(self, request, served, **kwargs):
        contender = Lockfile(self._config.state_dir, verb="drain", instance_id="model", clock=Clock())
        with pytest.raises(LockHeld):
            contender.acquire()
        return await llm.call(request)

    monkeypatch.setattr(ProviderLLM, "preflight", preflight)
    monkeypatch.setattr(ProviderLLM, "_invoke", call)
    original = Retro.__call__

    async def invoke(self, *, forced=False):
        assert forced
        driver = self.driver()
        assert isinstance(driver.llm, ProviderLLM)
        assert driver.llm.session is self.checkout.control.providers is seen[0]
        return await original(self, forced=forced)

    monkeypatch.setattr(Retro, "__call__", invoke)
    journal(root).append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="one")
    assert module.main(["engine", "retro"], cwd=root, env=ENV, clock=Clock()) == 0
    assert capsys.readouterr().out == "retro: committed tickets/retro/000001.md\n"
    assert len(llm.requests) == 1
    assert project_window(journal(root).read()).boundary == "retro/1"
    completion = next(e for e in journal(root).read() if e.key == "retro/1" and e.type == EventType.EFFECT_COMPLETION)
    assert completion.body == {"result": {"commit": git_out(root, "rev-parse", "HEAD").strip()}}
    assert git_out(root, "show", "--format=", "--name-only", "HEAD").splitlines() == ["tickets/retro/000001.md"]
    released(root)


@pytest.mark.parametrize("suppressed, later_merge", [(False, False), (True, False), (True, True)])
def test_retro_no_commit(root, capsys, monkeypatch, suppressed, later_merge):
    from clutch import runner
    from clutch.llm import FakeLLM

    llm = FakeLLM([RuntimeError("failed")])
    j = journal(root)
    j.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="one")
    if suppressed:
        j.append(EventType.SIGNAL, {"kind": "retro_failed", "window_boundary": "initial"}, key="retro-failed/initial/forced")

    def factory(c):
        writer = runner.bind(c, llm)
        writer.stages.driver.retry_cap = 0
        return writer

    prepared = []
    if later_merge:
        j.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="later")

        async def prepare(c):
            prepared.append(c)
            return factory(c)

        monkeypatch.setattr(runner, "prepare_pipeline", prepare)
    head = git_out(root, "rev-parse", "HEAD")
    if suppressed and not later_merge:

        async def forbidden(c):
            pytest.fail("suppressed retro prepared providers")

        monkeypatch.setattr(runner, "prepare_pipeline", forbidden)
        assert main(["engine", "retro"], cwd=root, env=ENV, clock=Clock()) == 1
    elif later_merge:
        assert main(["engine", "retro"], cwd=root, env=ENV, clock=Clock()) == 1
        assert len(prepared) == 1
    else:
        assert cli(root, "engine", "retro", stages=factory) == 1
    assert git_out(root, "rev-parse", "HEAD") == head
    assert capsys.readouterr().out == "retro: no report committed; inspect status and the Suggestion Box\n"
    assert len(llm.requests) == (0 if suppressed and not later_merge else 1)
    assert not (root / "tickets/retro").exists()
    released(root)


@pytest.mark.parametrize("failure", ["lock", "config", "journal", "driver", "prepare"])
def test_retro_refusals(root, capsys, failure):
    j = journal(root)
    j.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="one")
    holder = Lockfile(root / ".clutch/state", verb="drain", instance_id="other", clock=Clock())
    if failure == "lock":
        holder.acquire()
    elif failure == "config":
        (root / "config.yaml").write_text("schema_version: 1\n")
    elif failure == "journal":
        next(j.dir.glob("*.jsonl")).write_bytes(b"bad\n")

    def factory(c):
        class Dispatch:
            async def prepare(self):
                if failure == "prepare":
                    raise Refusal("preflight failed", "repair provider and retry")

            async def __call__(self, ticket):
                pytest.fail("dispatched")

        return Dispatch()

    try:
        assert cli(root, "engine", "retro", stages=factory) == 2
        err = capsys.readouterr().err
        assert "Traceback" not in err
        if failure == "lock":
            assert "retry after the running engine publishes" in err
        assert {"lock": "current control identity unavailable", "config": "repair", "journal": "never hand-edited", "driver": "construct the pipeline", "prepare": "repair provider"}[failure] in err
    finally:
        if holder.held:
            holder.release()
    released(root)


def test_doctor_cli(root, capsys):
    assert cli(root, "host", "doctor", stages=lambda c: pytest.fail("pipeline constructed")) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "doctor: ok"
    assert [line.split(":", 1)[0] for line in lines[1:]] == [f"PASS {n}" for n in ("venv", "config", "git", "lock", "journal", "core")]


@pytest.mark.parametrize(
    "routes, expected",
    [
        ([("medium", "implement", ["claude"])], {"CLAUDE.md"}),
        ([("medium", "implement", ["codex"])], {"AGENTS.md"}),
        ([("medium", "implement", ["claude", "codex"])], {"CLAUDE.md", "AGENTS.md"}),
        ([("medium", "implement", ["codex", "codex", "claude"]), ("high", "review", ["claude", "codex"])], {"CLAUDE.md", "AGENTS.md"}),
    ],
)
def test_core_routed_conduct_files(tmp_path, monkeypatch, routes, expected):
    import clutch.__main__ as module
    from clutch import hostfiles
    from tests.integration.test_hostfiles import RecordingFS

    core_config(tmp_path, routes)
    fs = RecordingFS()
    monkeypatch.setattr(module, "LocalFileSystem", lambda: fs)
    assert cli(tmp_path, "host", "core") == 0
    assert {p.name for p, _ in fs.writes} == expected
    assert len(fs.writes) == len(expected)
    for name in ("CLAUDE.md", "AGENTS.md"):
        path = tmp_path / name
        assert path.exists() == (name in expected)
        if path.exists():
            assert path.read_bytes() == hostfiles.render(b"")
    assert cli(tmp_path, "host", "core") == 0
    assert len(fs.writes) == len(expected)
    assert not (tmp_path / ".clutch").exists()


def test_core_refusal_and_no_git(tmp_path, monkeypatch, capsys):
    import clutch.__main__ as module
    from clutch import gates, hostfiles
    from clutch.seams import LocalFileSystem

    config = core_config(tmp_path, [("medium", "implement", ["claude", "codex"])])
    clean, corrupt = tmp_path / "CLAUDE.md", tmp_path / "AGENTS.md"
    project = b"# Project\r\nkeep every byte"
    clean.write_bytes(project)
    corrupt.write_bytes(b"project\n<!-- clutch:core beg")
    before = {p: p.read_bytes() for p in tmp_path.iterdir()}

    def forbidden(*args, **kwargs):
        pytest.fail("core constructed git, journal, provider, pipeline, or gate work")

    for name in ("Git", "Journal", "SubprocessExec", "ProviderLLM", "ProviderSession", "build_control"):
        monkeypatch.setattr(module, name, forbidden)
    monkeypatch.setattr(gates, "run_gates", forbidden)
    replacements = []
    original_replace = os.replace

    def observe_replace(src, dst):
        src, dst = Path(src), Path(dst)
        assert src.parent == dst.parent
        assert src.name == f".{dst.name}.tmp"
        assert src.read_bytes() == hostfiles.render(before[dst])
        assert dst.read_bytes() == before[dst]
        replacements.append(dst)
        original_replace(src, dst)

    monkeypatch.setattr(os, "replace", observe_replace)
    monkeypatch.setattr(module, "LocalFileSystem", LocalFileSystem)
    assert main(["--config", str(config), "host", "core"], cwd=tmp_path, env=ENV, pipeline=forbidden) == 2
    assert replacements == []
    assert {p: p.read_bytes() for p in tmp_path.iterdir()} == before
    error = capsys.readouterr().err
    assert "repair" in error and "retain all project content" in error and "retry host core" in error
    # The paved road escapes marker-like project text without deleting its content.
    repaired = before[corrupt].replace(b"clutch:core", b"clutch&#58;core")
    corrupt.write_bytes(repaired)
    before[corrupt] = repaired
    assert main(["host", "core"], cwd=tmp_path, env=ENV, pipeline=forbidden) == 0
    assert replacements == [clean, corrupt]
    assert clean.read_bytes() == hostfiles.render(project)
    assert corrupt.read_bytes() == hostfiles.render(repaired)
    assert main(["host", "core"], cwd=tmp_path, env=ENV, pipeline=forbidden) == 0
    assert replacements == [clean, corrupt]
    assert {p.name for p in tmp_path.iterdir()} == {"config.yaml", "CLAUDE.md", "AGENTS.md"}


@pytest.mark.parametrize("explicit", [False, True])
def test_migrate_config_before_load(tmp_path, monkeypatch, capsys, explicit):
    import clutch.__main__ as module
    from clutch.providers import ProviderLLM
    from tests.config_helpers import MigrationFS

    directory = tmp_path / "elsewhere" if explicit else tmp_path
    directory.mkdir(exist_ok=True)
    path = directory / ("host.yaml" if explicit else "config.yaml")
    original = CONFIG.replace("schema_version: 1", "schema_version: 0").encode()
    path.write_bytes(original)
    if explicit:
        (tmp_path / "config.yaml").write_bytes(b"unselected invalid config")
    fs = MigrationFS()
    monkeypatch.setattr(module, "LocalFileSystem", lambda: fs)

    def forbidden(*args, **kwargs):
        pytest.fail("migration invoked git, process, provider, journal, or pipeline work")

    for name in ("Git", "Journal", "SubprocessExec", "ProviderLLM", "ProviderSession", "build_control"):
        monkeypatch.setattr(module, name, forbidden)
    monkeypatch.setattr(ProviderLLM, "call", forbidden)
    args = (["--config", str(path)] if explicit else []) + ["config", "migrate"]
    assert main(args, cwd=tmp_path, env=ENV, pipeline=forbidden) == 0
    backup = path.with_name(path.name + ".bak")
    expected = CONFIG.encode()
    assert fs.writes == [(backup, original), (path, expected)]
    assert path.read_bytes() == expected
    assert backup.read_bytes() == original
    assert main(args, cwd=tmp_path, env=ENV, pipeline=forbidden) == 0
    assert len(fs.writes) == 2
    assert path.read_bytes() == expected and backup.read_bytes() == original
    path.write_bytes(original + b"caps: {retry: 7}\n")
    before = path.read_bytes()
    assert main(args, cwd=tmp_path, env=ENV, pipeline=forbidden) == 2
    assert "caps.retry" in capsys.readouterr().err
    assert len(fs.writes) == 2
    assert path.read_bytes() == before and backup.read_bytes() == original
    assert not (tmp_path / ".clutch").exists()
    if explicit:
        assert (tmp_path / "config.yaml").read_bytes() == b"unselected invalid config"


def test_core_and_gate_share_routed_paths(tmp_path, monkeypatch):
    from clutch import __main__ as module
    from clutch import hostfiles, providers
    from clutch.config import load_config
    from tests.integration.test_hostfiles import RecordingFS
    from tests.stages_helpers import evidence

    config_path = core_config(tmp_path, [("medium", "implement", ["codex", "claude", "codex"])])
    config = load_config(config_path, cwd=tmp_path)
    resolver = providers.routed_conduct_paths
    calls = []

    def resolved(config, root):
        paths = resolver(config, root)
        calls.append(paths)
        return paths

    monkeypatch.setattr(providers, "routed_conduct_paths", resolved)
    monkeypatch.setattr(module, "routed_conduct_paths", resolved)
    project = b"# project\r\nbytes\xff without newline"
    for path in resolver(config, tmp_path):
        path.write_bytes(project)
    fs = RecordingFS()
    monkeypatch.setattr(module, "LocalFileSystem", lambda: fs)
    assert cli(tmp_path, "host", "core") == 0
    assert cli(tmp_path, "host", "core") == 0
    g = Git(SubprocessExec(), env=ENV, timeout=30, commit_lock=commit_lock(tmp_path / ".clutch/state"))

    async def check():
        await g.init(tmp_path, branch="main")
        await g.add(tmp_path, ["config.yaml", "CLAUDE.md", "AGENTS.md"])
        await g.commit(tmp_path, "mechanical adoption")
        gathered = await hostfiles.committed_core(tmp_path, config, g)
        assert hostfiles.CoreDriftGate().check(evidence(**gathered), tmp_path).verdict == "pass"

    asyncio.run(check())
    assert calls == [resolver(config, tmp_path)] * 3
    assert len(fs.writes) == 2
    for path in resolver(config, tmp_path):
        assert hostfiles.parse(path.read_bytes()) == (b"", b"\n\n" + project)
    before = {p: p.read_bytes() for p in resolver(config, tmp_path)}
    damaged = tmp_path / "CLAUDE.md"
    damaged.write_bytes(before[damaged] + b"stray clutch:core")
    corrupt = {p: p.read_bytes() for p in before}
    assert cli(tmp_path, "host", "core") == 2
    assert {p: p.read_bytes() for p in before} == corrupt and len(fs.writes) == 2

    async def refusal():
        await g.add(tmp_path, ["CLAUDE.md"])
        await g.commit(tmp_path, "committed marker refusal")
        gathered = await hostfiles.committed_core(tmp_path, config, g)
        report = hostfiles.CoreDriftGate().check(evidence(**gathered), tmp_path)
        [finding] = report.findings
        assert finding.path == "CLAUDE.md" and "retain all project content" in finding.paved_road

    asyncio.run(refusal())


def test_suggest_publishes_while_writer_lock_is_held(root, capsys):
    from clutch.box import Box
    from clutch.seams import LocalFileSystem

    holder = Lockfile(root / ".clutch/state", verb="drain", instance_id="other", clock=Clock())
    holder.acquire()
    try:
        assert cli(root, "box", "suggest", "a distinct idea") == 0
        messages = Box(root / ".clutch/state/box", LocalFileSystem()).messages()
        assert len(messages) == 1
        message = messages[0]
        assert (message.message_class, message.status, message.summary, message.origin) == ("suggestion", "pending", "a distinct idea", "session")
        assert capsys.readouterr().out == f"suggest: filed {message.id}\n"
        assert not (root / ".clutch/state/box/suggestions").exists()
    finally:
        holder.release()


def test_suggest_duplicate(root, capsys):
    from clutch.box import Box
    from clutch.seams import LocalFileSystem

    assert cli(root, "box", "suggest", "a distinct idea") == 0
    assert cli(root, "box", "suggest", "a distinct idea") == 0
    messages = Box(root / ".clutch/state/box", LocalFileSystem()).messages()
    assert len(messages) == 1
    assert capsys.readouterr().out.splitlines() == [f"suggest: filed {messages[0].id}", f"suggest: already in the box as {messages[0].id}"]


def test_suggest_refuses_blank(root, capsys):
    assert cli(root, "box", "suggest", "  ") == 2
    assert capsys.readouterr().err == "clutch box: blank summary -- pass the idea as one quoted argument\n"
    from clutch.box import Box
    from clutch.seams import LocalFileSystem

    assert Box(root / ".clutch/state/box", LocalFileSystem()).messages() == []


def test_docs_reports_installed_guides(root, capsys):
    import clutch

    assert cli(root, "host", "docs") == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 6
    package = Path(clutch.__file__).parent
    for line, name in zip(lines, ("authoring", "running", "contract", "qwen", "antigravity", "training"), strict=True):
        path_text, purpose = line.split("  ")
        path = Path(path_text)
        assert path == package / "docs" / f"host-{name}.md"
        assert path.is_absolute() and path.is_file()
        assert path.is_relative_to(package) and not path.is_relative_to(root)
        assert "://" not in path_text and purpose
