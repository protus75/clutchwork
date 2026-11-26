# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Integration test that the antigravity provider passes preflight, invokes agy in plan or auto mode without pnpm, parses usage and records session and model evidence.
# relates: [clutch/config.py, clutch/evidence/store.py, clutch/llm.py, clutch/providers.py, clutch/redact.py, tests/config_fixture.py, tests/fakes.py]
# owner: clutch/providers.py
# verified: db2c0f62
# hash: 615dc9c5894e3df23e567db6d2aca3c27fd989c9fb6de5b83c27d5802a77f35b
import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from clutch.config import load_config_text
from clutch.evidence.store import EvidenceStore
from clutch.llm import LLMRequest
from clutch.providers import CallCapture, ProviderLLM
from clutch.redact import Redactor
from tests.config_fixture import build_config
from tests.fakes import FakeClock, FakeFileSystem
from tests.git_fake import GitFake

STREAM = '{"event":"init","conversation_id":"session-1","init":{"model":"served"}}\n{"event":"result","result":{"status":"SUCCESS","response":"pong","usage":{"input_tokens":12,"cache_read_tokens":5,"output_tokens":3}}}\n'


def test_calls_preflight_and_capture():
    root = Path("/repo")
    text = build_config(
        providers=[{"name": "antigravity", "models": dict.fromkeys(("low", "medium", "high", "max"), "requested"), "limits": {"concurrency": 1, "est_cost_per_call_usd": 0.5}}],
        routing=[{"tier": "low", "surface": surface, "candidates": [{"provider": "antigravity"}]} for surface in ("review", "implement")],
    ).replace("    package: test-cli\n", "")
    cfg = load_config_text(text, path=root / "config.yaml", cwd=root)
    fs, clock = FakeFileSystem(), FakeClock()

    class Exec:
        def __init__(self):
            self.calls = []

        async def run(self, argv, **kwargs):
            self.calls.append((argv, kwargs))
            if argv[-1] == "--version":
                return 0, "agy 1.2.3", ""
            if kwargs.get("on_stdout_line"):
                for line in STREAM.splitlines():
                    kwargs["on_stdout_line"](line)
            return 0, STREAM, ""

    exec_ = Exec()
    session = SimpleNamespace(thresh=SimpleNamespace(configure=Mock()), exclusions=lambda: set(), preflight_passed=Mock())
    client = ProviderLLM(cfg, exec_=exec_, fs=fs, env={"PATH": "/bin"}, cwd=root, timeout=10, session=session)
    git = GitFake(tree_id="tree", rev_parse="sha", tree_changes=[])
    capture = CallCapture("llm/ticket/1/review/1/1", "ticket", ("antigravity",), "first", git, clock)
    read = LLMRequest(surface="review", rendered="hello", tier="low", effort="low", subject="ticket", worktree=None)
    write = LLMRequest(surface="implement", rendered="change", tier="low", effort="low", subject="ticket", worktree=root / "worktree")

    async def run():
        assert await client.preflight() == []
        result = await client._adapters["antigravity"].invoke(read, "requested", capture=capture)
        await client.call(write)
        return result

    result = asyncio.run(run())
    assert (result.text, result.model, result.input_tokens, result.output_tokens) == ("pong", "served", 17, 3)
    assert exec_.calls[0][0] == ["agy", "--version"]
    assert all(argv[0] != "pnpm" for argv, _ in exec_.calls)
    assert exec_.calls[-2][0][-1] == "plan" and exec_.calls[-1][0][-2:] == ["auto", "--dangerously-skip-permissions"]
    store = EvidenceStore(cfg.state_dir, fs, fs.read_bytes, fs.size, Redactor({}).scrub)
    start, end = store.read_record(capture.key, "start"), store.read_record(capture.key, "end")
    assert start.native_ids.session_id == end.native_ids.session_id == "session-1"
    assert end.model.served == "served"
