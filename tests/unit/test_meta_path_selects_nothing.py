# clutch:meta
# schema: clutch.meta/1.0
# kind: test
# purpose: Unit tests showing that `clutch meta check`, `refresh` and `fill` refuse explicit paths that select no tracked file. They exit 2 with a remediation message for each such path, before any model call or write, while tracked valid paths still pass.
# relates: [clutch/__main__.py, clutch/meta.py, tests/unit/test_meta_refresh.py]
# owner: engine
# verified: c8bbefc9
# hash: b22539e32b99575e4e64835aa4951261ed1a7781631b4d6b2a04309578766440
import asyncio
from pathlib import Path

import pytest

from clutch import meta
from clutch.__main__ import _run_meta
from tests.unit.test_meta_refresh import MemoryFS, config


@pytest.mark.parametrize("verb", ["check", "refresh", "fill"])
@pytest.mark.parametrize("paths", [("docs/new.md",), ("src/x.py",), ("docs/a.md", "docs/new.md")])
def test_refuses_unselected_paths_before_work(verb, paths, capsys):
    fs = MemoryFS({"docs/a.md": "body\n", "docs/new.md": "new\n", "src/x.py": "x = 1\n"})
    original = fs.files.copy()

    async def ask(*args, **kwargs):
        pytest.fail("model called before refusal")

    result = asyncio.run(_run_meta(verb, config(), Path("/repo"), fs, ["docs/a.md"], "123456789", paths, ask))
    assert result == 2
    output = capsys.readouterr()
    missing = paths[-1]
    assert output.err == (
        f"clutch meta {verb}: {missing}: selects no tracked file -- for a new file, run git add -N {missing} then rerun; otherwise name a .md or .py path under a configured meta.paths root\n"
    )
    assert output.out == ""
    assert fs.files == original
    assert fs.writes == []


def test_all_unselected_paths_are_reported(capsys):
    fs = MemoryFS({"docs/a.md": "body\n"})
    result = asyncio.run(_run_meta("check", config(), Path("/repo"), fs, ["docs/a.md"], "123456789", ("docs/new.md", "src/x.py")))
    assert result == 2
    lines = capsys.readouterr().err.splitlines()
    assert len(lines) == 2
    assert "docs/new.md" in lines[0]
    assert "src/x.py" in lines[1]


def test_tracked_path_with_valid_block_passes(capsys):
    body = "body\n"
    fields = dict(schema="clutch.meta/1.0", kind="plan", purpose="useful", relates=[], owner="engine", verified="12345678", hash=meta.digest(body))
    block, _ = meta.compose(fields, body, 0, ".md")
    fs = MemoryFS({"docs/a.md": block})
    result = asyncio.run(_run_meta("check", config(), Path("/repo"), fs, ["docs/a.md"], "123456789", ("docs/a.md",)))
    assert result == 0
    assert capsys.readouterr().err == ""
