# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test roadmap fresh write
# relates: [clutch/box.py, clutch/roadmap.py, tests/unit/test_roadmap_author.py]
# owner: engine
# verified: 9a610809
# hash: c4ca0a6ba2290d22be3c2e913dbfee9b7104d995b4e3ea892b6ecd5d752752d9
from clutch import roadmap
from clutch.box import Resolution
from tests.unit.test_roadmap_author import put, r, run, setup  # noqa: F401


def test_changed_stem_skips_author_link(setup):
    checkout, box = setup
    put(checkout, r(114, "old-stem", content="Original work."))
    path = checkout.repo / roadmap.ROADMAP

    async def author(ids):
        path.write_text(path.read_text().replace("`old-stem`", "`new-stem`"))
        box.resolve(ids[0], Resolution(kind="ticket", link="old-stem"))

    lines = run(checkout, 1, author)
    assert "`new-stem`" in path.read_text() and "old-stem" not in path.read_text()
    assert not checkout.git.commits
    assert "roadmap: row 114 old-stem changed on disk; skipped link" in lines


def test_changed_content_skips_author_link(setup):
    checkout, box = setup
    put(checkout, r(114, "old-stem", content="Original work."))
    path = checkout.repo / roadmap.ROADMAP
    edited = []

    async def author(ids):
        path.write_text(path.read_text().replace("Original work.", "Revised work."))
        edited.append(path.read_bytes())
        box.resolve(ids[0], Resolution(kind="ticket", link="old-stem"))

    lines = run(checkout, 1, author)
    assert path.read_bytes() == edited[0]
    assert not checkout.git.commits
    assert "roadmap: row 114 old-stem changed on disk; skipped link" in lines


def test_other_row_change_survives_author_link(setup):
    checkout, box = setup
    put(checkout, r(114, "old-stem", content="Original work."), r(115, "other-stem", content="Other work."))
    path = checkout.repo / roadmap.ROADMAP

    async def author(ids):
        path.write_text(path.read_text().replace("Other work.", "Revised other work."))
        box.resolve(ids[0], Resolution(kind="ticket", link="old-stem"))

    run(checkout, 1, author)
    first, second = roadmap.parse(path.read_text())
    assert first.content == "**Authored** (`tickets/old-stem/`). Original work."
    assert second.content == "Revised other work."
    assert [message for message, _, _ in checkout.git.commits] == ["clutch(roadmap): author old-stem"]
