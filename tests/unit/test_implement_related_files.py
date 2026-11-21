# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Implement index hint outcomes and bounds
# relates: [clutch/config.py, clutch/context.py, clutch/stages.py]
# owner: engine
# verified: a0d5e388
# hash: 7c49c6c13f804129c56c1492bb5b9bf8e026f80a43a8ac6d56d2cd866518f115
import asyncio
import threading
from types import SimpleNamespace

import duckdb
import pytest
from pydantic import ValidationError

from clutch import context, stages
from clutch.config import Index


def index_file(tmp_path, count=1):
    with duckdb.connect(str(tmp_path / "index.duckdb")) as conn:
        conn.execute("CREATE TABLE files (path VARCHAR)")
        conn.execute("CREATE TABLE chunks (path VARCHAR, selector VARCHAR, text VARCHAR)")
        conn.execute("CREATE TABLE touches (ticket VARCHAR, path VARCHAR)")
        paths = ["clutch/index.py"] + ["clutch/merge.py" if i == 0 else f"clutch/file{i}.py" for i in range(count)]
        conn.executemany("INSERT INTO files VALUES (?)", [(p,) for p in paths])
        conn.executemany("INSERT INTO touches VALUES (?, ?)", [(t, p) for t in ("a", "b") for p in paths])
        conn.executemany(
            "INSERT INTO chunks VALUES (?, ?, ?)", [("clutch/index.py", f"clutch/index.py::{name}", "index build") for name in (["build"] if count == 1 else [f"build{i}" for i in range(count)])]
        )


def test_exact_and_no_terms(tmp_path):
    index_file(tmp_path)
    calls = []

    def connect(path, *, read_only):
        calls.append((path, read_only))
        return duckdb.connect(path, read_only=read_only)

    # Wrong: writable connection, sections first, a missing reason, or altered spacing.
    assert (
        context.hint_block(tmp_path, "demo", ["clutch/index.py"], [], "`index.build`", connect=connect)
        == "- clutch/merge.py  # changed with clutch/index.py in 2 past tickets\n- clutch/index.py::build  # matches build, index"
    )
    assert calls == [(str(tmp_path / "index.duckdb"), True)]
    # Wrong: suppress co-changes with no terms or match unquoted terms.
    assert context.hint_block(tmp_path, "demo", ["clutch/index.py"], [], "index build") == "- clutch/merge.py  # changed with clutch/index.py in 2 past tickets"
    assert context.hint_block(tmp_path, "demo", [], [], "index build") == "none"


def test_outcomes(tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("opened index")

    # Wrong: touching the index for blank text or conflating missing and unreadable.
    assert context.hint_block(tmp_path, "x", [], [], "  ", connect=forbidden) == "none"
    assert context.hint_block(tmp_path, "x", [], [], "text") == "unavailable: no_index (run clutch index build)"
    with duckdb.connect(str(tmp_path / "index.duckdb")) as conn:
        conn.execute("CREATE TABLE files (path VARCHAR)")

    def broken(*args, **kwargs):
        raise duckdb.Error("bad")

    for state, connect in [(tmp_path, broken), (tmp_path, duckdb.connect), (None, duckdb.connect)]:
        assert context.hint_block(state, "x", [], [], "text", connect=connect) == "unavailable: index_unreadable"


def test_limits_and_whitespace(tmp_path, monkeypatch):
    index_file(tmp_path, 7)
    result = context.hint_block(tmp_path, "demo", ["clutch/index.py"], [], "`index.build`")
    # Wrong: retaining all seven of each kind or reversing file and section groups.
    assert len(result.splitlines()) == 10
    assert "changed with" in result.splitlines()[0] and "matches" in result.splitlines()[-1]
    monkeypatch.setattr(context, "suggest", lambda *args: ([("long.py", "x" * 1000), ("newline.py", "first\nsecond")], []))
    lines = context.hint_block(tmp_path, "demo", [], [], "text").splitlines()
    # Wrong: preserving embedded newlines or exceeding the per-line limit.
    assert lines == ["- long.py  # " + "x" * 287, "- newline.py  # first second"]


def test_config():
    # Wrong: opting in by default or coercing arbitrary strings.
    assert Index().implement_hint is False
    assert Index(implement_hint=True).implement_hint is True
    with pytest.raises(ValidationError):
        Index(implement_hint="x")


def test_async_outcomes(tmp_path, monkeypatch):
    ticket = SimpleNamespace(stem="demo", scope_fence=("fence",), context=("context",), sections={"Goal / Why": "goal", "Scope in / Scope out": "scope"})
    config = SimpleNamespace(index=SimpleNamespace(implement_hint=False), state_dir=tmp_path)
    calls = []

    def hint(*args):
        calls.append(args)
        return "suggested"

    # Wrong: reading the index when disabled or passing the wrong query inputs.
    assert asyncio.run(stages.related_files(config, ticket, hint=hint)) == "none"
    assert calls == []
    config.index.implement_hint = True
    assert asyncio.run(stages.related_files(config, ticket, hint=hint)) == "suggested"
    assert calls == [(tmp_path, "demo", ["fence"], ["context"], "goal\nscope")]

    def broken(*args):
        raise RuntimeError("bad")

    assert asyncio.run(stages.related_files(config, ticket, hint=broken)) == "unavailable: index_unreadable"
    assert asyncio.run(stages.related_files(SimpleNamespace(), ticket, hint=hint)) == "unavailable: index_unreadable"
    release = threading.Event()
    monkeypatch.setattr(stages, "HINT_TIMEOUT_S", 0.05)

    async def timeout():
        try:
            return await asyncio.wait_for(stages.related_files(config, ticket, hint=lambda *args: release.wait()), 1)
        finally:
            release.set()

    assert asyncio.run(timeout()) == "unavailable: timeout"

    async def cancelled():
        started = threading.Event()
        blocker = threading.Event()

        def blocking(*args):
            started.set()
            blocker.wait()

        task = asyncio.create_task(stages.related_files(config, ticket, hint=blocking))
        while not started.is_set():
            await asyncio.sleep(0)
        task.cancel()
        try:
            with pytest.raises(asyncio.CancelledError):
                await task
        finally:
            blocker.set()

    asyncio.run(cancelled())
