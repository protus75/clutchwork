# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test roadmap release boundary
# relates: [clutch/roadmap.py, tests/unit/test_roadmap_author.py, tests/unit/test_roadmap_status.py]
# owner: engine
# verified: 62a64dee
# hash: e37b23b4a57adad8364551c72f4ffef894644915694c03bd68bbd39c3a4f157b
import asyncio

from clutch import roadmap
from tests.unit.test_roadmap_author import put, r, run, setup
from tests.unit.test_roadmap_status import HEADER, fixture, row


def test_choose_orders_by_release():
    rows = roadmap.parse(
        "### 1.0.0\n"
        + HEADER
        + row(1, "old-wait", "after its agent capture")
        + row(2, "old-ready")
        + "### 2.0.0\n"
        + HEADER
        + row(3, "cur-ready")
        + row(4, "cur-open", "`tickets/cur-open/`")
        + "### 3.0.0\n"
        + HEADER
        + row(5, "new-ready", priority="P0")
    )
    for states, current, expected in [
        ({"cur-open": "running"}, None, "old-ready"),
        ({"cur-open": "running"}, "9.9.9", "old-ready"),
        ({"cur-open": "running"}, "2.0.0", "cur-ready"),
        ({"cur-open": "merged", "cur-ready": "merged"}, "2.0.0", "old-ready"),
        ({"cur-open": "merged", "cur-ready": "merged"}, "3.0.0", "new-ready"),
    ]:
        choice = roadmap.choose(rows, states=states, files=set(), current=current)
        assert tuple(r.stem for r in choice.ready) == (expected,)
        assert tuple(w.row.stem for w in choice.waits) == ("old-wait",)


def test_current_release(tmp_path):
    path = tmp_path / "pyproject.toml"
    assert roadmap.current_release(tmp_path) is None
    for text, expected in [
        ("invalid [", None),
        ("[project]\n", None),
        ('[project]\nversion="dev"', None),
        ('[project]\nversion="0.3.0"', "0.4.0"),
        ('[project]\nversion="0.3.1"', "0.4.0"),
        ('[project]\nversion="0.6.1"', "0.7.0"),
        ('[project]\nversion="2.10.4"', "2.11.0"),
    ]:
        path.write_text(text)
        assert roadmap.current_release(tmp_path) == expected


def test_callers_pass_the_current_release(tmp_path, setup, monkeypatch):
    checkout, *_ = fixture(tmp_path)
    assert "next: q-eleven, r-six" in asyncio.run(roadmap.status(checkout))
    path = tmp_path / roadmap.ROADMAP
    path.write_text(path.read_text().replace("### 2.0.0", "### 2.1.0"))
    (tmp_path / "pyproject.toml").write_text('[project]\nversion="2.0.0"')
    assert "next: n-nine" in asyncio.run(roadmap.status(checkout))
    checkout, _ = setup
    (checkout.repo / "pyproject.toml").write_text('[project]\nversion="1.0.0"')
    put(checkout, r(1, "a-row"))
    original = roadmap.choose
    calls = []

    def choose(*args, **kwargs):
        calls.append(kwargs["current"])
        return original(*args, **kwargs)

    monkeypatch.setattr(roadmap, "choose", choose)

    async def author(ids):
        pass

    run(checkout, 1, author)
    assert calls == ["1.1.0"]
