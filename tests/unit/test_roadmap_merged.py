# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: test roadmap merged
# relates: [clutch/__main__.py, clutch/git.py, clutch/journal.py, clutch/roadmap.py, clutch/runner.py, tests/fakes.py]
# owner: engine
# verified: 9a610809
# hash: 91073dd9b9ad911f22e8216546749529454bcf8e20c9ba1c8c25cd09032b3ea3
import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

import clutch.__main__ as cli
from clutch import roadmap
from clutch.git import GitError
from clutch.journal import EventType
from clutch.runner import Refusal
from tests.fakes import FakeJournal


def run(c, stems=(), **kwargs):
    return asyncio.run(roadmap.merged(c, stems, **kwargs))


class FakeGit:
    def __init__(self):
        self.calls = []
        self.log = "a-row\n\nb-row\n\nb-row\n\nc-row\n\n"
        self.missing = False

    async def rev_parse(self, repo, ref):
        self.calls.append((repo, ref))
        if self.missing:
            raise GitError(["git"], 1, "", "missing")
        return "sha"

    async def _run(self, repo, *args):
        self.calls.append((repo, *args))
        return self.log


@pytest.fixture
def checkout(tmp_path):
    return SimpleNamespace(repo=tmp_path, journal=FakeJournal(), git=FakeGit())


def table(c, *groups):
    path = c.repo / roadmap.ROADMAP
    path.parent.mkdir(parents=True, exist_ok=True)
    text = ""
    for heading, rows in groups:
        text += f"### {heading}\n| # | Stem | Owner | Kind | P | Depends on | Runs before | Content |\n|---|---|---|---|---|---|---|---|\n"
        for n, stem, priority, content, struck in rows:
            cells = [str(n), f"`{stem}`", "roadmap", "feature", priority, "", "", content]
            text += "| " + " | ".join(f"~~{x}~~" if struck else x for x in cells) + " |\n"
    path.write_text(text)


def state(c, stem, value):
    c.journal.append(EventType.STATE_TRANSITION, {"to": value}, ticket=stem)


def signal(c, stem, name, **body):
    c.journal.append(EventType.SIGNAL, {"signal": name, **body}, ticket=stem)


def test_release_name():
    assert [roadmap.release_name(x) for x in ("0.3.0", "0.3.0, last group: the roadmap driver", "0.4.0 (conditional)", "Next")] == ["0.3.0", "0.3.0", "0.4.0", "Next"]


def test_named_stems(checkout):
    c = checkout
    table(
        c,
        (
            "1.0.0",
            [
                (1, "a-row", "P1", "", False),
                (2, "b-row", "P1", "", False),
                (3, "c-row", "P1", "", False),
                (4, "d-row", "P1", "", False),
                (5, "s-row", "P1", "**Authored** (`tickets/s-row/`, `tickets/s-two/`).", False),
            ],
        ),
    )
    for stem, value in [("a-row", "merged"), ("b-row", "already_satisfied"), ("c-row", "gate_failed"), ("s-row", "merged"), ("s-two", "running")]:
        state(c, stem, value)
    assert run(c, ["a-row", "b-row"]) == (True, ["roadmap merged: ok"])
    assert run(c, ["a-row", "c-row", "d-row", "s-row"]) == (
        False,
        ["roadmap merged: row 3 c-row is gate_failed", "roadmap merged: row 4 d-row is not in the journal", "roadmap merged: row 5 s-row has a split ticket that has not settled"],
    )
    state(c, "s-two", "merged")
    assert run(c, ["s-row"]) == (True, ["roadmap merged: ok"])
    with pytest.raises(Refusal, match="s-two"):
        run(c, ["s-two"])


def test_release_rows(checkout):
    c = checkout
    table(
        c,
        ("1.0.0", [(1, "p-one", "P1", "", False), (2, "p-two", "P2", "", False), (3, "p-three", "P1", "", True)]),
        ("1.0.0, last group", [(4, "p-four", "P1", "", False)]),
        ("2.0.0", [(5, "p-five", "P0", "", False)]),
    )
    for stem, value in [("p-one", "merged"), ("p-four", "merged"), ("p-five", "running")]:
        state(c, stem, value)
    assert run(c, release="1.0.0", priorities=("P0", "P1")) == (True, ["roadmap merged: ok"])
    assert run(c, release="1.0.0") == (False, ["roadmap merged: release 1.0.0 row 2 p-two is not in the journal"])
    assert run(c, release="2.0.0") == (False, ["roadmap merged: release 2.0.0 row 5 p-five is running"])
    with pytest.raises(Refusal, match="9.9.9"):
        run(c, release="9.9.9")
    state(c, "p-four", "running")
    assert run(c, release="1.0.0", priorities=("P0", "P1")) == (False, ["roadmap merged: release 1.0.0 row 4 p-four is running"])


def test_release_split_row(checkout):
    c = checkout
    table(c, ("1.0.0", [(1, "s-row", "P1", "**Authored** (`tickets/s-row/`, `tickets/s-two/`).", False)]))
    state(c, "s-row", "merged")
    state(c, "s-two", "running")
    assert run(c, release="1.0.0") == (False, ["roadmap merged: release 1.0.0 row 1 s-row has a split ticket that has not settled"])
    state(c, "s-two", "merged")
    assert run(c, release="1.0.0") == (True, ["roadmap merged: ok"])


def test_count_since_tag(checkout):
    c = checkout
    for stem, source in [("a-row", "box:roadmap_row"), ("b-row", "box:roadmap_row"), ("c-row", "human")]:
        signal(c, stem, "ticket_intake", source=source)
    signal(c, "a-row", "draft_confirmed")
    assert run(c, since="v1.0.0", at_least=3)[0]
    assert c.git.calls[-1] == (c.repo, "log", "--first-parent", "--format=%(trailers:key=clutch-ticket,valueonly)", "refs/tags/v1.0.0..HEAD")
    assert run(c, since="v1.0.0", at_least=4) == (False, ["roadmap merged: 3 of 4 tickets merged since v1.0.0 match"])
    assert run(c, since="v1.0.0", at_least=2, source="box:roadmap_row")[0]
    assert run(c, since="v1.0.0", at_least=2, source="box:roadmap_row", unattended=True) == (False, ["roadmap merged: 1 of 2 tickets merged since v1.0.0 match"])
    signal(c, "c-row", "reject_verdict", actor="machine")
    assert run(c, since="v1.0.0", at_least=2, unattended=True)[0]
    signal(c, "b-row", "reject_verdict", actor="operator")
    assert not run(c, since="v1.0.0", at_least=2, unattended=True)[0]
    signal(c, "c-row", "ticket_intake", source="box:roadmap_row")
    assert run(c, since="v1.0.0", at_least=3, source="box:roadmap_row")[0]


def test_missing_tag_refuses(checkout):
    checkout.git.missing = True
    with pytest.raises(Refusal, match="v9.9.9.*clutch release bump --minor"):
        run(checkout, since="v9.9.9", at_least=1)
    assert len(checkout.git.calls) == 1


@pytest.mark.parametrize(
    "stems,kwargs",
    [
        ((), {}),
        ((), {"priorities": ("P1",)}),
        ((), {"since": "v1"}),
        ((), {"at_least": 1}),
        ((), {"source": "x"}),
        ((), {"unattended": True}),
        ((), {"since": "v1", "at_least": 0}),
        (("Bad Stem",), {}),
    ],
)
def test_argument_refusals(checkout, stems, kwargs):
    checkout.journal.read = lambda: pytest.fail("journal read")
    with pytest.raises(Refusal):
        run(checkout, stems, **kwargs)
    assert checkout.git.calls == []


def test_missing_roadmap(checkout):
    with pytest.raises(Refusal, match="docs/roadmap.md"):
        run(checkout, ["a-row"])


def test_main_roadmap_merged(monkeypatch, capsys):
    monkeypatch.setattr(cli, "load_config", lambda *a, **kw: SimpleNamespace(state_dir=Path("/state")))
    monkeypatch.setattr(cli, "child_env", lambda *a: {})
    monkeypatch.setattr(cli, "Lockfile", lambda *a, **kw: pytest.fail("lock taken"))
    results = [(True, ["roadmap merged: ok"]), (False, ["x"]), Refusal("blocked", "repair")]
    calls = []

    async def fake(checkout, stems, **kwargs):
        calls.append((stems, kwargs))
        result = results.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(roadmap, "merged", fake)
    args = ["roadmap", "merged", "a-row", "--since", "v1.0.0", "--at-least", "2", "--source", "box:roadmap_row", "--unattended"]
    for expected, out, err in [(0, "roadmap merged: ok\n", ""), (1, "x\n", ""), (2, "", "clutch roadmap: blocked -- repair\n")]:
        assert cli.main(args, cwd=Path("/repo"), env={}) == expected
        captured = capsys.readouterr()
        assert (captured.out, captured.err) == (out, err)
    assert calls[0] == (["a-row"], {"release": None, "priorities": (), "since": "v1.0.0", "at_least": 2, "source": "box:roadmap_row", "unattended": True, "parallel": False})
    with pytest.raises(SystemExit):
        cli._parser().parse_args(["roadmap", "merged", "--release", "1.0.0", "--priority", "P4"])
