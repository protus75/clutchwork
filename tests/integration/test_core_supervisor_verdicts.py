from pathlib import Path

import pytest

from clutch.hostfiles import BEGIN, CORE_TEMPLATE, END


@pytest.mark.parametrize("name", ["CLAUDE.md", "AGENTS.md", "hosts/fixture/CLAUDE.md"])
def test_managed_block_matches_template(name):
    data = (Path(__file__).resolve().parents[2] / name).read_bytes()
    assert data.split(BEGIN, 1)[1].split(END, 1)[0] == b"\n" + CORE_TEMPLATE
