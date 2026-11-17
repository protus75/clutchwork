"""Envelope contracts with distinct fake git answers and a deterministic clock."""

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import quote

import pytest
from pydantic import BaseModel

from clutch import providers
from clutch.config import Config, snapshot_config
from clutch.driver import Driver, LlmStage
from clutch.effects import Effects
from clutch.evidence.store import EvidenceStore
from clutch.journal import Journal
from clutch.llm import FakeLLM, LLMRequest
from clutch.llmeffect import llm_call, llm_key
from clutch.providers import ProviderCallError, ProviderLLM, ProviderSession
from clutch.redact import Redactor
from clutch.seams import ExecutableNotFound, LocalFileSystem
from clutch.timers import Timers
from tests.evidence_records import seed_end

SECRET = "private-envelope-secret"
ENV = {"KEY": SECRET, "PATH": "/fake/bin", "HOME": "/fake/home"}
KEY = "llm/ticket/3/review/2/4"


class Time:
    def __init__(self):
        self.now = datetime(2026, 2, 3, 4, 5, 6, 123000, tzinfo=UTC)

    def __call__(self):
        return self.now

    async def sleep(self, seconds):
        await asyncio.Event().wait()


def config(root):
    return Config.model_validate(
        {
            "schema_version": 1,
            "state_dir": "state",
            "providers": [
                {
                    "name": "claude",
                    "kind": "cli",
                    "package": "claude-package",
                    "auth": "KEY",
                    "models_by_tier": dict.fromkeys(("low", "medium", "high", "max"), "requested-claude"),
                    "limits": {"concurrency": 1},
                },
                {
                    "name": "codex",
                    "kind": "cli",
                    "package": "codex-package",
                    "models_by_tier": dict.fromkeys(("low", "medium", "high", "max"), "requested-codex"),
                    "limits": {"concurrency": 1, "est_cost_per_call_usd": 2.5},
                },
            ],
            "routing": [{"tier": "medium", "surface": surface, "candidates": [{"provider": "claude"}, {"provider": "codex"}]} for surface in ("review", "implement")],
            "review": {},
            "merge": {},
            "engine_plane_safety_inventory": [],
        },
        context={"base": root},
    )


def stream(text="answer", *, codex=False):
    events = (
        [
            {"type": "thread.started", "thread_id": "native-thread"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": text}},
            {"type": "turn.completed", "usage": {"input_tokens": 37, "output_tokens": 19}},
        ]
        if codex
        else [
            {"type": "system", "subtype": "init", "model": "served-claude", "session_id": "native-session"},
            {"type": "result", "subtype": "success", "result": text, "total_cost_usd": 0.73, "usage": {"input_tokens": 23, "output_tokens": 11}},
        ]
    )
    return "".join(json.dumps(e) + "\n" for e in events)


class Exec:
    def __init__(self, fs, clock):
        self.fs, self.clock = fs, clock
        self.calls = []
        self.trees = 0
        self.rc, self.out, self.err = 0, stream(), "diagnostic"
        self.error = None
        self.spawn_check = lambda: None

    async def run(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        if argv[0] == "git":
            if "add" in argv:
                self.fs.write(Path(kwargs["env"]["GIT_INDEX_FILE"]), b"temporary index")
                return 0, "", ""
            if "write-tree" in argv:
                self.trees += 1
                return 0, ("b" if self.trees == 1 else "a") * 40 + "\n", ""
            if "diff" in argv:
                return 0, "changed.py\nother.txt\n", ""
            return 0, ("1" if argv[-1] == "main" else "2") * 40 + "\n", ""
        if argv[1:] == ["--version"]:
            return 0, "1.2.3 (Claude Code)", ""
        if argv[0] == "pnpm":
            return 0, "1.2.3", ""
        self.spawn_check()
        if kwargs.get("on_spawn"):
            kwargs["on_spawn"](97)
        if kwargs.get("on_stdout_line"):
            for line in self.out.splitlines(keepends=True):
                self.clock.now += timedelta(milliseconds=7)
                kwargs["on_stdout_line"](line)
        if self.error is not None:
            raise self.error
        return self.rc, self.out, self.err

    def kill_group(self, pgid):
        pass


class Rig:
    def __init__(self, root, monkeypatch, *, snapshot=False):
        monkeypatch.setattr(providers, "engine_version", lambda: "engine-test")
        monkeypatch.setattr(providers, "spec_version", lambda surface: "9.8")
        self.cfg = config(root)
        self.fs, self.clock = LocalFileSystem(), Time()
        self.exec = Exec(self.fs, self.clock)
        self.journal = Journal(self.cfg.state_dir, self.clock)
        self.session = ProviderSession(self.cfg, journal=self.journal, clock=self.clock, sleep=self.clock.sleep, timers=Timers(journal=self.journal, clock=self.clock, sleep=self.clock.sleep))
        self.client = ProviderLLM(snapshot_config(self.cfg) if snapshot else self.cfg, exec_=self.exec, fs=self.fs, env=ENV, cwd=root, timeout=601, session=self.session)
        self.store = EvidenceStore(self.cfg.state_dir, self.fs, self.fs.read_bytes, self.fs.size, Redactor.from_config(self.cfg, ENV).scrub)
        self.root = root

    def request(self, surface="review"):
        return LLMRequest(surface, f"prompt 雪 {SECRET}", "medium", "high", "ticket", self.root if surface == "implement" else None)

    async def call(self, surface="review", call_seq=4):
        return await llm_call(Effects(self.journal), self.client, self.request(surface), Redactor.from_config(self.cfg, ENV), ticket="ticket", stem="ticket", run_seq=3, attempt=2, call_seq=call_seq)

    def record(self, kind="end", surface="review", suffix=""):
        return self.store.read_record(f"llm/ticket/3/{surface}/2/4{suffix}", kind)

    def scratch(self):
        return self.fs.entries(self.store.root / "scratch")


def test_start_record_precedes_spawn(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)

    def check():
        # Rules out deferred publication after exec returns.
        assert rig.fs.entries(rig.store.root / "calls" / quote(KEY, safe="")) == ["start.json"]

    rig.exec.spawn_check = check
    asyncio.run(rig.call())
    start = rig.record("start")
    # Rules out request-local identity, swapped git refs, and an unscrubbed stdin copy.
    assert (start.id, start.group, start.run_seq, start.surface, start.attempt, start.call, start.stem) == (KEY, "ticket", 3, "review", 2, 4, "ticket")
    assert start.repo.model_dump() == {"main_sha": "1" * 40, "base_sha": "2" * 40, "tree_before": "b" * 40}
    assert rig.store.get_blob(start.prompt.blob) == "prompt 雪 [REDACTED:KEY]".encode()
    assert (start.prompt.chars, start.prompt.bytes, start.engine.model_dump(), start.clock.wall_start) == (
        23,
        25,
        {"version": "engine-test", "spec": "review.md", "spec_version": "9.8"},
        "2026-02-03T04:05:06.123000+00:00",
    )


@pytest.mark.parametrize("codex", [False, True])
def test_end_record_on_success(tmp_path, monkeypatch, codex):
    rig = Rig(tmp_path, monkeypatch)
    if codex:
        rig.session.auth_excluded.add("claude")
    rig.exec.out = stream(codex=codex)
    result = asyncio.run(rig.call())
    end = rig.record()
    # Rules out default counts, missing arrivals, parsed totals from another provider, and nested model guesses.
    assert (end.exit.model_dump(), end.repo, end.rusage) == ({"status": "ok", "code": 0, "signal": None, "failure_class": None}, None, None)
    assert rig.store.get_blob(end.raw.stdout).decode() == rig.exec.out
    assert (end.raw.lines, end.raw.non_json_lines, json.loads(rig.store.get_blob(end.raw.stdout_times))) == (3 if codex else 2, 0, [7000000, 14000000, 21000000] if codex else [7000000, 14000000])
    assert (end.parsed.input_tokens, end.parsed.output_tokens, end.parsed.text_chars, end.parsed.usd) == (result["input_tokens"], result["output_tokens"], 6, None if codex else 0.73)
    assert (end.model.served, end.model.served_source, end.native_ids.session_id, end.native_ids.thread_id) == (
        (None, "none", None, "native-thread") if codex else ("served-claude", "stream", "native-session", None)
    )


def test_writing_call_records_trees_and_cleans_scratch(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    asyncio.run(rig.call("implement"))
    # Rules out using HEAD in place of dirty trees, swapped before/after and the real git index.
    assert (rig.record("start", "implement").repo.tree_before, rig.record(surface="implement").repo.model_dump()) == ("b" * 40, {"tree_after": "a" * 40, "changed_paths": ["changed.py", "other.txt"]})
    indexes = [kwargs["env"]["GIT_INDEX_FILE"] for argv, kwargs in rig.exec.calls if "add" in argv or "write-tree" in argv]
    assert len(indexes) == 4 and len(set(indexes)) == 1 and indexes[0].startswith(str(rig.store.root / "scratch") + "/")
    assert rig.scratch() == []


def test_keyless_calls_leave_no_record(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    asyncio.run(rig.client.call(rig.request()))
    asyncio.run(rig.client.preflight())
    # Rules out incidental records/git work for probes and leaked stdin files.
    assert (rig.fs.entries(rig.store.root / "calls"), rig.fs.entries(rig.cfg.state_dir / "spools"), rig.scratch(), [argv for argv, _ in rig.exec.calls if argv[0] == "git"]) == ([], [], [], [])


def test_records_and_blobs_carry_no_secret(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    rig.exec.out, rig.exec.err = stream(SECRET), f"stderr {SECRET}"
    asyncio.run(rig.call())
    records = [p.read_bytes() for p in (rig.store.root / "calls").rglob("*.json")]
    from compression import zstd

    blobs = [zstd.decompress(p.read_bytes()) for p in (rig.store.root / "blobs").rglob("*") if p.is_file()]
    # Rules out hashing/storing the original bytes and scrubbing only the result.
    assert SECRET.encode() not in b"".join(records + blobs)
    assert b"[REDACTED:KEY]" in rig.store.get_blob(rig.record().raw.stdout)


@pytest.mark.parametrize("failure", ["nonzero", "timeout", "cancel", "spawn", "consumer", "negative", "parse"])
def test_failed_calls_still_end(tmp_path, monkeypatch, failure):
    rig = Rig(tmp_path, monkeypatch)
    expected = ProviderCallError
    if failure == "nonzero":
        rig.exec.rc, rig.exec.err = 7, "rate limit reached"
    elif failure == "negative":
        rig.exec.rc = -9
    elif failure == "parse":
        rig.exec.out = "not JSON\n[]\n"
    else:
        error = {"timeout": TimeoutError, "cancel": asyncio.CancelledError, "spawn": lambda: ExecutableNotFound("claude"), "consumer": RuntimeError}[failure]()
        error.process_capture = (f"partial {SECRET}", "partial error")
        rig.exec.error, expected = error, type(error)
    with pytest.raises(expected) as caught:
        asyncio.run(rig.call())
    end = rig.record()
    # Rules out exceptional paths skipping end publication or classifying all failures as nonzero.
    status = "killed" if failure in {"negative", "cancel", "consumer"} else "ok" if failure == "parse" else "spawn_error" if failure == "spawn" else failure
    assert (end.exit.status, end.exit.code, end.exit.signal, end.exit.failure_class) == (
        status,
        rig.exec.rc if failure in {"nonzero", "negative", "parse"} else None,
        9 if failure == "negative" else None,
        "rate_limited" if failure == "nonzero" else "unclassified" if failure in {"negative", "parse"} else None,
    )
    assert rig.store.get_blob(end.raw.stdout).decode() == (rig.exec.out if failure in {"nonzero", "negative", "parse"} else "partial [REDACTED:KEY]")
    assert rig.scratch() == []
    if rig.exec.error is not None:
        assert caught.value is rig.exec.error


def test_reexecuted_key_never_overwrites(tmp_path, monkeypatch):
    rig = Rig(tmp_path, monkeypatch)
    asyncio.run(rig.call())
    directory = rig.store.root / "calls" / quote(KEY, safe="")
    before = {p.name: p.read_bytes() for p in directory.iterdir()}
    rig.exec.out = stream("second distinct answer")

    # Effects normally replays; direct re-entry models the crash window before completion.
    async def effect(operation):
        return await operation()

    asyncio.run(rig.client.admitted_call(rig.request(), ticket="ticket", call_key=KEY, effect=effect))
    # Rules out replacement and exposing the storage suffix as journal identity.
    assert {p.name: p.read_bytes() for p in directory.iterdir()} == before
    assert (rig.record("start", suffix="#2").id, rig.store.get_blob(rig.record(suffix="#2").raw.stdout).decode()) == (KEY, rig.exec.out)


@pytest.mark.parametrize("reason", ["first", "failover", "spill", "breaker"])
def test_route_fields(tmp_path, monkeypatch, reason):
    rig = Rig(tmp_path, monkeypatch, snapshot=True)
    held = None

    async def run():
        nonlocal held
        if reason == "failover":
            rig.session.auth_excluded.add("claude")
        elif reason == "breaker":
            from clutch.thresh import Breaker

            monkeypatch.setattr(rig.session.thresh, "breakers", lambda: {"claude": Breaker(open_until=rig.clock() + timedelta(seconds=30))})
        elif reason == "spill":
            held = await rig.session.thresh.admit([providers.candidates(rig.cfg, "medium", "review")[0]], ticket="other", call_key="held", projected_wait_seconds=0)
        rig.exec.out = stream(codex=reason != "first")
        try:
            await rig.call()
        finally:
            if held:
                rig.session.thresh.release(held)

    asyncio.run(run())
    route = rig.record("start").route
    # Rules out sorting candidates, labeling every alternate as failover, and hashing the mutable Config repr.
    assert route.model_dump() == {
        "tier": "medium",
        "effort": "high",
        "candidates": ["claude", "codex"],
        "chosen": "claude" if reason == "first" else "codex",
        "reason": "failover" if reason == "breaker" else reason,
        "config_sha": hashlib.sha256(repr(snapshot_config(rig.cfg)).encode()).hexdigest(),
    }


@pytest.mark.parametrize("preflight", [False, True])
def test_cli_version_from_preflight(tmp_path, monkeypatch, preflight):
    rig = Rig(tmp_path, monkeypatch)
    if preflight:
        asyncio.run(rig.client.preflight())
    asyncio.run(rig.call())
    # Rules out raw version banners and using empty string for an unprobed adapter.
    assert rig.record("start").provider.cli_version == ("1.2.3" if preflight else None)


def test_llm_call_log_events_carry_call_key(tmp_path):
    cfg = config(tmp_path)
    clock = Time()

    class Reply(BaseModel):
        text: str

    driver = Driver.from_config(cfg, journal=Journal((cfg).state_dir, clock), llm=FakeLLM(["invalid", '{"text":"valid"}']), env=ENV, clock=clock, sleep=clock.sleep)
    stage = LlmStage("review", Reply, [], lambda *_: "prompt")
    asyncio.run(driver.run(stage, None, ticket="ticket", attempt=2, workspace=tmp_path, tier="medium", effort="high", stuck_budget=100, expected_budget=50, scope_fence=()))
    events = [json.loads(line) for line in (cfg.state_dir / "engine.log").read_text().splitlines()]
    # Rules out per-stage keys, duplicated call numbers, and contaminating stage events.
    assert [e["call_key"] for e in events if e["event"] == "llm_call"] == [llm_key("ticket", 0, "review", 2, n) for n in (1, 2)]
    assert [(e["event"], "call_key" in e) for e in events if e["event"] in {"stage_start", "stage_end"}] == [("stage_start", False), ("stage_end", False)]


def test_latest_stdout(tmp_path):
    seed_end(tmp_path, "llm/a/0/review/0/1", "old a", "2026-01-01")
    store = seed_end(tmp_path, "llm/a/1/review/0/1", "new a", "2026-01-02")
    seed_end(tmp_path, "llm/b/0/review/0/1", "later b", "2026-01-03")
    # Rules out selecting the globally newest or lexically first record.
    assert (store.latest_stdout("llm/a/"), store.latest_stdout("llm/c/")) == ("new a", "")
    seed_end(tmp_path, "llm/a/2/review/0/1", "tie wins", "2026-01-02")
    assert store.latest_stdout("llm/a/") == "tie wins"
    store.fs.remove(store._blob_path(store.read_record("llm/a/2/review/0/1", "end").raw.stdout))
    # Rules out falling back to older stdout after retention removed the newest blob.
    assert store.latest_stdout("llm/a/") == ""
    store.fs.write(store._record_path("llm/a/future", "end"), b'{"schema":"clutch.evidence.call/2.0"}')
    store.fs.write(store._record_path("llm/a/inflight", "start"), b"{}")
    assert store.latest_stdout("llm/a/") == ""
