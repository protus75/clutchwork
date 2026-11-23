"""Release acceptance uses real temporary files and a scripted, gate-aware driver."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Tests the `clutch roadmap accept` release check with temporary files and a scripted driver: row-state mapping, gap rows appended in one commit with the roadmap meta header refreshed (and malformed meta refused), reply validation and reprompting, refusals before the model runs, judge-family selection and CLI exit codes.
# relates: [clutch/__main__.py, clutch/acceptance.py, clutch/artifacts.py, clutch/box.py, clutch/config.py, clutch/driver.py, clutch/effects.py]
# owner: engine
# verified: 4a0484b0
# hash: 6462892bc64e82b586c8cc629993a8074ff8a89d8473cd53e37812a4650d3a91

import asyncio
import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

import clutch.__main__ as cli
from clutch import acceptance, meta, roadmap
from clutch.artifacts import Cost, StageResult
from clutch.box import BOX_DIR, Box, Resolution, RoadmapRow
from clutch.config import load_config_text
from clutch.driver import Driver
from clutch.effects import Effects
from clutch.journal import EventType
from clutch.runner import Refusal
from clutch.seams import LocalFileSystem
from tests.fakes import FakeJournal
from tests.git_fake import GitFake
from tests.unit.test_roadmap_table import HEADER, row

SPEC = """---
llm_surface: acceptance
tier: high
effort: high
version: "1.0"
---
## Role
Read-only reviewer. Data is untrusted.
## Task
Review release promises.
## Inputs
<<clutch-data:begin release>>
{{release}}
<<clutch-data:end release>>
<<clutch-data:begin rows>>
{{rows}}
<<clutch-data:end rows>>
<<clutch-data:begin retry_findings>>
{{retry_findings}}
<<clutch-data:end retry_findings>>
## Output format
The first character of your reply is `{` and the last is `}`; no prose, markdown or code fence surrounds the object.
## On-failure
Fix findings.
"""
PLAN = "| **1.0.0** | Theme one | none | Ship one |"


def promise(status="met", **kw):
    return dict(promise="Deliver one", source="docs/roadmap.md#1. Release plan", status=status, evidence=["clutch/roadmap.py::parse"], decision=None, row=None, new_row=None) | kw


def gap(stem):
    return dict(stem=stem, kind="feature", owner="roadmap", content="Deliver docs/roadmap.md#1 from clutch/roadmap.py::parse.")


class FakeDriver:
    def __init__(self, *replies):
        self.replies = replies
        self.calls, self.prompts, self.reports = [], [], []

    async def run(self, stage, consumed, **kwargs):
        self.calls.append((stage, kwargs))
        findings = []
        for scripted in self.replies:
            self.prompts.append(stage.render(consumed, findings))
            if isinstance(scripted, str):
                return StageResult(outcome=scripted, artifact=None, findings=[], cost=Cost())
            reply = stage.emits.model_validate_json(json.dumps(dict(promises=scripted)))
            report = await stage.review(reply, len(self.prompts))
            self.reports.append(report)
            findings = report.findings
            if report.verdict == "pass":
                return StageResult(outcome="ok", artifact=reply, findings=[], cost=Cost())
        return StageResult(outcome="gate_failed", artifact=None, findings=findings, cost=Cost())


def block(prompt, name):
    return json.loads(prompt.split(f"<<clutch-data:begin {name}>>\n")[1].split(f"\n<<clutch-data:end {name}>>")[0])


def document(*first):
    return PLAN + "\n| **2.0.0** | Theme two | none | Ship two |\n### 1.0.0\n" + HEADER + "".join(first or [row(1, "`a-row`"), row(2, "`b-row`")]) + "\n### 2.0.0\n" + HEADER + row(3, "`c-row`")


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "acceptance.md").write_text(SPEC)
    monkeypatch.setattr(acceptance, "SPECS_DIR", specs)
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / roadmap.ROADMAP).write_text(document())

    async def status(repo_arg, *args):
        assert (repo_arg, args) == (repo, ("--", roadmap.ROADMAP))
        return git.dirty

    async def run(repo_arg, *args):
        assert args == ("ls-files", "--cached", "--others", "--exclude-standard", "-z")
        return "\0".join(git.files)

    async def commit_edit(repo_arg, message, *, only, edit):
        await edit()
        git.commits.append((message, only, (repo_arg / roadmap.ROADMAP).read_text()))

    git = GitFake(status_porcelain=status, _run=run, commit_edit=commit_edit, ls_files=lambda repo_arg: git.tracked, rev_parse=lambda repo_arg, rev: "12345678abcdef")
    git.dirty, git.files, git.commits, git.tracked = "", [], [], []
    return SimpleNamespace(
        repo=repo,
        config=SimpleNamespace(state_dir=tmp_path / "state", providers=[], meta=SimpleNamespace(paths=[SimpleNamespace(root="docs", kind="doc")])),
        git=git,
        fs=LocalFileSystem(),
        journal=FakeJournal(),
    )


def run(checkout, driver, release="1.0.0"):
    return asyncio.run(acceptance.accept(checkout, driver, release))


def test_append_row():
    # Wrong last-table or end-of-file insertion differs from both exact documents below.
    text = "### 1.0.0\r\n" + HEADER.replace("\n", "\r\n") + row(1, "`a-row`").replace("\n", "\r\n") + row(2, "`b-row`").replace("\n", "\r\n")
    text += "\r\n```gate\r\nclutch doctor\r\n```\r\n### 1.0.0, last group\r\n" + HEADER + row(3, "`c-row`")
    tail = "| (5) | `cond-row` | roadmap | feature | P2 | | | c |\n"
    text += "\n### 2.0.0\n" + HEADER + row(4, "`d-row`") + tail + "\n"
    line = "| 6 | `gap-row` | roadmap | feature | P1 | | | Fill gap. |"
    for release, anchor, ending, heading in [("1.0.0", row(2, "`b-row`").replace("\n", "\r\n"), "\r\n", "1.0.0"), ("2.0.0", tail, "\n", "2.0.0")]:
        result = roadmap.append_row(text, release, line)
        assert result == text.replace(anchor, anchor + line + ending)
        added = next(r for r in roadmap.parse(result) if r.number == 6)
        # The inserted row must actually parse, with no accidental link, strike or dependencies.
        assert (added.stem, added.priority, added.depends, added.linked, added.struck, added.release) == ("gap-row", "P1", "", False, False, heading)
    with pytest.raises(Refusal, match="no release 9.9.9"):
        roadmap.append_row(text, "9.9.9", line)


def test_accept_passes(checkout):
    for i in range(4):
        checkout.journal.append(EventType.STATE_TRANSITION, {"to": "running"}, ticket=f"prior-{i}")
    driver = FakeDriver([promise(), promise("deferred", promise="Wait for two", decision="section 5 decision 7")])
    # A failure verdict or dropped decision changes these complete printed results.
    assert run(checkout, driver) == (
        True,
        [
            "accept 1.0.0: met: Deliver one [docs/roadmap.md#1. Release plan]",
            "accept 1.0.0: deferred: Wait for two [docs/roadmap.md#1. Release plan] -- section 5 decision 7",
            "accept 1.0.0: passed",
        ],
    )
    assert checkout.git.commits == []  # A read-only pass must not create a commit.
    assert not any(call[0] == "commit_edit" for call in checkout.git.calls)
    stage, kwargs = driver.calls[0]
    assert kwargs == dict(ticket=None, subject="1.0.0", run_seq=4, attempt=1, workspace=checkout.repo, tier="high", effort="high", stuck_budget=1800.0, expected_budget="surface", scope_fence=())
    assert (stage.surface, stage.emits, stage.gates) == ("acceptance", acceptance.AcceptanceReply, [])
    assert block(driver.prompts[0], "release") == dict(release="1.0.0", next_release="2.0.0", release_plan=PLAN, plans=["docs/roadmap.md"])


def test_meta_header(checkout):
    path = checkout.repo / roadmap.ROADMAP
    checkout.git.tracked = [roadmap.ROADMAP]
    fields, body, offset = meta.parse(document(), ".md")
    fields, _ = meta.generated(fields, body, roadmap.ROADMAP, "doc", checkout.git.tracked, "oldsha")
    fields["purpose"] = "Roadmap"
    fields["hash"] = "stale-hash"
    stale, _ = meta.compose(fields, body, offset, ".md")
    path.write_text(stale)
    old_hash = fields["hash"]
    run(checkout, FakeDriver([promise("partial", new_row=gap("meta-gap"))]))
    message, only, committed = checkout.git.commits[0]
    assert message == "clutch(roadmap): accept 1.0.0"
    assert only == [roadmap.ROADMAP]
    assert meta.parse(committed, ".md")[0]["hash"] != old_hash
    assert meta.check(checkout.config, checkout.repo, checkout.fs, checkout.git.tracked, "12345678abcdef") == []
    assert committed == path.read_text()


def test_meta_malformed(checkout):
    path = checkout.repo / roadmap.ROADMAP
    checkout.git.tracked = [roadmap.ROADMAP]
    original = ("<!-- clutch:meta\ninvalid\n-->\n" + document()).encode()
    path.write_bytes(original)
    with pytest.raises(Refusal, match="malformed docs/roadmap.md.*fix the meta block"):
        run(checkout, FakeDriver([promise("partial", new_row=gap("meta-gap"))]))
    assert path.read_bytes() == original
    assert checkout.git.commits == []


def test_row_states(checkout):
    path = checkout.repo / roadmap.ROADMAP
    path.write_text(
        document(
            row(1, "~~`struck-row`~~"),
            row(2, "`merged-row`"),
            row(4, "`rejected-row`", content="**Authored** (`tickets/rejected-row/`). Work."),
            row(5, "`declined-row`"),
            row(6, "`linked-row`", content="**Authored** (`tickets/linked-row/`). Work."),
            row(7, "`file-row`"),
            row(8, "`open-row`", owner="sample plan", kind="chore", priority="P2", depends="row 6", content="Distinct open work."),
        )
    )
    checkout.git.files = ["tickets/file-row/ticket.md", "tickets/declined-row/ticket.md", "docs/sample-plan.md"]
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="struck-row")
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="merged-row")
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="rejected-row")
    box = Box(checkout.config.state_dir / BOX_DIR, checkout.fs)
    payload = RoadmapRow(number=5, release="1.0.0", stem="declined-row", owner="roadmap", kind="feature", priority="P1", content="Work.", plan=roadmap.ROADMAP)
    id_, _ = box.enqueue(message_class="roadmap_row", origin="roadmap/declined-row", summary="Decline.", roadmap_row=payload)
    box.resolve(id_, Resolution(kind="declined", link="decision"))
    driver = FakeDriver([promise()])
    run(checkout, driver)
    # Treating any dead row as open, or failing to recognize linked/file-backed rows, changes this mapping.
    assert {r["stem"]: r["state"] for r in block(driver.prompts[0], "rows")} == {
        "struck-row": "merged",
        "merged-row": "merged",
        "rejected-row": "rejected",
        "declined-row": "declined",
        "linked-row": "authored",
        "file-row": "authored",
        "open-row": "open",
        "c-row": "open",
    }

    assert block(driver.prompts[0], "rows")[-2] == dict(
        number=8, release="1.0.0", stem="open-row", owner="sample plan", kind="chore", priority="P2", depends="row 6", content="Distinct open work.", state="open"
    )


def test_gaps_append_rows(checkout):
    driver = FakeDriver([promise("partial", new_row=gap("gap-one")), promise("unmet", row=2), promise("deferred", new_row=gap("gap-two"))])
    ok, lines = run(checkout, driver)
    assert ok is False  # partial/unmet must fail even though the review itself passed.
    assert lines[-1] == "accept 1.0.0: failed: 2 of 3 promises partial or unmet -- `clutch roadmap author` files the rows above; the gate passes once they merge"
    assert [line.split(" -- ")[-1] for line in lines[:-1]] == ["new row 4 gap-one in 1.0.0", "row 2 b-row", "new row 5 gap-two in 2.0.0"]
    expected = document().replace(row(2, "`b-row`"), row(2, "`b-row`") + "| 4 | `gap-one` | roadmap | feature | P1 | | | " + gap("gap-one")["content"] + " |\n")
    expected = expected.replace(row(3, "`c-row`"), row(3, "`c-row`") + "| 5 | `gap-two` | roadmap | feature | P1 | | | " + gap("gap-two")["content"] + " |\n")
    # Exact one-commit text rules out duplicate existing rows, per-row commits and wrong release/priority.
    assert checkout.git.commits == [("clutch(roadmap): accept 1.0.0", [roadmap.ROADMAP], expected)]
    checkout.git.commits.clear()
    (checkout.repo / roadmap.ROADMAP).write_text(document())
    ok, lines = run(checkout, FakeDriver([promise("deferred", new_row=gap("deferred-only"))]))
    assert (ok, lines[-1]) == (True, "accept 1.0.0: passed")
    assert len(checkout.git.commits) == 1


def test_reply_checks_reprompt(checkout):
    checkout.journal.append(EventType.STATE_TRANSITION, {"to": "rejected"}, ticket="journal-used")
    checkout.git.files = ["tickets/file-used/evidence/a.txt", "docs/sample-plan.md"]
    invalid = [
        promise(source="docs/alien-plan.md#Target design"),
        promise("partial", row=99),
        promise("unmet", row=3),
        promise("partial", row=1),
        promise("partial", new_row=gap("Bad Stem")),
        promise("partial", new_row=gap("b-row")),
        promise("partial", new_row=gap("journal-used")),
        promise("partial", new_row=gap("file-used")),
        promise("partial", new_row=gap("repeat-row")),
        promise("partial", new_row=gap("repeat-row")),
        promise("partial", new_row=gap("bad-owner") | {"owner": "roadmap|x"}),
        promise("partial", new_row=gap("wrong-plan") | {"owner": "sample"}),
        promise("partial", new_row=gap("newline-row") | {"content": "First\nsecond"}),
        promise("deferred", row=2),
        promise("partial", new_row=gap("newline-owner") | {"owner": "roadmap\nmore"}),
    ]
    (checkout.repo / roadmap.ROADMAP).write_text(document(row(1, "~~`a-row`~~"), row(2, "`b-row`")))
    driver = FakeDriver(invalid, [promise()])
    assert run(checkout, driver)[0] is True
    findings = driver.reports[0].findings
    # One finding for each independent defect, with the first repeat-row being valid.
    assert len(findings) == 14
    assert all(f.code == "acceptance_reply" and f.paved_road for f in findings)
    assert all(f.message in driver.prompts[1] and f.paved_road in driver.prompts[1] for f in findings)
    assert driver.reports[1].verdict == "pass"
    driver = FakeDriver([promise("deferred", new_row=gap("last-release"))], [promise()])
    assert run(checkout, driver, "2.0.0")[0] is True
    assert [f.message for f in driver.reports[0].findings] == ["no next release"]


def test_refusals_before_the_model(checkout):
    path = checkout.repo / roadmap.ROADMAP
    for problem, expected in [("missing", "missing docs/roadmap.md"), ("dirty", "uncommitted docs/roadmap.md"), ("unknown", "no release 9.9.9"), ("section", "no section 1 row for 1.0.0")]:
        path.write_text(document())
        checkout.git.dirty = ""
        if problem == "missing":
            path.unlink()
        elif problem == "dirty":
            checkout.git.dirty = " M docs/roadmap.md"
        elif problem == "section":
            path.write_text(document().replace(PLAN, ""))
        driver = FakeDriver([promise()])
        with pytest.raises(Refusal, match=expected) as error:
            run(checkout, driver, "9.9.9" if problem == "unknown" else "1.0.0")
        assert str(error.value).split(" -- ", 1)[1]
        assert not driver.calls and not checkout.git.commits
    path.write_text(document())
    driver = FakeDriver("timeout")
    with pytest.raises(Refusal, match="acceptance review ended timeout"):
        run(checkout, driver)
    assert len(driver.calls) == 1 and not checkout.git.commits


def config(checkout, *, single=False, judge=False):
    names = ["codex"] if single else ["claude", "codex"]
    return load_config_text(
        json.dumps(
            dict(
                schema_version=1,
                state_dir=str(checkout.config.state_dir),
                review={},
                merge={},
                engine_plane_safety_inventory=[],
                providers=[dict(name=n, kind="cli", package="test-package", limits={"concurrency": 1}, models_by_tier=dict(low="model", medium="model", high="model", max="model")) for n in names],
                routing=[dict(tier="high", surface="review", candidates=[dict(provider="codex")])] + ([dict(tier="high", surface="acceptance", candidates=[dict(provider="claude")])] if judge else []),
            )
        ),
        path=checkout.repo / "config.yaml",
        cwd=checkout.repo,
    )


def test_judge_family(checkout):
    (checkout.repo / roadmap.ROADMAP).write_text(document(row(1, "~~`a-row`~~", content="Merged `tickets/split-row/`."), row(2, "~~`b-row`~~")))
    for stem, provider, count in [("a-row", "claude", 2), ("b-row", "codex", 1), ("split-row", "codex", 2), ("outside-row", "claude", 5)]:
        for i in range(count):
            checkout.journal.append(EventType.EFFECT_COMPLETION, {"cost": {"provider": provider}}, key=f"llm/{stem}/9/implement/1/{i}")
    # These distractors must not count: wrong surface, malformed key and non-completion.
    checkout.journal.append(EventType.EFFECT_COMPLETION, {"cost": {"provider": "claude"}}, key="llm/a-row/9/review/1/1")
    checkout.journal.append(EventType.EFFECT_COMPLETION, {"cost": {"provider": "claude"}}, key="llm/a-row/9/implement/1/1/extra")
    checkout.journal.append(EventType.EFFECT_INTENT, {"cost": {"provider": "claude"}}, key="llm/a-row/9/implement/1/99")
    checkout.config = config(checkout)
    driver = FakeDriver([promise()])
    with pytest.raises(Refusal, match="acceptance judge codex implemented most of release 1.0.0") as error:
        run(checkout, driver)
    assert "surface: acceptance" in str(error.value).split(" -- ", 1)[1] and "provider: claude" in str(error.value).split(" -- ", 1)[1]
    assert not driver.calls
    checkout.config = config(checkout, judge=True)
    assert run(checkout, FakeDriver([promise()]))[0] is True
    checkout.config = config(checkout, single=True)
    assert run(checkout, FakeDriver([promise()]))[0] is True


@pytest.mark.parametrize(("result", "code", "output"), [(True, 0, "a"), (False, 1, "b"), (None, 2, None)])
def test_main_roadmap_accept(tmp_path, monkeypatch, capsys, result, code, output):
    cfg = SimpleNamespace(state_dir=tmp_path / "state")
    journal = FakeJournal()
    monkeypatch.setattr(cli, "load_config", lambda *a, **kw: cfg)
    monkeypatch.setattr(cli, "child_env", lambda *a: {})
    monkeypatch.setattr(cli, "Journal", lambda *a: journal)
    events = []

    class NoLock:
        def __init__(self, *a, **kw):
            pytest.fail("roadmap accept took the writer lock")

    class Session:
        async def close(self):
            events.append("close")

    async def preflight(checkout, session):
        events.append("preflight")
        return "llm"

    driver = SimpleNamespace()

    def from_config(config, **kw):
        events.append((config, kw["llm"]))
        driver.journal = kw["journal"]
        driver.effects = Effects(kw["journal"])
        return driver

    async def accept(c, d, release):
        events.append((c.repo, release, d is driver, d.journal is journal, d.effects._journal is journal))
        if result is None:
            raise Refusal("blocked", "repair")
        return result, [output]

    monkeypatch.setattr(cli, "Lockfile", NoLock)
    monkeypatch.setattr(cli, "build_control", lambda c: SimpleNamespace(providers=Session()))
    monkeypatch.setattr(cli, "_preflighted_llm", preflight)
    monkeypatch.setattr(Driver, "from_config", from_config)
    monkeypatch.setattr(acceptance, "accept", accept)
    assert cli.main(["roadmap", "accept", "1.0.0"], cwd=tmp_path, env={}) == code
    assert events == ["preflight", (cfg, "llm"), (tmp_path, "1.0.0", True, True, True), "close"]
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ((output + "\n", "") if output else ("", "clutch roadmap: blocked -- repair\n"))


def test_dirty_after_review_refuses(checkout):
    driver = FakeDriver([promise("partial", new_row=gap("gap-row"))])
    original_run = driver.run

    async def dirty(*args, **kwargs):
        result = await original_run(*args, **kwargs)
        checkout.git.dirty = " M docs/roadmap.md"
        return result

    driver.run = dirty
    before = (checkout.repo / roadmap.ROADMAP).read_bytes()
    with pytest.raises(Refusal, match="uncommitted docs/roadmap.md"):
        run(checkout, driver)
    assert not checkout.git.commits and (checkout.repo / roadmap.ROADMAP).read_bytes() == before


@pytest.mark.parametrize(
    "item",
    [
        promise(row=1),
        promise("partial"),
        promise("unmet", decision="decision", row=1),
        promise("partial", row=1, new_row=gap("gap-row")),
        promise("deferred"),
        promise("deferred", row=1, decision="decision"),
        promise(evidence=[]),
        promise("partial", row=0),
        promise("partial", new_row=gap("gap-row") | {"kind": "bug"}),
        promise(extra="unknown"),
        promise("partial", row="2"),
    ],
)
def test_reply_models_reject_invalid_shapes(item):
    # Each item isolates a schema or status-coherence violation, not a default-valued assertion.
    with pytest.raises(ValidationError):
        acceptance.AcceptanceReply.model_validate_json(json.dumps({"promises": [item]}))


def test_plan_inputs_and_fresh_numbering(checkout):
    checkout.git.files = ["docs/sample-plan.md", "docs/other-plan.md"]
    path = checkout.repo / roadmap.ROADMAP
    path.write_text(document(row(1, "`a-row`", owner="sample plan"), row(2, "`b-row`")))
    driver = FakeDriver([promise("partial", source="docs/sample-plan.md#Target design", new_row=gap("plan-gap") | {"owner": "sample"})])
    original_run = driver.run

    async def intervening_commit(*args, **kwargs):
        result = await original_run(*args, **kwargs)
        path.write_text(path.read_text() + "\n### 3.0.0\n" + HEADER + row(40, "`later-row`"))
        return result

    driver.run = intervening_commit
    ok, lines = run(checkout, driver)
    # Pulling every plan in the repo, or omitting a selected row's plan, changes this exact list.
    assert block(driver.prompts[0], "release")["plans"] == ["docs/roadmap.md", "docs/sample-plan.md"]
    # Numbering from the pre-model snapshot collides with a clean change made while the model reads.
    assert (ok, lines[0].split(" -- ")[-1]) == (False, "new row 41 plan-gap in 1.0.0")
    assert "`later-row`" in checkout.git.commits[0][2]


def test_judge_tie_first_provider(checkout):
    (checkout.repo / roadmap.ROADMAP).write_text(document(row(1, "~~`a-row`~~"), row(2, "`b-row`")))
    for provider in ("codex", "claude"):
        checkout.journal.append(EventType.EFFECT_COMPLETION, {"cost": {"provider": provider}}, key="llm/a-row/1/implement/1/1")
    checkout.config = config(checkout)
    # An alphabetic tie-break would pick claude, allowing the codex judge through.
    with pytest.raises(Refusal, match="acceptance judge codex"):
        run(checkout, FakeDriver([promise()]))


def test_latest_box_message_wins(checkout):
    box = Box(checkout.config.state_dir / BOX_DIR, checkout.fs)
    for version in ("old", "new"):
        payload = RoadmapRow(number=1, release="1.0.0", stem="a-row", owner="roadmap", kind="feature", priority="P1", content=version, plan=roadmap.ROADMAP)
        id_, _ = box.enqueue(message_class="roadmap_row", origin="roadmap/a-row", summary=version, roadmap_row=payload)
        if version == "old":
            box.resolve(id_, Resolution(kind="declined", link="old-decision"))
    driver = FakeDriver([promise()])
    run(checkout, driver)
    # Taking the oldest message, or any declined message, makes this open row dead.
    assert block(driver.prompts[0], "rows")[0]["state"] == "open"
