# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Index additional source records and preserve incremental updates.
# relates: [clutch/box.py, tests/unit/test_index_build.py]
# owner: engine
# verified: 8c543cf0
# hash: 6d3c6615d1a8e0d0c1f21fed984fe13326fb2782a197e5512f02c435644028d5
import hashlib

import pytest

from clutch.box import Box, DecisionRecord, Resolution, render_record
from tests.unit.test_index_build import rig, rows, run  # noqa: F401

ROADMAP = (
    "# Roadmap\n"
    "| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n"
    "|---|---|---|---|---|---|---|---|\n"
    "| 1 | `first` | x | feature | P1 | - | - | First item |\n"
    "| ~~2~~ | ~~`second`~~ | x | feature | P2 | - | - | ~~Second item~~ |\n"
)


def put(rig, path, data):
    rig.fs.write(rig.root / path, data if isinstance(data, bytes) else data.encode())
    rig.git.paths.append(path)


def record(id, body):
    return render_record(DecisionRecord(id=id, kind="declined", link="ticket", reopen_after_days=3), body)


def box_messages(rig):
    box = Box(rig.config.state_dir / "box", rig.fs)
    first, _ = box.enqueue(message_class="suggestion", origin="one", summary="Same summary")
    second, _ = box.enqueue(message_class="suggestion", origin="two", summary="Same summary")
    third, _ = box.enqueue(message_class="suggestion", origin="three", summary="Resolved report")
    box.resolve(third, Resolution(kind="ticket", link="ticket"))
    return box, first, second, third


@pytest.mark.asyncio
async def test_roadmap_and_decisions(rig):
    put(rig, "docs/roadmap.md", ROADMAP)
    put(rig, "other.md", ROADMAP)
    put(rig, "tickets/decisions/d1.md", record("d1", "Body text here."))
    put(rig, "tickets/decisions/d2.md", record("d2", "\n\nBody text here."))
    put(rig, "tickets/decisions/blank.md", record("blank", "\n"))
    put(rig, "tickets/decisions/bad.md", "missing")
    put(rig, "tickets/decisions/binary.md", b"\xff")
    put(rig, "tickets/decisions/sub/d2.md", record("nested", "Nested"))
    put(rig, "tickets/decisions/d3.txt", "ignored")
    put(rig, "tickets/other.md", "# ignored")
    assert await run(rig) == []
    files = {r[0]: r for r in rows(rig, "files")}
    assert files["tickets/decisions/d1.md"][1:5] == ("decision", "Body text here.", "[]", "")
    assert files["tickets/decisions/d2.md"][2] == "Body text here."
    assert {"tickets/decisions/blank.md", "tickets/decisions/bad.md", "tickets/decisions/binary.md"} <= files.keys()
    assert not {"tickets/decisions/sub/d2.md", "tickets/decisions/d3.txt", "tickets/other.md"} & files.keys()
    chunks = rows(rig, "chunks")
    assert [r[1:] for r in chunks if r[0] == "docs/roadmap.md" and "#row " in r[1]] == [("docs/roadmap.md#row 1", "first: First item", 3), ("docs/roadmap.md#row 2", "second: Second item", 3)]
    assert any(r[1] == "docs/roadmap.md#Roadmap" for r in chunks)
    assert not any(r[0] == "other.md" and "#row " in r[1] for r in chunks)
    assert ("tickets/decisions/d1.md", "tickets/decisions/d1.md#d1", "Body text here.", 3) in chunks
    assert not any(r[0] in {"tickets/decisions/blank.md", "tickets/decisions/bad.md", "tickets/decisions/binary.md"} for r in chunks)


@pytest.mark.asyncio
@pytest.mark.parametrize("data", ["# Heading\nNo table", ROADMAP + "| 1 | `third` | x | feature | P1 | - | - | Duplicate |\n", ROADMAP.replace("| 1 |", "| ² |"), b"\xff"])
async def test_bad_roadmap(rig, data):
    put(rig, "docs/roadmap.md", data)
    assert await run(rig) == []
    assert not any(r[0] == "docs/roadmap.md" and "#row " in r[1] for r in rows(rig, "chunks"))
    if isinstance(data, str):
        assert any(r[1].startswith("docs/roadmap.md#") for r in rows(rig, "chunks"))


@pytest.mark.asyncio
async def test_incremental_box_and_embeddings(rig):
    rig.config.index.embed = ["fake"]
    put(rig, "docs/roadmap.md", ROADMAP)
    put(rig, "tickets/decisions/d1.md", record("d1", "Body text here."))
    box, first, second, third = box_messages(rig)
    duplicate = box.get(first).model_copy(update={"seq": 9, "summary": "Last version"})
    (box.root / "duplicate.json").write_text(duplicate.model_dump_json())
    assert await run(rig) == []
    files = {r[0]: r for r in rows(rig, "files")}
    assert {p for p in files if p.startswith("box:")} == {f"box:{i}" for i in (first, second, third)}
    assert files[f"box:{first}"][1:5] == ("box", "Last version", "[]", "one")
    assert files[f"box:{second}"][5] == hashlib.sha256(b"Same summary").hexdigest()
    chunks = rows(rig, "chunks")
    assert {r[1] for r in chunks if r[0].startswith("box:")} == {f"box:{i}#summary" for i in (first, second, third)}
    assert {(r[0], r[1]) for r in rows(rig, "embeddings")} == {(r[0], r[1]) for r in chunks}
    rig.statements.clear()
    assert await run(rig) == []
    assert not any(s.startswith(("INSERT INTO files", "INSERT INTO chunks", "INSERT INTO embeddings", "DELETE FROM files", "DELETE FROM chunks", "DELETE FROM embeddings")) for s in rig.statements)
    box.resolve(second, Resolution(kind="ticket", link="other"))
    rig.statements.clear()
    assert await run(rig) == []
    assert not any(s.startswith(("INSERT INTO files", "INSERT INTO chunks", "INSERT INTO embeddings", "DELETE FROM files", "DELETE FROM chunks", "DELETE FROM embeddings")) for s in rig.statements)
    (box.root / "duplicate.json").write_text(duplicate.model_copy(update={"summary": "Changed summary"}).model_dump_json())
    rig.statements.clear()
    assert await run(rig) == []
    writes = [s for s in rig.statements if s.startswith(("DELETE FROM files", "DELETE FROM chunks", "DELETE FROM embeddings"))]
    assert len(writes) == 3 and all(f"box:{first}" in s for s in writes)
    box.path(box.get(second)).unlink()
    assert await run(rig) == []
    for table in ("files", "chunks", "embeddings"):
        assert not any(r[0] == f"box:{second}" for r in rows(rig, table))
        assert any(r[0] == "docs/roadmap.md" for r in rows(rig, table))


@pytest.mark.asyncio
async def test_read_failures_preserve_rows(rig):
    put(rig, "docs/roadmap.md", ROADMAP)
    put(rig, "tickets/decisions/d1.md", record("d1", "Body"))
    box, first, _, _ = box_messages(rig)
    assert await run(rig) == []
    before = {table: rows(rig, table) for table in ("files", "chunks")}
    (box.root / "broken.json").write_text("{}")
    rig.fs.write(rig.root / "a.md", b"# Changed\n")
    findings = await run(rig)
    assert len(findings) == 1 and findings[0].startswith("box_unreadable: invalid box file")
    for table in before:
        assert [r for r in rows(rig, table) if r[0].startswith("box:")] == [r for r in before[table] if r[0].startswith("box:")]
    assert any(r[1] == "a.md#Changed" for r in rows(rig, "chunks"))
    before = {table: rows(rig, table) for table in before}
    rig.git.fail_ls = True
    findings = await run(rig)
    assert len(findings) == 1 and findings[0].startswith("git_failed:")
    assert all(rows(rig, table) == data for table, data in before.items())
