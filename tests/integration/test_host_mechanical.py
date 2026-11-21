"""Host checks through production Check and inline admission."""
# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Host checks through production Check and inline admission.
# relates: [clutch/box.py, clutch/config.py, clutch/daemon.py, clutch/flake.py, clutch/journal.py, clutch/merge.py, clutch/seams.py, clutch/stages.py]
# owner: engine
# verified: 77c3dad9
# hash: 50df0251b3c87339bed27ee50e6970164b32ec462e3e5d8c7dc41bc96d2ee627

import asyncio

import pytest

from clutch import merge, stages
from clutch.box import BOX_DIR, Box
from clutch.seams import ExecutableNotFound
from tests.integration.test_mergequeue import approve, commit, ctx, host, ready, scripted
from tests.integration.test_stages import SECRET
from tests.spool_captures import list_captures, read_capture


async def checked(ctx, ticket):
    slip = stages.PackingSlip(produced_by_spec_version=1, produced_at_sha="head", stem=ticket.stem, branch=ticket.stem, outcome="ok", summary="work", run_record="run.md")
    return await stages.check(ctx, ticket, slip, attempt=0)


def test_triggered_entries_run_at_check(ctx, monkeypatch):
    async def run():
        ticket = await ready(ctx)
        ctx.config.review.mechanical = [host("always"), host("path", trigger=["clutch"])]
        calls = scripted(ctx, monkeypatch, [(0, "", "")] * 2)
        result = await checked(ctx, ticket)
        assert result.outcome == "ok" and [c[0][1] for c in calls] == ["always", "path"]
        assert [r.code for r in result.artifact.reports[-2:]] == ["always", "path"]
        assert "check/host-02.txt" in [name for _, name in list_captures(ctx.config.state_dir, ticket.stem, 0)]

    asyncio.run(run())


def test_untriggered_entry_never_runs(ctx, monkeypatch):
    async def run():
        ticket = await ready(ctx, changes={"clutch/xy.py": "ok"}, fence=("clutch/xy.py",))
        ctx.config.review.mechanical = [host("skip", trigger=["clutch/x"])]
        calls = scripted(ctx, monkeypatch, [])
        result = await checked(ctx, ticket)
        assert result.outcome == "ok" and not calls
        assert "skip" not in [r.code for r in result.artifact.reports]
        assert [name for _, name in list_captures(ctx.config.state_dir, ticket.stem, 0) if name.rsplit("/", 1)[-1].startswith("host-")] == []

    asyncio.run(run())


@pytest.mark.parametrize("severity", ["hard", "soft"])
def test_failure(ctx, monkeypatch, severity):
    async def run():
        ticket = await ready(ctx)
        ctx.config.review.mechanical = [host("bad", severity=severity)]
        scripted(ctx, monkeypatch, [(1, "bad", ""), (0, "", "")])
        result = await checked(ctx, ticket)
        assert result.outcome == ("gate_failed" if severity == "hard" else "ok")
        assert result.artifact.reports[-1].verdict == "fail" and result.findings[-1].code == "bad"

    asyncio.run(run())


def test_hard_failure_fails_check(ctx, monkeypatch):
    test_failure(ctx, monkeypatch, "hard")


def test_soft_failure_reported_and_passes(ctx, monkeypatch):
    test_failure(ctx, monkeypatch, "soft")


def test_base_red_entry_is_preexisting(ctx, monkeypatch):
    async def run():
        ticket = await ready(ctx, changes={"clutch/other.py": "outside"})
        ctx.config.review.mechanical = [host("base-red")]
        scripted(ctx, monkeypatch, [(1, "red", ""), (1, "red", "")])
        result = await checked(ctx, ticket)
        assert result.outcome == "gate_failed"
        report = result.artifact.reports[-1]
        assert report.verdict == "pass" and not report.findings
        assert [f.code for f in stages._prior_findings(ctx, ticket.stem, "check")] == ["scope_fence"]
        assert Box(ctx.config.state_dir / BOX_DIR, ctx.fs).messages()[0].outcome == "base_red"

    asyncio.run(run())


@pytest.mark.parametrize("failure", [TimeoutError(), ExecutableNotFound("host")])
def test_timeout_and_missing_executable_fail_closed(ctx, monkeypatch, failure):
    async def run():
        ticket = await ready(ctx)
        ctx.config.review.mechanical = [host("bad", argv=["host", SECRET])]
        calls = scripted(ctx, monkeypatch, [failure, (0, "", "")])
        result = await checked(ctx, ticket)
        assert result.outcome == "gate_failed" and "FAKE_KEY" not in calls[0][1]["env"]
        assert SECRET not in result.findings[-1].message
        assert SECRET not in read_capture(ctx.config.state_dir, ticket.stem, 0, "check/host-01.txt").decode()

    asyncio.run(run())


def test_inline_merge_reruns_triggered_hard_entries(ctx, monkeypatch):
    async def run():
        ticket = await ready(ctx)
        ctx.fs.write(ctx.repo / "clutch/other.py", b"main moved\n")
        await commit(ctx, ctx.repo, ["clutch/other.py"])
        ctx.config.review.mechanical = [host("red"), host("soft", severity="soft"), host("skip", trigger=["other"])]
        calls = scripted(ctx, monkeypatch, [(1, "red", "")])
        before = await ctx.git.rev_parse(ctx.repo, "main")
        result = await merge.merge(ctx, ticket, attempt=0)
        assert result.outcome == "gate_failed" and [c[0][1] for c in calls] == ["red"]
        assert await ctx.git.rev_parse(ctx.repo, "main") == before
        assert "merge/host-01.txt" in [name for _, name in list_captures(ctx.config.state_dir, ticket.stem, 0)]

    asyncio.run(run())


@pytest.mark.parametrize("stale", [False, True])
def test_inline_merge_skips_unchanged_code(ctx, monkeypatch, stale):
    async def run():
        ticket = await ready(ctx, verification=(("host", "verify"),))
        if stale:
            await approve(ctx, ticket, sha="older")
        ctx.config.review.mechanical = [host("check")]
        calls = scripted(ctx, monkeypatch, [])
        result = await merge.merge(ctx, ticket, attempt=0)
        assert not calls
        assert result.outcome == ("gate_failed" if stale else "ok")
        if stale:
            assert any(f.code == "correctness_review" for f in result.findings)
        assert [name for _, name in list_captures(ctx.config.state_dir, ticket.stem, 0) if name.startswith("merge/")] == []

    asyncio.run(run())


def test_autofix_config_loading(ctx, tmp_path):
    import yaml

    from clutch.config import ConfigError, load_config

    raw = yaml.safe_load((ctx.repo / "config.yaml").read_text())
    raw["review"]["autofix"] = [{"code": "fix", "argv": ["fix"], "files": ["*.py"]}]
    path = tmp_path / "config.yaml"

    def load():
        path.write_text(yaml.safe_dump(raw))
        return load_config(path, cwd=tmp_path)

    raw["review"]["mechanical"] = [{"code": "tests", "argv": ["pytest"], "trigger": "always", "severity": "hard", "results": "results.json"}]
    assert load().review.mechanical[0].results == "results.json"
    assert load().review.autofix[0].argv == ["fix"]
    for entry in ({"code": "fix", "argv": [], "files": ["*.py"]}, {"code": "fix", "argv": ["fix"], "files": ["*.py"], "extra": 1}):
        raw["review"]["autofix"] = [entry]
        with pytest.raises(ConfigError):
            load()

    for entry in ({"code": "fix", "argv": ["fix"]}, {"code": "fix", "argv": ["fix"], "files": []}):
        raw["review"]["autofix"] = [entry]
        with pytest.raises(ConfigError) as exc:
            load()
        assert exc.value.key == "review.autofix.0.files"


def test_autofix_commits_selected_files_and_evaluates_head(ctx, monkeypatch):
    from clutch.config import AutofixCommand
    from tests.integration.test_mergequeue import commit

    async def run():
        ticket = await ready(ctx, changes={"clutch/thing.py": "before\n", "tickets/extra.txt": "ticket\n"}, fence=("clutch/thing.py", "tickets"))
        root = ctx.worktree(ticket.stem)
        (root / "clutch/other.py").unlink()
        await commit(ctx, root, ["clutch/other.py"], "delete")
        ctx.config.review.autofix = [AutofixCommand(code="fix", argv=["host", "fix"], files=["*.py"])]
        original = ctx.exec_.run
        calls = []

        async def execute(argv, **kw):
            if argv[0] == "host":
                calls.append(argv)
                (root / "clutch/thing.py").write_text("fixed\n")
                return 0, "", ""
            return await original(argv, **kw)

        monkeypatch.setattr(ctx.exec_, "run", execute)
        result = await checked(ctx, ticket)
        head = await ctx.git.rev_parse(ctx.repo, ticket.stem)
        assert calls == [["host", "fix", "clutch/thing.py"]]
        assert result.artifact.produced_at_sha == head
        assert "clutch/thing.py" in await ctx.git.diff_names(ctx.repo, "main", ticket.stem)
        assert (await ctx.git._run(root, "log", "-1", "--format=%s")).strip() == f"clutch({ticket.stem}): autofix"
        assert (await ctx.git._run(root, "show", "--format=", "--name-only", "HEAD")).strip() == "clutch/thing.py"
        assert result.artifact.reports[0].verdict == "pass"

    asyncio.run(run())


def test_autofix_no_change_and_already_satisfied(ctx, monkeypatch):
    from clutch.config import AutofixCommand

    async def run():
        ticket = await ready(ctx)
        root = ctx.worktree(ticket.stem)
        head = await ctx.git.rev_parse(ctx.repo, ticket.stem)
        (root / "clutch/thing.py").write_text("uncommitted\n")
        ctx.config.review.autofix = [AutofixCommand(code="fix", argv=["host", "fix"], files=["*.py"])]
        calls = scripted(ctx, monkeypatch, [(0, "", "")])
        await checked(ctx, ticket)
        assert len(calls) == 1 and await ctx.git.rev_parse(ctx.repo, ticket.stem) == head
        assert (root / "clutch/thing.py").read_text() == "uncommitted\n"
        slip = stages.PackingSlip(produced_by_spec_version=1, produced_at_sha=head, stem=ticket.stem, branch=ticket.stem, outcome="already_satisfied", summary="done", run_record="run.md")
        await stages.check(ctx, ticket, slip, attempt=1)
        assert len(calls) == 1

    asyncio.run(run())


def test_autofix_failure_restores_and_blocks_check(ctx, monkeypatch):
    from clutch.config import AutofixCommand
    from tests.integration.test_mergequeue import commit

    async def run():
        ticket = await ready(ctx, fence=("clutch/thing.py", "tickets"))
        root = ctx.worktree(ticket.stem)
        path = root / "clutch/thing.py"
        path.chmod(0o755)
        await commit(ctx, root, ["clutch/thing.py"], "executable")
        head = await ctx.git.rev_parse(ctx.repo, ticket.stem)
        ctx.config.review.autofix = [AutofixCommand(code="bad", argv=["host", "bad"], files=["*.py"]), AutofixCommand(code="later", argv=["host", "later"], files=["*.py"])]
        original = ctx.exec_.run
        calls = []

        async def execute(argv, **kw):
            if argv[0] == "host":
                calls.append(argv)
                path.write_text("broken")
                path.chmod(0o644)
                return 1, "", "failed"
            return await original(argv, **kw)

        monkeypatch.setattr(ctx.exec_, "run", execute)
        result = await checked(ctx, ticket)
        assert result.outcome == "gate_failed" and any(f.code == "bad" for f in result.findings)
        assert len(calls) == 1 and await ctx.git.rev_parse(ctx.repo, ticket.stem) == head
        assert "clutch/thing.py" not in await ctx.git.status_porcelain(root)
        assert path.stat().st_mode & 0o111

    asyncio.run(run())


def test_autofix_skips_when_no_files(ctx, monkeypatch):
    from clutch.config import AutofixCommand
    from tests.integration.test_mergequeue import commit

    async def run():
        ticket = await ready(ctx)
        root = ctx.worktree(ticket.stem)
        (root / "clutch/thing.py").unlink()
        await commit(ctx, root, ["clutch/thing.py"], "delete")
        ctx.config.review.autofix = [AutofixCommand(code="fix", argv=["host", "fix"], files=["*.py"])]
        calls = scripted(ctx, monkeypatch, [])
        await checked(ctx, ticket)
        assert not calls

    asyncio.run(run())


@pytest.mark.parametrize("fail", [False, True])
def test_autofix_selection_and_union(ctx, monkeypatch, fail):
    from clutch.config import AutofixCommand

    async def run():
        changes = {"a.py": "python\n", "config.yaml": "yaml\n", ".gitignore": "ignore\n"}
        ticket = await ready(ctx, changes=changes, fence=tuple(changes))
        root = ctx.worktree(ticket.stem)
        head = await ctx.git.rev_parse(ctx.repo, ticket.stem)
        ctx.config.review.autofix = [
            AutofixCommand(code="py", argv=["host", "py"], files=["*.py"]),
            AutofixCommand(code="yaml", argv=["host", "yaml"], files=["*.yaml"]),
        ]
        original = ctx.exec_.run
        calls = []

        async def execute(argv, **kw):
            if argv[0] == "host":
                calls.append(list(argv))
                (root / argv[-1]).write_text("fixed\n")
                return (1 if fail and argv[1] == "yaml" else 0), "", ""
            return await original(argv, **kw)

        monkeypatch.setattr(ctx.exec_, "run", execute)
        result = await checked(ctx, ticket)
        assert calls == [["host", "py", "a.py"], ["host", "yaml", "config.yaml"]]
        if fail:
            assert result.outcome == "gate_failed"
            assert await ctx.git.rev_parse(ctx.repo, ticket.stem) == head
            assert all((root / path).read_text() == data for path, data in changes.items())
        else:
            assert result.outcome == "ok"
            assert (await ctx.git._run(root, "log", "-1", "--format=%s")).strip() == f"clutch({ticket.stem}): autofix"
            assert set((await ctx.git._run(root, "show", "--format=", "--name-only", "HEAD")).split()) == {"a.py", "config.yaml"}

    asyncio.run(run())


def test_autofix_skips_unmatched_files(ctx, monkeypatch):
    from clutch.config import AutofixCommand

    async def run():
        ticket = await ready(ctx, changes={"config.yaml": "changed\n"}, fence=("config.yaml",))
        ctx.config.review.autofix = [AutofixCommand(code="py", argv=["host", "py"], files=["*.py"])]
        calls = scripted(ctx, monkeypatch, [])
        result = await checked(ctx, ticket)
        assert result.outcome == "ok" and not calls

    asyncio.run(run())


def results_script(ctx, monkeypatch, runs):
    import json

    original = ctx.exec_.run
    calls = []

    async def execute(argv, **kw):
        if argv[0] != "host":
            return await original(argv, **kw)
        calls.append(kw["cwd"])
        rc, outcomes = runs.pop(0)
        if outcomes is not None:
            (kw["cwd"] / "results.json").write_text(json.dumps({"schema_version": 2, "tests": outcomes, "seconds": {key: 0.0 for key in outcomes}}))
        return rc, "", ""

    monkeypatch.setattr(ctx.exec_, "run", execute)
    return calls


def test_results_detection_and_replay(ctx, monkeypatch):
    async def run():
        test = "tests/test_a.py::test_x"
        ticket = await ready(ctx)
        ctx.config.review.mechanical = [host("tests").model_copy(update={"results": "results.json"})]
        runs = [(1, {test: "failed"}), (0, {test: "passed"})] * 2
        results_script(ctx, monkeypatch, runs)
        for _ in range(2):
            assert (await checked(ctx, ticket)).outcome == "ok"
        assert len([e for e in ctx.driver.journal.read() if e.body.get("kind") == "flake_detected"]) == 1
        assert len(Box(ctx.config.state_dir / BOX_DIR, ctx.fs).messages()) == 1
        assert "check/host-01-rerun.txt" in [name for _, name in list_captures(ctx.config.state_dir, ticket.stem, 0)]

    asyncio.run(run())


@pytest.mark.parametrize("edited,second,expected", [(True, "passed", "gate_failed"), (False, "failed", "gate_failed")])
def test_results_block_edited_flake_and_real_failure(ctx, monkeypatch, edited, second, expected):
    async def run():
        test = "tests/test_a.py::test_x"
        ticket = await ready(ctx, changes={"tests/test_a.py": "changed"} if edited else None, fence=("tests/test_a.py",) if edited else ("clutch/thing.py",))
        ctx.config.review.mechanical = [host("tests").model_copy(update={"results": "results.json"})]
        results_script(ctx, monkeypatch, [(1, {test: "failed"}), (0 if second == "passed" else 1, {test: second}), (0, {})])
        result = await checked(ctx, ticket)
        assert result.outcome == expected and any(test in f.message for f in result.findings)
        assert not any(e.body.get("kind") == "flake_detected" for e in ctx.driver.journal.read())

    asyncio.run(run())


def test_results_quarantine_release_and_reflake(ctx, monkeypatch):
    from clutch.box import Resolution
    from clutch.daemon import flake_detection, storm_producer
    from clutch.journal import EventType

    async def run():
        test = "tests/test_a.py::test_x"
        ticket = await ready(ctx)
        ctx.config.review.mechanical = [host("tests").model_copy(update={"results": "results.json"})]
        box = storm_producer(root=ctx.config.state_dir / BOX_DIR, fs=ctx.fs, journal=ctx.driver.journal, clock=ctx.driver.clock)
        flake = flake_detection(journal=ctx.driver.journal, box=box, config=ctx.config, escalate=lambda _: None)
        runs = [(1, {test: "failed"}), (0, {test: "passed"}), (1, {test: "failed"}), (1, {test: "failed"}), (0, {test: "passed"}), (0, {test: "passed"}), (1, {test: "failed"}), (0, {test: "passed"})]
        results_script(ctx, monkeypatch, runs)
        assert (await checked(ctx, ticket)).outcome == "ok"
        identity = next(iter(flake.quarantine().active.values()))
        assert (await checked(ctx, ticket)).outcome == "ok"
        box.resolve(identity.box_id, Resolution(kind="ticket", link="fix-x"))
        assert (await checked(ctx, ticket)).outcome == "ok" and test in flake.quarantine().tests
        ctx.driver.journal.append(EventType.STATE_TRANSITION, {"to": "merged"}, ticket="fix-x")
        assert (await checked(ctx, ticket)).outcome == "ok" and test not in flake.quarantine().tests
        assert (await checked(ctx, ticket)).outcome == "ok"
        assert test in flake.quarantine().tests and len(box.messages()) == 2
        assert identity.box_id not in flake.quarantine().active

    asyncio.run(run())


@pytest.mark.parametrize("runs", [[(0, None), (0, {})], [(1, {"a": "failed"}), (0, None), (0, {})], [(1, {"a": "failed"}), (1, {"a": "passed"}), (0, {})]])
def test_results_fail_closed(ctx, monkeypatch, runs):
    async def run():
        ticket = await ready(ctx)
        ctx.config.review.mechanical = [host("tests").model_copy(update={"results": "results.json"})]
        missing = runs[0][1] is None or runs[1][1] is None
        results_script(ctx, monkeypatch, runs)
        result = await checked(ctx, ticket)
        assert result.outcome == "gate_failed"
        if missing:
            assert any("results.json" in f.message for f in result.findings)

    asyncio.run(run())


@pytest.mark.parametrize("edited,cap", [(True, False), (False, True)])
def test_results_edited_quarantine_and_cap(ctx, monkeypatch, edited, cap):
    from clutch.daemon import flake_detection, storm_producer
    from clutch.flake import RerunEvidence

    async def run():
        test = "tests/test_a.py::test_x"
        ticket = await ready(ctx, changes={"tests/test_a.py": "changed"} if edited else None, fence=("tests/test_a.py",) if edited else ("clutch/thing.py",))
        ctx.config.review.mechanical = [host("tests").model_copy(update={"results": "results.json"})]
        ctx.config.caps.quarantine = 1
        box = storm_producer(root=ctx.config.state_dir / BOX_DIR, fs=ctx.fs, journal=ctx.driver.journal, clock=ctx.driver.clock)
        flake = flake_detection(journal=ctx.driver.journal, box=box, config=ctx.config, escalate=lambda _: None)
        existing = "other" if cap else test
        flake.detect(test_id=existing, evidence=RerunEvidence(existing, "fail", "pass", True, True, True), summary="existing", reason="existing", occurrence_id="existing")
        second = "passed" if cap else "failed"
        results_script(ctx, monkeypatch, [(1, {test: "failed"}), (0 if cap else 1, {test: second}), (0, {})])
        result = await checked(ctx, ticket)
        assert result.outcome == "gate_failed" and any(test in f.message for f in result.findings)
        if cap:
            assert any("quarantine-cap crossed" in f.message for f in result.findings)
            assert test not in flake.quarantine().tests

    asyncio.run(run())


@pytest.mark.parametrize("deletion,covered,expected", [(False, 3, "gate_failed"), (False, 2, "ok"), (False, 9, "ok"), (True, 5, "gate_failed"), (True, 2, "ok")])
def test_coverage_changed_lines(ctx, monkeypatch, deletion, covered, expected):
    import json

    from tests.integration.test_mergequeue import commit

    async def run():
        test = "tests/test_a.py::test_x"
        original_lines = [f"line {i}\n" for i in range(1, 11)]
        ctx.fs.write(ctx.repo / "pkg/m.py", "".join(original_lines).encode())
        await commit(ctx, ctx.repo, ["pkg/m.py"], "base code")
        changed = original_lines.copy()
        if deletion:
            del changed[4]
        else:
            changed[2] = "edited\n"
        ticket = await ready(ctx, changes={"pkg/m.py": "".join(changed)}, fence=("pkg/m.py",))
        ctx.config.review.mechanical = [host("tests").model_copy(update={"results": "results.json", "coverage": "coverage.json", "flake_coverage_argv": ["flake"]})]
        original = ctx.exec_.run
        calls = []

        async def execute(argv, **kw):
            if argv[0] not in {"host", "flake"}:
                return await original(argv, **kw)
            calls.append(argv)
            if argv[0] == "flake":
                (kw["cwd"] / "coverage.json").write_text(json.dumps({"files": {"pkg/m.py": {"executed_lines": [covered]}}}))
                return 0, "", ""
            outcomes = {test: "failed" if len(calls) == 1 else "passed"}
            (kw["cwd"] / "results.json").write_text(json.dumps({"schema_version": 2, "tests": outcomes, "seconds": {test: 0.0}}))
            return (1 if len(calls) == 1 else 0), "", ""

        monkeypatch.setattr(ctx.exec_, "run", execute)
        result = await checked(ctx, ticket)
        assert result.outcome == expected
        assert ["flake", test] in calls
        detected = [e for e in ctx.driver.journal.read() if e.body.get("kind") == "flake_detected"]
        assert bool(detected) == (expected == "ok")
        if expected == "gate_failed":
            assert any(test in f.message for f in result.findings)
        assert all("show_contexts" not in f.message + f.paved_road for f in result.findings)

    asyncio.run(run())


@pytest.mark.parametrize("case", ["missing", "malformed", "unset", "green", "green_invalid"])
def test_coverage_fail_closed(ctx, monkeypatch, case):
    import json

    async def run():
        test = "tests/test_a.py::test_x"
        ticket = await ready(ctx)
        command = None if case == "unset" else ["flake"]
        ctx.config.review.mechanical = [host("tests").model_copy(update={"results": "results.json", "coverage": "coverage.json", "flake_coverage_argv": command})]
        original = ctx.exec_.run
        calls = []

        async def execute(argv, **kw):
            if argv[0] not in {"host", "flake"}:
                return await original(argv, **kw)
            calls.append(argv)
            if argv[0] == "flake":
                if case == "malformed":
                    (kw["cwd"] / "coverage.json").write_text(json.dumps({"files": {"x": {}}}))
                return 0, "", ""
            flaky = case not in {"green", "green_invalid"}
            (kw["cwd"] / "results.json").write_text(json.dumps({"schema_version": 2, "tests": {test: "failed" if flaky and len(calls) == 1 else "passed"}, "seconds": {test: 0.0}}))
            if case == "green":
                (kw["cwd"] / "coverage.json").write_text(json.dumps({"meta": {"format": 3}, "files": {}}))
            return (1 if flaky and len(calls) == 1 else 0), "", ""

        monkeypatch.setattr(ctx.exec_, "run", execute)
        result = await checked(ctx, ticket)
        assert result.outcome == ("ok" if case == "green" else "gate_failed")
        assert not any(e.body.get("kind") == "flake_detected" for e in ctx.driver.journal.read())
        assert sum(call[0] == "flake" for call in calls) == (1 if case in {"missing", "malformed"} else 0)
        if case == "green":
            assert calls == [["host", "tests"]]
        if case in {"missing", "malformed", "unset"}:
            assert any("flake_coverage_argv" in f.paved_road for f in result.findings)
        if case == "green_invalid":
            assert any("Missing or invalid coverage report" in f.message for f in result.findings)
        assert all("show_contexts" not in f.message + f.paved_road for f in result.findings)

    asyncio.run(run())


def test_coverage_requires_results(ctx, tmp_path):
    import yaml

    from clutch.config import ConfigError, load_config

    raw = yaml.safe_load((ctx.repo / "config.yaml").read_text())
    raw["review"]["mechanical"] = [{"code": "tests", "argv": ["pytest"], "trigger": "always", "severity": "hard", "coverage": "coverage.json"}]
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ConfigError) as exc:
        load_config(path, cwd=tmp_path)
    assert exc.value.key == "review.mechanical.0.coverage"


def timing_run(ctx, monkeypatch, durations, outcomes, **options):
    import json

    async def run():
        ticket = await ready(ctx, changes={"changed.py": "changed"}, fence=("changed.py",))
        ctx.config.review.mechanical = [host("tests").model_copy(update={"results": "results.json", **options})]
        original = ctx.exec_.run

        async def execute(argv, **kw):
            if argv[0] != "host":
                return await original(argv, **kw)
            (kw["cwd"] / "results.json").write_text(json.dumps({"schema_version": 2, "tests": outcomes, "seconds": durations}))
            return 0, "", ""

        monkeypatch.setattr(ctx.exec_, "run", execute)
        return (await checked(ctx, ticket)).artifact.reports[-1]

    return asyncio.run(run())


def test_results_record_timing(ctx, monkeypatch):
    report = timing_run(ctx, monkeypatch, {"a": 0.5, "b": 3.0, "c": 1.0}, {"a": "passed", "b": "failed", "c": "skipped"})
    assert list(report.timing.slow.items()) == [("b", 3.0), ("c", 1.0)]
    assert (report.timing.passed, report.timing.failed, report.timing.skipped) == (1, 1, 1)


def test_slow_tests_capped(ctx, monkeypatch):
    durations = {f"test_{n:03}": 2.0 for n in range(150)}
    report = timing_run(ctx, monkeypatch, durations, dict.fromkeys(durations, "passed"))
    assert list(report.timing.slow) == list(durations)[:100]


def test_slow_test_bounds_configured(ctx, monkeypatch):
    durations = {"a": 2.0, "b": 3.0, "c": 4.0}
    report = timing_run(ctx, monkeypatch, durations, dict.fromkeys(durations, "passed"), slow_test_seconds=2.5, slow_test_limit=1)
    assert report.timing.slow == {"c": 4.0}


@pytest.mark.parametrize("field,value", [("slow_test_seconds", 2.5), ("slow_test_limit", 1)])
def test_slow_bounds_require_results(ctx, tmp_path, field, value):
    import yaml

    from clutch.config import ConfigError, load_config

    raw = yaml.safe_load((ctx.repo / "config.yaml").read_text())
    raw["review"]["mechanical"] = [{"code": "tests", "argv": ["pytest"], "trigger": "always", "severity": "hard", field: value}]
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw))
    with pytest.raises(ConfigError) as exc:
        load_config(path, cwd=tmp_path)
    assert exc.value.key == f"review.mechanical.0.{field}"


@pytest.mark.parametrize("valid", [True, False])
def test_coverage_recorded_for_changed_files(ctx, monkeypatch, valid):
    import json

    async def run():
        ticket = await ready(ctx, changes={"changed.py": "changed"}, fence=("changed.py",))
        ctx.config.review.mechanical = [host("tests").model_copy(update={"results": "results.json", "coverage": "coverage.json"})]
        original = ctx.exec_.run

        async def execute(argv, **kw):
            if argv[0] != "host":
                return await original(argv, **kw)
            (kw["cwd"] / "results.json").write_text(json.dumps({"schema_version": 2, "tests": {"a": "passed"}, "seconds": {"a": 2.0}}))

            def entry(covered):
                return {"summary": {"covered_lines": covered, "num_statements": 4}, "missing_lines": []}

            (kw["cwd"] / "coverage.json").write_text(json.dumps({"meta": {"format": 3}, "files": {"changed.py": entry(2), "other.py": entry(4)}}) if valid else "invalid")
            return 0, "", ""

        monkeypatch.setattr(ctx.exec_, "run", execute)
        report = (await checked(ctx, ticket)).artifact.reports[-1]
        if valid:
            assert report.verdict == "pass"
            assert report.coverage.model_dump() == {"percent": 75.0, "files": {"changed.py": 50.0}}
        else:
            assert report.verdict == "fail"
            assert any("Missing or invalid coverage report" in f.message for f in report.findings)

    asyncio.run(run())
