"""Shared inbox, author, retro and control scaffolding on the in-memory seams."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Shared test scaffolding on fake seams: box triage CLI runner, inbox report arrivals, bug ticket replies, retro checkout rig and control-inbox rig
# relates: [clutch/__main__.py, clutch/box.py, clutch/config.py, clutch/control.py, clutch/daemon.py, clutch/journal.py, clutch/llm.py, clutch/retro.py]
# owner: engine
# verified: ff6ac88d
# hash: 150f94b1af53c8c1afb12c7ce7810d1dec54825301650f63e1abae822adc1eb4

import asyncio
import json
from functools import cache
from pathlib import Path

import clutch.__main__ as main_module
from clutch import control, daemon, runner
from clutch.box import Box
from clutch.config import load_config_text
from clutch.control import ControlProjection, ControlRequest, publish_request
from clutch.journal import EventType
from clutch.llm import FakeLLM
from clutch.retro import Retro
from clutch.seams import LocalFileSystem
from tests.cli_helpers import ENV
from tests.config_fixture import amend_config, build_config
from tests.fakes import FakeClock, FakeExec, FakeFileSystem, FakeJournal, turn
from tests.git_fake import GitFake
from tests.loop_helpers import author_reply
from tests.stage_replies import requisition_reply


def commit_lock(state_dir):
    return asyncio.Lock()


@cache
def _state(root):
    # Separate roots stay isolated; repeated box/CLI/event calls share their seams.
    return LocalFileSystem(), FakeJournal(), GitFake()


def _box(root):
    fs, _, _ = _state(root)
    return Box(root / ".clutch/state/box", fs)


def _events(root):
    _, journal, _ = _state(root)
    return journal.read()


def _run(root, monkeypatch, llm):
    fs, journal, git = _state(root)
    with monkeypatch.context() as patch:
        patch.setattr(main_module, "ProviderLLM", lambda *args, **kwargs: llm)
        patch.setattr(main_module, "Subprocess" + "Exec", FakeExec)
        patch.setattr(main_module, "Git", lambda *args, **kwargs: git)
        patch.setattr(main_module, "Journal", lambda *args, **kwargs: journal)
        patch.setattr(main_module, "LocalFileSystem", lambda: fs)
        patch.setattr(main_module, "CommitLock", lambda *args, **kwargs: commit_lock(root))
        return main_module.main(["box", "triage"], cwd=root, env=ENV, clock=journal.clock)


def _routes(root):
    import yaml

    config = yaml.safe_load((root / "config.yaml").read_text())
    routes = config["routing"] + [{"tier": tier, "surface": surface, "candidates": [{"provider": "claude"}]} for surface in ("author", "review") for tier in ("low", "medium", "high", "max")]
    amend_config(root, routing=routes)


def rig(tmp_path, script=()):
    clock, fs, journal, git = FakeClock(), FakeFileSystem(), FakeJournal(), GitFake()
    journal.clock = clock
    repo = tmp_path / "repo"
    config = load_config_text(build_config(), path=repo / "config.yaml", cwd=repo)

    async def sleep(seconds):
        clock.advance(seconds)
        await turn()

    c = runner.Checkout(repo, config, ENV, FakeExec(), git, journal, fs, clock, sleep)
    from dataclasses import replace

    c = replace(c, control=main_module.build_control(c))
    llm = FakeLLM(list(script))
    writer = runner.bind(c, llm)
    writer.stages.driver.retry_cap = 0
    return c, writer, Retro(c, writer), llm


def raw_report(origin="player", **updates):
    data = dict(schema_version=1, origin=origin, summary="Observed scoring defect", app_commit="host-supplied-evidence", app_version="1.2.3")
    if origin == "self_diagnosed":
        data.update(game_slug="score2", anomaly_code="illegal42", location="app/view.py:123")
    return {**data, **updates}


def arrival(root, **updates):
    root.mkdir(parents=True, exist_ok=True)
    (root / "inbox").mkdir(exist_ok=True)
    (root / "replay.json").write_text(json.dumps({"initial_state": {"score": 0}, "actions": []}))
    (root / "log.txt").write_text("structured log\n")
    path = root / "inbox/a.json"
    path.write_text(json.dumps(raw_report(evidence={"replay": "replay.json", "log": "log.txt"}, **updates)))
    return path


def block(prompt, name):
    return prompt.split(f"<<clutch-data:begin {name}>>\n", 1)[1].split(f"\n<<clutch-data:end {name}>>", 1)[0]


def _failure(box):
    return box.enqueue(message_class="failure_report", origin="test", summary="current broken behavior", stage="check", outcome="gate_failed")[0]


def bug_reply(stem, *, prose=None):
    data = json.loads(author_reply(stem))
    data["ticket"] = data["ticket"].replace("kind: feature", "kind: bug")
    data["ticket"] = data["ticket"].replace("- clutch/thing.py\n\n## Goal", f"- clutch/thing.py\n- tickets/{stem}/evidence/replay.json\n\n## Goal")
    data["ticket"] = data["ticket"].replace("## Scope fence\n", "## Scope fence\n- tests/report_regression.py\n")
    data["ticket"] += "\n## Regression\n```\npython tests/report_regression.py\n```\n- carries: tests/report_regression.py\n"
    if prose is not None:
        data["ticket"] = data["ticket"].replace("`clutch/thing.py` is repaired.", prose)
    return json.dumps(data)


PROPOSAL = {"fixed_failure": "Observed café failure", "overcorrection_risk": "Rejecting useful inputs", "proposed_spec_paths": ["specs/review.md", "specs/author.md"]}


def completed(journal, sequence):
    return journal.append(EventType.EFFECT_COMPLETION, {"result": {"commit": "receipt"}}, key=f"retro/{sequence}")


def merged(journal, stem="one", commit=None):
    return journal.append(EventType.STATE_TRANSITION, {"to": "merged", "commit": commit}, ticket=stem)


def decision(id, *, life="life-1", verb="kill", hold=None, result="accepted", reason="matching lifecycle and hold identities"):
    return {"kind": control.CONTROL_DECISION, "request_id": id, "lifecycle_id": life, "verb": verb, "hold_id": hold, "decision": result, "reason": reason}


class Rig:
    def __init__(self, state, *, life="life-1"):
        self.state, self.life = state, life
        self.clock, self.fs = FakeClock(), FakeFileSystem()
        self.journal = FakeJournal(self.clock)
        self.projection = ControlProjection(life)
        self.holds, self.applications, self.changes = set(), [], []
        self.inbox = self.reconstruct()

    def apply(self, projection):
        assert any(e.body.get("decision") == "accepted" and e.body.get("lifecycle_id") == self.life for e in self.journal.read())
        self.applications.append(projection)
        if projection != self.projection:
            self.changes.append(projection)
        self.projection = projection
        self.holds.difference_update(projection.released_hold_ids)

    def reconstruct(self, apply=None):
        return daemon.control_inbox(
            journal=self.journal,
            lifecycle_id=self.life,
            holds=lambda: self.holds,
            apply=apply or self.apply,
            files=lambda: [self.state / "control/inbox" / name for name in reversed(self.fs.entries(self.state / "control/inbox"))],
            read=self.fs.read_bytes,
            known=lambda _: False,
        )

    def publish(self, id, verb="kill", hold=None, life=None):
        publish_request(self.state, ControlRequest(id, life or self.life, verb, hold), self.fs)
        return self.state / "control/inbox" / (id + ".json")

    def decisions(self):
        events = self.journal.read()
        assert all(e.type == EventType.SIGNAL and e.ticket is None and e.key is None for e in events)
        assert all(set(e.body) == set(decision("id")) for e in events)
        return [e.body for e in events]
