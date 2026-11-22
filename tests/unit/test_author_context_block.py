# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Checks every outcome of the Author context_suggest block (its format, ranking, none, unavailable, read-only connection that is always closed) and that it is computed once per request across re-prompts
# relates: [clutch/author.py, clutch/box.py, tests/fakes.py, tests/unit/test_retro_recurrence.py]
# owner: engine
# verified: bc0baafb
# hash: 7ae10c94385eefdc63a2a4abb50eb747fc01b6330ac7c3fd3c7e0318168e072b
import asyncio
from pathlib import Path
from types import SimpleNamespace

import duckdb
import pytest

from clutch import author
from clutch.box import RoadmapRow
from tests.fakes import FakeJournal
from tests.git_fake import GitFake
from tests.unit.test_retro_recurrence import message


def index_file(tmp_path, chunks):
    with duckdb.connect(str(tmp_path / "index.duckdb")) as conn:
        conn.execute("CREATE TABLE files (path VARCHAR)")
        conn.execute("CREATE TABLE chunks (path VARCHAR, selector VARCHAR, text VARCHAR)")
        conn.execute("CREATE TABLE touches (ticket VARCHAR, path VARCHAR)")
        for selector, text in chunks:
            path = selector.split("::")[0]
            conn.execute("INSERT INTO files VALUES (?)", [path])
            conn.execute("INSERT INTO chunks VALUES (?, ?, ?)", [path, selector, text])


def test_suggested_exact_format_and_read_only_connection(tmp_path):
    index_file(tmp_path, [("clutch/index.py::build", "index build")])
    connections = []

    def connect(path, *, read_only):
        connections.append((path, read_only))
        return duckdb.connect(path, read_only=read_only)

    # Wrong: bare path, extra space, blank first line, or trailing newline.
    assert author.context_block(tmp_path, "Build `index.build` in `clutch/index.py`", "demo", connect=connect) == "- clutch/index.py::build  # matches build, index"
    # Wrong: opening a writable database or a different state directory.
    assert connections == [(str(tmp_path / "index.duckdb"), True)]


@pytest.mark.parametrize("text", ["Build index.build in clutch/index.py", "`unmatched.words`"])
def test_no_matches_is_none(tmp_path, text):
    index_file(tmp_path, [("clutch/index.py::build", "index build")])
    # Wrong: matching outside backticks, returning an empty string, or ignoring search terms.
    assert author.context_block(tmp_path, text, "demo") == "none"


def test_blank_skips_index(tmp_path):
    def forbidden(*args, **kwargs):
        pytest.fail("blank text opened the index")

    index_file(tmp_path, [("clutch/index.py::build", "index build")])
    # Wrong: querying the index for blank text or returning unavailable instead of none.
    assert author.context_block(tmp_path, " \n\t", "demo", connect=forbidden) == "none"


@pytest.mark.parametrize("case", ["missing", "connect_error", "missing_chunks", "invalid_state"])
def test_unavailable_outcomes(tmp_path, case):
    def broken(*args, **kwargs):
        raise duckdb.Error("unreadable")

    if case != "missing":
        with duckdb.connect(str(tmp_path / "index.duckdb")) as conn:
            conn.execute("CREATE TABLE files (path VARCHAR)")
    state = None if case == "invalid_state" else tmp_path
    kwargs = {"connect": broken} if case == "connect_error" else {}
    expected = "unavailable: no_index (run clutch index build)" if case == "missing" else "unavailable: index_unreadable"
    # Wrong: raising, collapsing missing/unreadable, or silently returning none.
    assert author.context_block(state, "`index.build`", "demo", **kwargs) == expected


def test_ranked_sections_only(tmp_path):
    index_file(
        tmp_path,
        [
            (f"clutch/index.py::{name}", text)
            for name, text in [
                ("zulu", "index build clutch"),
                ("echo", "index build"),
                ("delta", "index build"),
                ("charlie", "index build"),
                ("bravo", "index build"),
                ("alpha", "index build"),
                ("aardvark", "index build"),
            ]
        ],
    )
    # Wrong: insertion order, selector-only order, more/fewer than five, or co-changed files.
    assert author.context_block(tmp_path, "`index.build` `clutch/index.py`", "demo") == "\n".join(
        ["- clutch/index.py::zulu  # matches build, clutch, index"] + [f"- clutch/index.py::{name}  # matches build, index" for name in ["aardvark", "alpha", "bravo", "charlie"]]
    )


@pytest.mark.parametrize("query_error", [False, True])
def test_connection_closed_even_on_query_error(tmp_path, query_error):
    index_file(tmp_path, [])
    closed = []

    class Connection:
        def close(self):
            closed.append(True)

    def suggest(*args):
        if query_error:
            raise RuntimeError("query failed")
        return [("wrong.py", "co-changed")], [("right.py::name", "matches right, name")]

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(author.context, "suggest", suggest)
        result = author.context_block(tmp_path, "`right.name`", "demo", connect=lambda *args, **kwargs: Connection())
    # Wrong: rendering co-changed files or leaking non-DuckDB query failures.
    assert result == ("unavailable: index_unreadable" if query_error else "- right.py::name  # matches right, name")
    # Wrong: leaking connections on success or exception.
    assert closed == [True]


@pytest.mark.parametrize("roadmap", [False, True])
def test_author_uses_request_text_and_stem_once_across_reprompt(tmp_path, monkeypatch, roadmap):
    index_file(tmp_path, [("clutch/index.py::build", "index build"), ("clutch/fault.py::repair", "fault repair"), ("clutch/other.py::wrong", "other wrong")])
    captured, calls, suggest_calls = [], [], []
    real_block, real_suggest = author.context_block, author.context.suggest

    def counted(state_dir, text, stem):
        calls.append((state_dir, text, stem))
        return real_block(state_dir, text, stem)

    def suggest(conn, stem, fence, context, goal):
        suggest_calls.append((stem, fence, context, goal))
        return real_suggest(conn, stem, fence, context, goal)

    async def ls_files(repo):
        return ["docs/plan.md"]

    async def open_tickets(checkout):
        return "none"

    async def run(stage, *args, **kwargs):
        stage.render(None, [])
        stage.render(None, [])
        raise StopAsyncIteration

    monkeypatch.setattr(Path, "read_text", lambda self: "spec")
    monkeypatch.setattr(author, "load_spec", lambda text: SimpleNamespace(meta=SimpleNamespace(effort="medium")))
    monkeypatch.setattr(author, "render", lambda spec, values: captured.append(values) or "rendered")
    monkeypatch.setattr(author, "list_open_tickets", open_tickets)
    monkeypatch.setattr(author, "template", lambda kind: "skeleton")
    monkeypatch.setattr(author, "context_block", counted)
    monkeypatch.setattr(author.context, "suggest", suggest)
    row = RoadmapRow(number=191, release="0.5", stem="row-stem", owner="engine", kind="feature", priority="P2", content="Build `index.build`", plan="docs/plan.md")
    summary, rationale = ("`other.wrong`", "irrelevant") if roadmap else ("Fix `fault`", "Needs `repair`")
    item = message().model_copy(
        update={
            "message_class": "roadmap_row" if roadmap else "bug_report",
            "roadmap_row": row if roadmap else None,
            "summary": summary,
            "verdict": SimpleNamespace(rationale=rationale),
            "bug_origin": "player",
            "has_repro": True,
        }
    )
    checkout = SimpleNamespace(repo=tmp_path, git=GitFake(ls_files=ls_files), journal=FakeJournal(), config=SimpleNamespace(state_dir=tmp_path, routing_default_tier="medium"))
    with pytest.raises(StopAsyncIteration):
        asyncio.run(author.author(checkout, SimpleNamespace(run=run), SimpleNamespace(root=tmp_path), item, 1))
    text, stem = (row.content, row.stem) if roadmap else (summary + "\n" + rationale, "")
    # Wrong: summary for rows, missing rationale/newline, wrong stem, or recomputing on re-prompt.
    assert calls == [(tmp_path, text, stem)]
    # Wrong: inventing a fence/Context before drafting or passing the wrong stem to suggest.
    assert suggest_calls == [(stem, [], [], text)]
    expected = "- clutch/index.py::build  # matches build, index" if roadmap else "- clutch/fault.py::repair  # matches fault, repair"
    # Wrong: dropping the block on one prompt or selecting the other request's sections.
    assert [values["context_suggest"] for values in captured] == [expected, expected]
