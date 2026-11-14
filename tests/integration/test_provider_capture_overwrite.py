import asyncio
from dataclasses import replace

from tests.integration.test_providers import FakeExec, claude_ok, config, llm, req


def test_capture_survives_new_process(tmp_path):
    cfg = config(tmp_path)
    first = llm(cfg, FakeExec((0, claude_ok("first run"), "")), tmp_path)
    second = llm(cfg, FakeExec((0, claude_ok("second run"), "")), tmp_path)
    asyncio.run(first.call(req("review")))
    asyncio.run(second.call(req("review")))

    root = cfg.state_dir / "spools/providers/t-1"
    captures = sorted(root.rglob("events.jsonl"))
    assert captures == [root / "claude-0001/events.jsonl", root / "claude-0002/events.jsonl"]
    assert "first run" in captures[0].read_text()
    assert "second run" in captures[1].read_text()


def test_capture_numbers_are_per_stem(tmp_path):
    cfg = config(tmp_path)
    client = llm(cfg, FakeExec((0, claude_ok("first"), ""), (0, claude_ok("second"), "")), tmp_path)
    asyncio.run(client.call(req("review")))
    asyncio.run(client.call(replace(req("review"), ticket="t-2")))

    root = cfg.state_dir / "spools/providers"
    assert sorted(p.relative_to(root).as_posix() for p in root.rglob("events.jsonl")) == [
        "t-1/claude-0001/events.jsonl",
        "t-2/claude-0001/events.jsonl",
    ]
