"""Roadmap table contracts, using only in-memory documents."""

from dataclasses import replace

import pytest

from clutch.roadmap import choose, depends_on, link, parse, plan_path, strike
from clutch.runner import Refusal

HEADER = "| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n|---|---|---|---|---|---|---|---|\n"


def row(n, stem, *, owner="roadmap", kind="feature", priority="P1", depends="", before="", content="Work."):
    return f"| {n} | {stem} | {owner} | {kind} | {priority} | {depends} | {before} | {content} |\n"


def document(*rows):
    return "### Next\n\n" + HEADER + "".join(rows)


def edited_only(original, changed, selected):
    before, after = original.splitlines(keepends=True), changed.splitlines(keepends=True)
    assert len(before) == len(after)
    assert before[selected.line] != after[selected.line]
    assert all(a == b for i, (a, b) in enumerate(zip(before, after, strict=True)) if i != selected.line)


def test_parse_reads_master_tables():
    text = (
        "| Release | Theme |\n|---|---|\n| bad | table |\n"
        + document(
            row(1, "`a-row`", owner="driver plan", kind="chore", priority="P2", before="`b-row`", content="Run `cmd --a|--b`."),
            row("(56)", "`cond-row`"),
            row(35, "(re-measure)"),
            row(2, "`b-row`", before="every feature ticket below"),
        )
        + "```gate\n./dev.py test\n```\n### Later, last group\n"
        + HEADER
        + row(3, "`c-row`")
    )
    rows = parse(text)
    assert [(r.number, r.release, r.stem, r.owner, r.kind, r.priority, r.runs_before, r.content) for r in rows] == [
        (1, "Next", "a-row", "driver plan", "chore", "P2", ("b-row",), "Run `cmd --a|--b`."),
        (2, "Next", "b-row", "roadmap", "feature", "P1", (), "Work."),
        (3, "Later, last group", "c-row", "roadmap", "feature", "P1", (), "Work."),
    ]


def test_parse_linked_and_struck():
    text = document(
        row(1, "[`a-row`](../tickets/a-row/)"),
        row(2, "`b-row`", content="**Authored** (`tickets/b-row/`). Work."),
        row(3, "`c-row`", content="**Authored** (`tickets/c-split/`). Work."),
        row(4, "~~`d-row`~~", content="**Merged** (`tickets/d-row/`). Work."),
        row("~~5~~", "~~`e-row`~~", content="~~Work.~~"),
        row(6, "`f-row`", content="~~Work.~~"),
        row(7, "`g-row`"),
        row(8, "`i-row`", content="`tickets/i-row/evidence/x.txt`"),
    )
    rows = parse(text)
    assert [(r.linked, r.struck) for r in rows] == [(True, False), (True, False), (False, False), (True, True), (False, True), (False, True), (False, False), (False, False)]
    assert [(r.number, r.stem, r.content) for r in rows[3:6]] == [(4, "d-row", "**Merged** (`tickets/d-row/`). Work."), (5, "e-row", "Work."), (6, "f-row", "Work.")]


def test_parse_refuses():
    with pytest.raises(Refusal, match="restore header"):
        parse("nothing")
    with pytest.raises(Refusal, match="number: 4"):
        parse(document(row(4, "`a`"), row(4, "`b`")))
    with pytest.raises(Refusal, match="stem: dup-row"):
        parse(document(row(1, "`dup-row`"), row(2, "`dup-row`")))


def test_depends_on():
    rows = parse(document(row(2, "`a`"), row(3, "`b`"), row(4, "`c`")))
    assert depends_on(replace(rows[2], depends="rows 2-3, `x-row`"), rows) == ("a", "b", "x-row")
    assert depends_on(replace(rows[2], depends="row 2"), rows) == ("a",)
    assert depends_on(rows[2], rows) == ()
    for value, match in [("rows 7-8", "7"), ("after the hand test", "after the hand test"), ("rows 3-2", "rows 3-2")]:
        with pytest.raises(ValueError, match=match):
            depends_on(replace(rows[2], depends=value), rows)


def test_link_and_strike_edit_one_line():
    text = document(row(1, "`a-row`", content="Run `cmd --a|--b` here."), row(2, "`c-row`", content="**Authored** (`tickets/c-split/`). Work."), row(3, "[`d-row`](../tickets/d-row/)"))
    a, c, d = parse(text)
    linked = link(text, a)
    edited_only(text, linked, a)
    a2 = parse(linked)[0]
    assert a2 == replace(a, linked=True, content="**Authored** (`tickets/a-row/`). Run `cmd --a|--b` here.")
    assert link(linked, a2) == linked
    split = link(text, c)
    edited_only(text, split, c)
    assert parse(split)[1].content == "**Authored** (`tickets/c-split/`, `tickets/c-row/`). Work."
    merged = strike(linked, a2)
    edited_only(linked, merged, a2)
    assert "~~`a-row`~~" in merged
    assert parse(merged)[0] == replace(a2, struck=True, content="**Merged** (`tickets/a-row/`). Run `cmd --a|--b` here.")
    assert "|  |  |" in merged
    assert strike(merged, parse(merged)[0]) == merged
    plain = strike(text, a)
    edited_only(text, plain, a)
    assert parse(plain)[0].content.startswith("**Merged** (`tickets/a-row/`).")
    md = strike(text, d)
    edited_only(text, md, d)
    assert "~~[`d-row`](../tickets/d-row/)~~" in md
    assert parse(md)[2].struck and parse(md)[2].linked
    assert strike(md, parse(md)[2]) == md


def test_plan_path():
    files = {"docs/roadmap-driver-plan.md", "docs/stage-panels-plan.md", "docs/how-clutch-works.md", "docs/roadmap.md"}
    assert plan_path("driver plan 3", files) == "docs/roadmap-driver-plan.md"
    assert plan_path("panels plan 5", files) == "docs/stage-panels-plan.md"
    assert plan_path("roadmap (decision 4)", files) == "docs/roadmap.md"
    assert plan_path("works plan 1", files) is None
    assert plan_path("panel plan 2", files) is None
    assert plan_path("", files) is None
    assert plan_path("driver plan 3", files | {"docs/driver-extra-plan.md"}) is None


def test_choose_partitions_rows():
    text = (
        document(
            row(1, "`done`", content="**Authored** (`tickets/done/`). Work."),
            row(2, "`satisfied`"),
            row(3, "`link`"),
            row(4, "`open`", content="**Authored** (`tickets/open/`). Work."),
            row(5, "`reject`", content="**Authored** (`tickets/reject/`). Work."),
            row(6, "`blocked`"),
            row(7, "`dependent`", depends="`open`"),
            row(8, "~~`struck`~~"),
            row(9, "`p2`", priority="P2", depends="row 8"),
            row(10, "`p1`"),
            row(11, "`bad`", kind="evidence"),
        )
        + "### Later, last group\n"
        + HEADER
        + row(12, "`later`", priority="P0")
    )
    rows = parse(text)
    states = {"done": "merged", "satisfied": "already_satisfied", "reject": "rejected", "blocked": "blocked"}
    files = {"tickets/link/ticket.md"}
    choice = choose(rows, states=states, files=files)
    assert [r.stem for r in choice.strike] == ["done", "satisfied"]
    assert [r.stem for r in choice.link] == ["link"]
    assert choice.open == 2
    assert [r.stem for r in choice.ready] == ["p1", "p2"]
    assert {w.row.stem for w in choice.waits} == {"reject", "blocked", "bad"}
    assert "journal" in next(w.reason for w in choice.waits if w.row.stem == "blocked")
    assert "new stem" in next(w.road for w in choice.waits if w.row.stem == "reject")
    states = {r.stem: "merged" for r in rows if r.release == "Next"} | {"reject": "rejected", "blocked": "rejected"}
    choice = choose(rows, states=states, files=files)
    assert [r.stem for r in choice.ready] == ["later"]
    assert [w.row.stem for w in choice.waits] == ["reject", "blocked"]


def test_choose_split_row():
    rows = parse(document(row(1, "`s-row`", content="**Authored** (`tickets/s-row/`, `tickets/s-two/`). Work."), row(2, "`t-row`", depends="row 1")))
    choice = choose(rows, states={"s-row": "merged", "s-two": "running"}, files=set())
    assert choice.open == 1 and choice.strike == () and choice.link == () and choice.ready == () and choice.waits == ()
    choice = choose(rows, states={"s-row": "merged", "s-two": "merged"}, files=set())
    assert [r.stem for r in choice.strike] == ["s-row"]
    assert [r.stem for r in choice.ready] == ["t-row"]


def test_choose_hand_test_refusal():
    rows = parse(
        document(
            row(1, "`h-row`", content="after the hand test `tickets/h-row/evidence/a0.txt`"),
            row(2, "`g-row`", content="after its agent capture"),
            row(3, "`hand-row`", content="after its hand test"),
            row(4, "`b-row`", kind="bug"),
            row(5, "`n-row`", content="`tickets/n-row/evidence/x.txt`"),
        )
    )
    choice = choose(rows, states={}, files={"tickets/h-row/evidence/other.txt"})
    assert not choice.ready and len(choice.waits) == 5
    assert "tickets/h-row/evidence/a0.txt" in choice.waits[0].reason
    assert "tickets/g-row/evidence/" in choice.waits[1].road
    assert "tickets/hand-row/evidence/" in choice.waits[2].road
    assert "observed failure" in choice.waits[3].road
    files = {"tickets/h-row/evidence/a0.txt", "tickets/g-row/evidence/capture.txt", "tickets/hand-row/evidence/capture.txt", "tickets/b-row/evidence/failure", "tickets/n-row/evidence/x.txt"}
    assert [r.stem for r in choose(rows, states={}, files=files).ready] == ["h-row", "g-row", "hand-row", "b-row", "n-row"]


def test_choose_waits_on_plan_and_depends():
    rows = parse(document(row(1, "`plan`", owner="unknown plan"), row(2, "`dep`", depends="see notes"), row(3, "`priority`", priority="P9")))
    choice = choose(rows, states={}, files=set())
    assert choice.ready == ()
    assert "docs/*-plan.md" in choice.waits[0].road
    assert "see notes" in choice.waits[1].reason
    assert "P9" in choice.waits[2].reason
